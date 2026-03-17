#!/usr/bin/env python3
"""
Cerebro - Windows Microphone Sender
===================================
Captura microfone no Windows, transcreve com Whisper local e envia para o backend.

Toda configuração é feita no arquivo .env na raiz do projeto.
Não altere este arquivo — edite apenas o .env.

Instalação (PowerShell ou cmd, com Python 3.11/3.12):
    pip install sounddevice numpy requests silero-vad python-dotenv
    pip install torch --extra-index-url https://download.pytorch.org/whl/cpu
    pip install openai-whisper

Uso (rodar da pasta raiz do projeto):
    python clients\\windows_mic_sender.py
    python clients\\windows_mic_sender.py --list-devices
"""

import argparse
import os
import sys
import time
import threading
import requests
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from queue import Queue

# ─── Carregar .env da raiz do projeto ────────────────────────────────────────

# O script pode ser chamado de qualquer pasta — encontrar a raiz do projeto
_script_dir = Path(__file__).resolve().parent        # clients/
_project_root = _script_dir.parent                   # nuvbox/
_env_file = _project_root / ".env"

try:
    from dotenv import load_dotenv
    if _env_file.exists():
        load_dotenv(_env_file)
        print(f"✅ Configurações carregadas de {_env_file}")
    else:
        print(f"⚠️  Arquivo .env não encontrado em {_env_file}")
        print("   Usando valores padrão. Copie .env.example para .env e ajuste.")
except ImportError:
    print("⚠️  python-dotenv não instalado. Rode: pip install python-dotenv")
    print("   Usando variáveis de ambiente do sistema.")

# ─── Verificar dependências ───────────────────────────────────────────────────

def _check_import(package, install_cmd):
    try:
        return __import__(package)
    except ImportError:
        print(f"❌ '{package}' não instalado. Rode: {install_cmd}")
        sys.exit(1)

sd = _check_import("sounddevice", "pip install sounddevice")
_check_import("torch", "pip install torch --extra-index-url https://download.pytorch.org/whl/cpu")
_check_import("whisper", "pip install openai-whisper")

import torch
from silero_vad import load_silero_vad
import whisper


# ─── Ler configurações do .env ───────────────────────────────────────────────

def _get(key, default, cast=str):
    """Lê variável de ambiente com fallback para default."""
    val = os.environ.get(key, "")
    return cast(val) if val else default

CFG = {
    # Backend
    "backend_url":      _get("BACKEND_URL", "http://localhost:5001"),
    "secret":           _get("ALEXA_WEBHOOK_SECRET", "mude_antes_do_ngrok"),
    "source_id":        _get("CLIENT_SOURCE_ID", "windows_mic"),
    # Microfone
    "device":           _get("MIC_DEVICE_ID", None, lambda v: int(v) if v and v.strip() else None),
    "sample_rate":      _get("MIC_SAMPLE_RATE", 16000, int),
    "chunk_size":       _get("MIC_CHUNK_SIZE", 512, int),
    # Whisper
    "whisper_model":    _get("WHISPER_MODEL", "small"),
    "language":         _get("WHISPER_LANGUAGE", "pt"),
    # VAD
    "silence_ms":       _get("VAD_SILENCE_DURATION_MS", 600, int),
    "min_speech_ms":    _get("VAD_MIN_SPEECH_DURATION_MS", 300, int),
}


# ─── Transcritor ─────────────────────────────────────────────────────────────

class Transcriber:
    def __init__(self):
        model_name = CFG["whisper_model"]
        print(f"🔄 Carregando Whisper '{model_name}'...")
        self.model = whisper.load_model(model_name)
        self.language = CFG["language"]
        print(f"✅ Whisper '{model_name}' carregado")

    def transcribe(self, audio_bytes: bytes) -> str | None:
        audio_np = np.frombuffer(audio_bytes, dtype=np.float32).copy()
        result = self.model.transcribe(audio_np, language=self.language, fp16=False)
        text = result.get("text", "").strip()
        return text if text else None


# ─── Enviador para Backend ───────────────────────────────────────────────────

class BackendSender:
    def __init__(self):
        self.url = CFG["backend_url"].rstrip("/") + "/webhook/text"
        self.secret = CFG["secret"]
        self.source_id = CFG["source_id"]

    def send(self, text: str, duration_ms: int) -> bool:
        payload = {
            "text": text,
            "source": self.source_id,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "metadata": {
                "whisper_model": CFG["whisper_model"],
                "language": CFG["language"],
                "duration_ms": duration_ms,
                "platform": "windows",
            },
        }
        headers = {
            "Content-Type": "application/json",
            "X-Cerebro-Secret": self.secret,
        }
        try:
            resp = requests.post(self.url, json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                print(f"  ✅ Enviado para backend: \"{text[:80]}\"")
                return True
            else:
                print(f"  ❌ Backend retornou {resp.status_code}: {resp.text}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"  ❌ Sem conexão com {self.url}")
            print(f"     Verifique BACKEND_URL no .env e se o backend está rodando.")
            return False
        except Exception as e:
            print(f"  ❌ Erro ao enviar: {e}")
            return False


# ─── Captura de Microfone com VAD ────────────────────────────────────────────

class MicCapture:
    def __init__(self, audio_queue: Queue):
        self.audio_queue = audio_queue

        print("🔄 Carregando Silero VAD...")
        self.vad = load_silero_vad()
        print("✅ VAD carregado")

        self._buffer = np.array([], dtype=np.float32)
        self._in_speech = False
        self._silence_frames = 0
        self._speech_frames = 0

        fps = CFG["sample_rate"] / CFG["chunk_size"]
        self.silence_thresh = int((CFG["silence_ms"] / 1000.0) * fps)
        self.min_speech_thresh = int((CFG["min_speech_ms"] / 1000.0) * fps)

    def _callback(self, indata, frames, time_info, status):
        if status:
            # input overflow é comum e não crítico — suprimir
            if "overflow" not in str(status).lower():
                print(f"⚠️  Audio: {status}")

        chunk = indata[:, 0].astype(np.float32)

        with torch.no_grad():
            prob = self.vad(torch.from_numpy(chunk), CFG["sample_rate"])
            is_speech = float(prob) > 0.5

        if is_speech:
            self._silence_frames = 0
            if not self._in_speech:
                self._in_speech = True
                self._speech_frames = 0
                self._buffer = np.array([], dtype=np.float32)
            self._speech_frames += 1
        else:
            if self._in_speech:
                self._silence_frames += 1
                if self._silence_frames >= self.silence_thresh:
                    if self._speech_frames >= self.min_speech_thresh and self._buffer.size > 0:
                        duration_ms = int(len(self._buffer) / CFG["sample_rate"] * 1000)
                        self.audio_queue.put_nowait((self._buffer.tobytes(), duration_ms))
                        print(f"🎤 Fala detectada ({duration_ms}ms) — transcrevendo...")
                    self._buffer = np.array([], dtype=np.float32)
                    self._in_speech = False
                    self._silence_frames = 0
                    self._speech_frames = 0

        if self._in_speech and self._speech_frames >= self.min_speech_thresh:
            self._buffer = np.concatenate([self._buffer, chunk])

    def start(self):
        self._stream = sd.InputStream(
            device=CFG["device"],
            samplerate=CFG["sample_rate"],
            channels=1,
            blocksize=CFG["chunk_size"],
            dtype=np.float32,
            callback=self._callback,
            latency="low",
        )
        self._stream.start()

    def stop(self):
        if hasattr(self, "_stream"):
            self._stream.stop()
            self._stream.close()


# ─── Worker de Processamento ─────────────────────────────────────────────────

def processing_worker(audio_queue: Queue, transcriber: Transcriber, sender: BackendSender, stop_event: threading.Event):
    while not stop_event.is_set():
        try:
            audio_bytes, duration_ms = audio_queue.get(timeout=1.0)
            text = transcriber.transcribe(audio_bytes)
            if text:
                sender.send(text, duration_ms)
            else:
                print("  ⚠️  Nada transcrito")
        except Exception:
            continue


# ─── Main ─────────────────────────────────────────────────────────────────────

def list_devices():
    print("🎤 Dispositivos de áudio disponíveis:")
    print(sd.query_devices())
    print()
    print("Use o número da linha em MIC_DEVICE_ID no .env para escolher um dispositivo específico.")


def main():
    parser = argparse.ArgumentParser(description="Cerebro Windows Mic Sender — lê configurações do .env")
    parser.add_argument("--list-devices", action="store_true", help="Listar dispositivos de áudio e sair")
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        return

    print("=" * 60)
    print("🎙️  CEREBRO — Windows Mic Sender")
    print("=" * 60)
    print(f"  Backend:   {CFG['backend_url']}")
    print(f"  Source ID: {CFG['source_id']}")
    print(f"  Whisper:   {CFG['whisper_model']}")
    print(f"  Idioma:    {CFG['language']}")
    print(f"  Device:    {CFG['device'] or 'padrão do sistema'}")
    print(f"  Config:    {_env_file}")
    print("=" * 60)
    print()

    audio_queue = Queue(maxsize=20)
    stop_event = threading.Event()

    transcriber = Transcriber()
    sender = BackendSender()
    capture = MicCapture(audio_queue)

    worker = threading.Thread(
        target=processing_worker,
        args=(audio_queue, transcriber, sender, stop_event),
        daemon=True,
    )
    worker.start()

    try:
        capture.start()
        print("✅ Escutando... (Ctrl+C para parar)")
        print()
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n⏹️  Parando...")
    finally:
        capture.stop()
        stop_event.set()
        worker.join(timeout=5)
        print("✅ Encerrado.")


if __name__ == "__main__":
    main()

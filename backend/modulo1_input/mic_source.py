import threading
import numpy as np
from queue import Queue
from datetime import datetime
from modulo1_input.base_source import AudioSource, AudioChunk
from config import settings
from utils import is_shutdown_requested, setup_logger

logger = setup_logger(__name__)

try:
    import sounddevice as sd
except ImportError:
    logger.error("sounddevice not installed. Install with: pip install sounddevice")
    sd = None

try:
    import torch
    from silero_vad import load_silero_vad
except ImportError:
    logger.error("silero-vad not installed. Install with: pip install silero-vad torch")
    torch = None


class MicrophoneSource(AudioSource):
    """
    Captures audio from USB microphone with Silero VAD detection.

    Pipeline:
    1. sounddevice captures chunks (512 samples @ 16kHz)
    2. Accumulate chunks in VAD detector
    3. When speech ends, emit AudioChunk to output queue
    """

    def __init__(self, audio_queue: Queue):
        """
        Args:
            audio_queue: Queue to push AudioChunk objects when speech detected
        """
        if not sd:
            raise RuntimeError("sounddevice not available")
        if not torch:
            raise RuntimeError("silero-vad dependencies not available")

        self.audio_queue = audio_queue
        self._stream = None
        self._running = False
        self._lock = threading.Lock()

        # VAD state
        self.vad_model = None
        self._vad_buffer = np.array([], dtype=np.float32)
        self._silence_frames = 0
        self._speech_frames = 0
        self._in_speech = False

        # Config
        self.sample_rate = settings.mic.sample_rate  # 16000
        self.chunk_size = settings.mic.chunk_size  # 512 samples
        self.device_id = settings.mic.device_id

        # VAD thresholds (converted to frames)
        self.silence_threshold_frames = int(
            (settings.vad.silence_duration_ms / 1000.0) * self.sample_rate / self.chunk_size
        )
        self.min_speech_threshold_frames = int(
            (settings.vad.min_speech_duration_ms / 1000.0) * self.sample_rate / self.chunk_size
        )

        logger.info(
            f"MicrophoneSource initialized: device={self.device_id}, "
            f"sample_rate={self.sample_rate}, chunk_size={self.chunk_size}"
        )

    def start(self):
        """Start capturing audio from microphone."""
        with self._lock:
            if self._running:
                logger.warning("Microphone already running")
                return

            try:
                self._load_vad_model()
                self._stream = sd.InputStream(
                    device=self.device_id,
                    samplerate=self.sample_rate,
                    channels=1,
                    blocksize=self.chunk_size,
                    dtype=np.float32,
                    callback=self._audio_callback,
                    latency="low",
                )
                self._stream.start()
                self._running = True
                logger.info("✅ Microphone source started")
            except Exception as e:
                logger.error(f"❌ Failed to start microphone: {e}")
                raise

    def stop(self):
        """Stop capturing and flush any remaining buffered audio."""
        with self._lock:
            if not self._running:
                return

            try:
                if self._stream:
                    self._stream.stop()
                    self._stream.close()
                self._running = False
                logger.info("✅ Microphone source stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping microphone: {e}")

    def is_running(self) -> bool:
        """Check if microphone is actively capturing."""
        with self._lock:
            return self._running

    def _load_vad_model(self):
        """Load Silero VAD model (run once at startup)."""
        try:
            logger.info("Loading Silero VAD model...")
            self.vad_model = load_silero_vad()
            logger.info("✅ VAD model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load VAD model: {e}")
            raise

    def _audio_callback(self, indata, frames, time_info, status):
        """
        Callback invoked by sounddevice for each audio chunk.

        Args:
            indata: Audio data chunk (shape: (blocksize, channels))
            frames: Number of frames in indata
            time_info: Time info from stream
            status: Status info from stream
        """
        if status:
            logger.warning(f"Audio callback status: {status}")

        # Convert to mono float32
        audio_chunk = indata[:, 0].astype(np.float32)

        # VAD inference on this chunk
        with torch.no_grad():
            vad_prob = self.vad_model(torch.from_numpy(audio_chunk), self.sample_rate)
            speech_detected = vad_prob > 0.5

        # Update VAD state machine
        if speech_detected:
            self._silence_frames = 0
            if not self._in_speech:
                self._speech_frames = 0
                self._in_speech = True
                logger.debug("🎤 Speech detected (start)")
            self._speech_frames += 1
        else:
            self._speech_frames = 0
            if self._in_speech:
                self._silence_frames += 1
                if self._silence_frames >= self.silence_threshold_frames:
                    # Speech ended, emit audio chunk
                    if self._vad_buffer.size > 0:
                        self._emit_audio_chunk()
                    self._in_speech = False
                    self._silence_frames = 0
                    logger.debug("🎤 Speech ended")

        # Accumulate audio
        if self._in_speech and self._speech_frames >= self.min_speech_threshold_frames:
            self._vad_buffer = np.concatenate([self._vad_buffer, audio_chunk])

    def _emit_audio_chunk(self):
        """Emit buffered audio as AudioChunk to queue."""
        if self._vad_buffer.size == 0:
            return

        try:
            # Convert float32 to bytes
            audio_bytes = self._vad_buffer.tobytes()
            duration_ms = int((len(self._vad_buffer) / self.sample_rate) * 1000)

            chunk = AudioChunk(
                audio_bytes=audio_bytes,
                source_id="mic_usb",
                captured_at=datetime.now(),
                sample_rate=self.sample_rate,
            )

            # Non-blocking put (discard if queue full to prevent blocking audio callback)
            try:
                self.audio_queue.put_nowait(chunk)
                logger.debug(f"📦 Emitted audio chunk: {duration_ms}ms, {len(audio_bytes)} bytes")
            except:  # Queue.Full
                logger.warning("❌ Audio queue full, dropping chunk")

            self._vad_buffer = np.array([], dtype=np.float32)

        except Exception as e:
            logger.error(f"❌ Error emitting audio chunk: {e}")

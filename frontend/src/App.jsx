import { useState } from "react";

// Items already completed — pre-checked on load
const initialChecked = {
  // Ambiente & Setup
  a1: true, a2: true, a3: true, a4: true, a5: true,
  b1: true, b2: true, b3: true,
  c1: true, c2: true, c3: true, c5: true, c6: true, c8: true,
  d1: true, d2: true, d3: true, d4: true, d5: true,
  f1: true, f3: true,
  // Módulo 1 — captura + VAD
  m1a1: true, m1a2: true, m1a3: true,
  m1b1: true, m1b2: true, m1b3: true, m1b4: true,
  // Módulo 1 — webhook + windows sender
  wh1: true, wh2: true, wh3: true, wh4: true,
  ws1: true, ws2: true, ws3: true, ws4: true, ws5: true, ws6: true,
  // Módulo 2
  m2a1: true, m2a2: true, m2a3: true, m2a4: true,
  m2b1: true, m2b2: true,
  // Módulo 3
  m3a1: true, m3a3: true, m3a4: true,
  m3b1: true, m3b2: true, m3b3: true,
  // Sistema
  s1: true, s3: true, s4: true, s8: true, s9: true,
};

const data = {
  sections: [
    {
      id: "ambiente",
      label: "AMBIENTE & SETUP",
      color: "#00FFB2",
      icon: "⚙️",
      groups: [
        {
          title: "Sistema Operacional & Python",
          items: [
            { id: "a1", text: "Python 3.11+ configurado (via Docker)", note: "Resolvido com multi-stage Docker build usando python:3.11-slim. Sem necessidade de instalar Python no host." },
            { id: "a2", text: "Docker e Docker Compose instalados e funcionando", note: "docker --version + docker-compose --version. Versão Docker >= 20. Compose v2 (docker compose) ou v1 (docker-compose)." },
            { id: "a3", text: "Ambiente isolado: Docker container como venv do projeto", note: "O Dockerfile gerencia todas as dependências Python. O bind mount ./backend:/app permite editar código sem rebuild." },
            { id: "a4", text: "Variáveis de ambiente centralizadas no .env", note: "cp .env.example .env — todas as configurações (banco, mic, whisper, VAD, webhooks) em um único arquivo." },
            { id: "a5", text: "pip e setuptools atualizados no Docker build", note: "Resolvido no Dockerfile: pip install --upgrade pip setuptools wheel antes dos requirements. Necessário para pacotes sem wheel pré-compilado." },
          ]
        },
        {
          title: "Dependências de Sistema",
          items: [
            { id: "b1", text: "ffmpeg instalado no container Docker", note: "Whisper depende do ffmpeg para processar áudio. Instalado no Dockerfile: apt-get install -y ffmpeg" },
            { id: "b2", text: "PortAudio instalado no container (portaudio19-dev)", note: "Ubuntu 22.04: portaudio19-dev (não libportaudio-dev). Instalado no Dockerfile. Necessário para sounddevice." },
            { id: "b3", text: "Microfone capturado fora do Docker via windows_mic_sender.py", note: "Docker no WSL2 não tem acesso ao hardware de áudio do Windows. Solução: script Python nativo no Windows (clients/windows_mic_sender.py) captura e envia via HTTP para o backend." },
          ]
        },
        {
          title: "Pacotes Python",
          items: [
            { id: "c1", text: "openai-whisper instalado", note: "Incluído em backend/requirements.txt. Modelo small (~460MB) baixado automaticamente no primeiro uso." },
            { id: "c2", text: "silero-vad instalado", note: "Incluído em backend/requirements.txt. Integrado no mic_source.py para detecção de início/fim de fala." },
            { id: "c3", text: "PyTorch CPU instalado (sem CUDA)", note: "Instalado com --extra-index-url https://download.pytorch.org/whl/cpu. Necessário usar --extra-index-url (não --index-url) para não bloquear outros pacotes como sounddevice." },
            { id: "c4", text: "sounddevice instalado (substituiu PyAudio)", note: "Usamos sounddevice ao invés de PyAudio — menos problemas de compilação no WSL2 e Windows. pip install sounddevice" },
            { id: "c5", text: "psycopg2-binary instalado", note: "Conector Python para PostgreSQL. A versão binary não exige compilação local. Incluído em requirements.txt." },
            { id: "c6", text: "python-dotenv instalado", note: "Usado no backend (config.py) e no windows_mic_sender.py para ler .env automaticamente." },
            { id: "c7", text: "openai (cliente Python) — para Módulo 4", note: "Necessário para GPT-4o mini no processamento batch. NÃO instalado ainda — aguarda Módulo 4." },
            { id: "c8", text: "requirements.txt gerado e versionado", note: "backend/requirements.txt contém todas as dependências com versões pinadas. Usado pelo Dockerfile para build reproduzível." },
          ]
        },
        {
          title: "PostgreSQL",
          items: [
            { id: "d1", text: "PostgreSQL 15 rodando via Docker", note: "Imagem postgres:15-alpine no docker-compose.yml. Sem instalação local necessária." },
            { id: "d2", text: "Dados persistidos em ./data/postgres/ (bind mount)", note: "Volume bind mount em vez de volume nomeado Docker. Facilita backup manual e migração para VPS: basta copiar a pasta data/." },
            { id: "d3", text: "Banco criado automaticamente via POSTGRES_DB", note: "docker-compose.yml define POSTGRES_DB=${DB_NAME:-cerebro_db}. O container cria o banco na primeira inicialização." },
            { id: "d4", text: "Usuário dedicado criado via POSTGRES_USER", note: "docker-compose.yml define POSTGRES_USER=${DB_USER:-cerebro}. Credenciais configuradas no .env." },
            { id: "d5", text: "Schema aplicado automaticamente no boot", note: "entrypoint.sh aplica backend/modulo3_armazenamento/schema.sql via psql a cada inicialização (usa CREATE TABLE IF NOT EXISTS — idempotente)." },
          ]
        },
        {
          title: "API OpenAI",
          items: [
            { id: "e1", text: "Criar conta na OpenAI", note: "platform.openai.com — necessário para Módulo 4 (batch processing com GPT-4o mini)." },
            { id: "e2", text: "Adicionar créditos (mínimo $5)", note: "GPT-4o mini é barato. $5 dura semanas em uso moderado. Necessário para Módulo 4." },
            { id: "e3", text: "Gerar API key e adicionar ao .env", note: "OPENAI_API_KEY=sk-... no .env. NUNCA commitar essa chave no git. O .env já está no .gitignore." },
            { id: "e4", text: ".env no .gitignore", note: "Verificar: cat .gitignore | grep .env. O arquivo .env.example (sem segredos) é commitado; o .env real não." },
            { id: "e5", text: "Testar chamada simples à API", note: "Uma chamada de teste com 'Olá' para confirmar key funcionando. Aguarda Módulo 4." },
          ]
        },
        {
          title: "Estrutura de Pastas",
          items: [
            { id: "f1", text: "Estrutura de diretórios criada", note: "backend/ (modulo1_input, modulo2_transcricao, modulo3_armazenamento, utils) | clients/ | docs/ | data/ | frontend/ | logs/" },
            { id: "f2", text: "Repositório git inicializado", note: "git init + .gitignore com: .env, __pycache__, data/postgres/, venv/, logs/*.log" },
            { id: "f3", text: "Configuração central em config.py", note: "backend/config.py lê todas as variáveis do .env via python-dotenv e expõe objeto Settings com sub-objetos (db, mic, whisper, vad, flask)." },
          ]
        }
      ]
    },
    {
      id: "modulo1",
      label: "MÓDULO 1 — INPUT (FONTES MODULARES)",
      color: "#FF6B35",
      icon: "🎙️",
      groups: [
        {
          title: "Captura de Áudio (Linux/Docker)",
          items: [
            { id: "m1a1", text: "Listar dispositivos de áudio disponíveis", note: "make test ou: docker-compose run --rm backend python -c \"import sounddevice as sd; print(sd.query_devices())\"" },
            { id: "m1a2", text: "Captura contínua em chunks com sounddevice", note: "Implementado em backend/modulo1_input/mic_source.py usando sd.InputStream. Chunk de 512 amostras a 16kHz." },
            { id: "m1a3", text: "Taxa de amostragem em 16kHz (Whisper)", note: "Configurável via MIC_SAMPLE_RATE no .env (padrão 16000). Whisper espera 16kHz — não mudar sem resample." },
            { id: "m1a4", text: "Teste de captura: salvar .wav e ouvir", note: "Pendente: testar gravando 10s de áudio em arquivo para confirmar qualidade do hardware antes de conectar ao Whisper." },
          ]
        },
        {
          title: "VAD — Detecção de Voz (Silero)",
          items: [
            { id: "m1b1", text: "Modelo silero-vad carregado e funcionando", note: "Carregado em mic_source.py. Na primeira execução faz download do modelo (~2MB). Cache em ~/.cache/torch." },
            { id: "m1b2", text: "Detecção de início de fala implementada", note: "Quando VAD detecta voz: acumula chunks em buffer. Configurado via VAD_MIN_SPEECH_DURATION_MS no .env." },
            { id: "m1b3", text: "Detecção de fim de fala implementada", note: "Após VAD_SILENCE_DURATION_MS ms de silêncio, utterance é considerada completa e enviada para transcrição. Padrão aumentado para 1500ms para acomodar pausas de pensamento." },
            { id: "m1b4", text: "VAD calibrado para pausas longas", note: "VAD_SILENCE_DURATION_MS=1500 resolve frases cortadas no meio. Documentação de calibração em docs/03-Referencia/VAD-Calibracao.md." },
            { id: "m1b5", text: "Modo sleep por inatividade (futuro)", note: "Após N min sem voz, pausar captura e reduzir CPU. Reativar automaticamente quando voz detectada." },
            { id: "m1b6", text: "Wake automático por detecção de voz (futuro)", note: "Thread leve mantém escuta mesmo no sleep para reativar o pipeline completo quando voz aparecer." },
          ]
        },
        {
          title: "Webhook Genérico (/webhook/text)",
          items: [
            { id: "wh1", text: "Endpoint POST /webhook/text criado no Flask", note: "Implementado em backend/modulo1_input/text_webhook.py. Aceita qualquer fonte via campo 'source'. Registrado via register_text_webhook(app, text_queue)." },
            { id: "wh2", text: "Validação de campos obrigatórios (text, source, timestamp)", note: "Retorna 400 se campos faltando. Aceita fontes: windows_mic, alexa, esp32, arquivo, manual, e qualquer string nova." },
            { id: "wh3", text: "Texto injetado direto na text_queue (bypassa Whisper)", note: "Fontes externas já transcreveram o áudio localmente — não faz sentido reprocessar. Vai direto para StorageWorker." },
            { id: "wh4", text: "Testado via make webhook-test e curl", note: "make webhook-test envia POST de teste. Verificar com make db-recent se o registro aparece no banco." },
          ]
        },
        {
          title: "Cliente Windows — Script (windows_mic_sender.py)",
          items: [
            { id: "ws1", text: "Script clients/windows_mic_sender.py criado", note: "Script Python nativo Windows (fora do WSL2). Captura mic, transcreve com Whisper local, envia texto para o backend via HTTP." },
            { id: "ws2", text: "100% configurável via .env — sem hardcode", note: "Usa python-dotenv para ler BACKEND_URL, CLIENT_SOURCE_ID, MIC_DEVICE_ID, WHISPER_MODEL, VAD_SILENCE_DURATION_MS, etc. do .env. Não é necessário editar o código." },
            { id: "ws3", text: "Silero VAD integrado localmente no script", note: "Mesmo modelo e lógica do backend. VAD_SILENCE_DURATION_MS controlado pelo .env. Resolvido: .copy() no array numpy para evitar warning do PyTorch." },
            { id: "ws4", text: "Whisper integrado localmente no script", note: "Transcrição acontece no Windows, não no backend. Reduz carga no servidor e mantém latência baixa mesmo com backend remoto." },
            { id: "ws5", text: "Texto enviado via POST /webhook/text", note: "Payload: {text, source: CLIENT_SOURCE_ID, timestamp}. Backend recebe e armazena sem reprocessar." },
            { id: "ws6", text: "Pipeline end-to-end testado e funcionando", note: "Falar → windows_mic_sender captura → VAD detecta fim → Whisper transcreve → POST para backend → salvo no banco. Verificado via make db-debug." },
          ]
        },
        {
          title: "Contexto de Ativação",
          items: [
            { id: "m1c1", text: "Janela de horário configurável (ex: 8h-22h)", note: "Ler do config: hora_inicio, hora_fim. Não gravar fora desse horário. Implementar com datetime simples." },
            { id: "m1c2", text: "Log de ativação, desativação e estatísticas", note: "Parcialmente feito via logging INFO. Melhorar: registrar quantos fragmentos capturados, tempo de atividade, erros de envio." },
          ]
        }
      ]
    },
    {
      id: "cliente_windows_app",
      label: "CLIENTE WINDOWS — APP DESKTOP",
      color: "#38BDF8",
      icon: "🖥️",
      groups: [
        {
          title: "Análise & Decisão de Stack",
          items: [
            { id: "app1", text: "Definir stack tecnológica do app", note: "Opções: Python+PyQt6 (mesmo stack, mais simples), Electron+Node.js (UI web, tray fácil), Tauri+Rust (bundle leve, UI web), C# WPF (nativo Windows). Considerar: bundle size, UX, manutenção a longo prazo." },
            { id: "app2", text: "Decidir arquitetura de transcrição: local vs remota", note: "Local (Whisper no app): privacidade, funciona offline, mais pesado para baixar. Remota (backend transcreve): app leve, depende de rede. Recomendação MVP: local, igual ao windows_mic_sender.py atual." },
            { id: "app3", text: "Definir features do MVP do app", note: "MVP mínimo: tray icon (ativo/pausado), captura + VAD + Whisper + envio. Janela de configurações básica. Tudo configurável sem editar código." },
            { id: "app4", text: "Definir formato de distribuição", note: "Opções: instalador .exe (NSIS/Inno Setup), portable .exe, winget/chocolatey. Para uso pessoal: portable .exe é suficiente no início." },
          ]
        },
        {
          title: "Setup do Projeto App",
          items: [
            { id: "app5", text: "Criar estrutura de pastas do projeto do app", note: "Dentro do repo atual (clients/windows_app/) ou repo separado. Separado facilita build pipeline independente." },
            { id: "app6", text: "Configurar ambiente de desenvolvimento da stack escolhida", note: "Ex se PyQt6: python -m venv app-env + pip install PyQt6 sounddevice silero-vad openai-whisper. Se Electron: npm init + electron + node-addon-api." },
            { id: "app7", text: "Configurar pipeline de build/empacotamento", note: "PyInstaller (Python), electron-builder (Electron), Tauri CLI. Configurar para gerar .exe standalone sem dependências externas." },
          ]
        },
        {
          title: "Core — Captura & VAD",
          items: [
            { id: "app8", text: "Captura de microfone funcionando no app (16kHz, float32)", note: "Reusar lógica do windows_mic_sender.py. Garantir seleção de dispositivo de entrada configurável." },
            { id: "app9", text: "Silero VAD integrado no app", note: "Mesmo modelo do script atual. Parâmetros (silence_ms, min_speech_ms) lidos da config do app." },
            { id: "app10", text: "Buffer de áudio thread-safe entre captura e VAD", note: "Queue ou buffer circular. Captura roda numa thread, VAD em outra — evitar perda de chunks durante processamento." },
            { id: "app11", text: "Configuração de VAD acessível na UI (não só no .env)", note: "Slider ou campo numérico para VAD_SILENCE_DURATION_MS na janela de configurações do app." },
          ]
        },
        {
          title: "Transcrição Local",
          items: [
            { id: "app12", text: "Whisper integrado no app Windows", note: "openai-whisper ou whisper.cpp (via binding Python). whisper.cpp é muito mais rápido em CPU — considerar para melhor UX no app." },
            { id: "app13", text: "Modelo e idioma configuráveis via UI", note: "Dropdown para selecionar tiny/base/small/medium. Campo de idioma (pt, en, auto). Mudança salva na config." },
            { id: "app14", text: "Medir e exibir latência de transcrição", note: "Mostrar tempo de processamento na UI. Útil para o usuário entender delay e escolher modelo adequado para seu hardware." },
          ]
        },
        {
          title: "Integração com Backend",
          items: [
            { id: "app15", text: "Cliente HTTP para POST /webhook/text", note: "Mesmo payload do windows_mic_sender.py: {text, source, timestamp}. O endpoint do backend não muda." },
            { id: "app16", text: "BACKEND_URL e CLIENT_SOURCE_ID configuráveis na UI", note: "Campo de texto para URL (localhost, IP local, domínio VPS). Campo para nome desta máquina no banco." },
            { id: "app17", text: "Health check e indicador de conexão em tempo real", note: "GET /health (ou timeout no POST). Ícone verde/vermelho na UI mostrando se backend está acessível." },
            { id: "app18", text: "Fila local com retry quando backend offline", note: "Se POST falha, guardar em fila em memória (ou SQLite local). Tentar reenviar quando conexão voltar. Não perder transcrições." },
          ]
        },
        {
          title: "Interface — Tray Icon & Configurações",
          items: [
            { id: "app19", text: "Tray icon com status visual", note: "Ícone no systray do Windows com estados: 🟢 gravando, ⏸️ pausado, 🔴 erro/desconectado. Clique para pausar/retomar." },
            { id: "app20", text: "Menu de contexto do tray icon", note: "Botão direito: Pausar/Retomar, Abrir Configurações, Ver Log, Sair. Ícone muda conforme estado." },
            { id: "app21", text: "Janela de configurações completa", note: "Abas ou seções: Microfone (dropdown de dispositivos), Backend (URL, source_id), VAD (silence_ms, min_speech_ms), Whisper (modelo, idioma). Botão Salvar + Testar Conexão." },
            { id: "app22", text: "Contador/log de transcrições enviadas", note: "Quantidade de transcrições enviadas nesta sessão, última enviada (preview), erros de envio. Pode ser tooltip no tray icon." },
          ]
        },
        {
          title: "Persistência & Auto-start",
          items: [
            { id: "app23", text: "Configurações salvas localmente (config.json ou .env)", note: "Arquivo de config em %APPDATA%\\Cerebro\\ ou pasta do app. Carregado automaticamente na inicialização." },
            { id: "app24", text: "Auto-start com login do Windows", note: "Adicionar entrada em HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run ou criar atalho na pasta Startup. Configurável (toggle na UI)." },
            { id: "app25", text: "Migração de config ao atualizar app", note: "Ao lançar nova versão, preservar configurações existentes. Versionar o formato do config.json." },
          ]
        },
        {
          title: "Build & Distribuição",
          items: [
            { id: "app26", text: "Gerar executável standalone (.exe)", note: "PyInstaller: pyinstaller --onefile --windowed app.py. Electron: electron-builder --win. Testar em máquina sem o ambiente de dev." },
            { id: "app27", text: "Criar installer para usuário final", note: "Inno Setup ou NSIS (Python), electron-builder NSIS (Electron). Installer cria atalho, configura auto-start opcional." },
            { id: "app28", text: "Documentar instalação e configuração inicial", note: "Guia de instalação: baixar .exe, rodar, configurar URL do backend, selecionar microfone, testar. Máximo 5 passos." },
          ]
        }
      ]
    },
    {
      id: "modulo2",
      label: "MÓDULO 2 — TRANSCRIÇÃO",
      color: "#A78BFA",
      icon: "✍️",
      groups: [
        {
          title: "Whisper Local",
          items: [
            { id: "m2a1", text: "Modelo Whisper Small carregado e funcionando", note: "whisper.load_model('small') em backend/modulo2_transcricao/whisper_engine.py. Modelo baixado no primeiro uso (~460MB). Cache em /root/.cache/whisper." },
            { id: "m2a2", text: "Função de transcrição de buffer implementada", note: "Recebe array numpy float32 (16kHz), retorna dict com text, language, segments. Implementado em whisper_engine.py." },
            { id: "m2a3", text: "Idioma fixo configurado (pt)", note: "WHISPER_LANGUAGE=pt no .env. Evita detecção automática de idioma que desperdiça tempo. Configurável para outros idiomas." },
            { id: "m2a4", text: "Fila de transcrição implementada (raw_audio_queue)", note: "Queue thread-safe em main.py. VAD produz AudioChunks, TranscriptionWorker consome. Sem bloqueio do pipeline de captura durante transcrição." },
            { id: "m2a5", text: "Medir latência de transcrição no hardware alvo", note: "Pendente: cronometrar transcrição de 10s de áudio no hardware do usuário. Essa medição define se haverá backlog na fila." },
            { id: "m2a6", text: "Filtro de transcrições curtas/inúteis", note: "Pendente: descartar transcrições com menos de 3 palavras ou apenas ruído ('hmm', 'né', sons curtos). Reduz ruído no banco." },
          ]
        },
        {
          title: "Metadados",
          items: [
            { id: "m2b1", text: "Timestamp de início/fim de cada fragmento capturado", note: "AudioChunk.captured_at preenchido em mic_source.py. duracao_ms calculado e salvo no banco." },
            { id: "m2b2", text: "Campo 'fonte' registrado em todas as transcrições", note: "Coluna 'fonte' na tabela transcricoes. Valores: windows_mic, alexa, linux_mic, manual. Configurável via CLIENT_SOURCE_ID no .env." },
          ]
        }
      ]
    },
    {
      id: "modulo3",
      label: "MÓDULO 3 — STORAGE BRUTO",
      color: "#34D399",
      icon: "🗄️",
      groups: [
        {
          title: "Schema do Banco",
          items: [
            { id: "m3a1", text: "Tabela 'transcricoes' criada com todos os campos", note: "id, texto, fonte, criado_em, duracao_ms, modelo_whisper, idioma, sessao_id, metadados (JSONB). Schema em backend/modulo3_armazenamento/schema.sql." },
            { id: "m3a2", text: "Tabela 'usuarios' — aguarda multi-usuário", note: "Não implementada ainda. Sistema atual é single-user. Criar quando escalar para múltiplos usuários (Módulo 5+)." },
            { id: "m3a3", text: "Índices em fonte e criado_em criados", note: "idx_transcricoes_fonte e idx_transcricoes_criado_em DESC. Consultas por data e por fonte serão performáticas." },
            { id: "m3a4", text: "Schema versionado e aplicado automaticamente", note: "schema.sql usa CREATE TABLE IF NOT EXISTS — idempotente. Aplicado pelo entrypoint.sh a cada boot. Futuras migrations precisarão de controle de versão (Alembic, Flyway)." },
          ]
        },
        {
          title: "Persistência",
          items: [
            { id: "m3b1", text: "StorageWorker implementado (text_queue → INSERT)", note: "backend/modulo3_armazenamento/storage_worker.py consome text_queue e insere na tabela transcricoes. Thread dedicada, sem bloquear transcrição." },
            { id: "m3b2", text: "ThreadedConnectionPool para múltiplas threads", note: "psycopg2.pool.ThreadedConnectionPool (min=1, max=5). Flask (Alexa) e StorageWorker compartilham pool sem conflito." },
            { id: "m3b3", text: "Erros de persistência logados", note: "Exceções capturadas e logadas via utils/logger.py. Sistema não quebra em caso de falha pontual de DB." },
            { id: "m3b4", text: "Teste de volume: 1000 inserções simuladas", note: "Pendente: script de stress test para validar performance do schema com volume real." },
          ]
        }
      ]
    },
    {
      id: "modulo4",
      label: "MÓDULO 4 — PROCESSAMENTO IA",
      color: "#FBBF24",
      icon: "🤖",
      groups: [
        {
          title: "Schema Estruturado (pós-processamento)",
          items: [
            { id: "m4a1", text: "Criar tabela 'entidades'", note: "Campos: id, nome, tipo (pessoa/empresa/projeto/lugar/conceito), descricao, usuario_id, criado_em." },
            { id: "m4a2", text: "Criar tabela 'fragmentos'", note: "Campos: id, transcricao_id (FK), texto, data_hora, usuario_id, importance_score (float 0-1)." },
            { id: "m4a3", text: "Criar tabela 'fragmento_entidade'", note: "Campos: fragmento_id (FK), entidade_id (FK), relevancia (float). Esta tabela é o coração do sistema de memória." },
            { id: "m4a4", text: "Criar tabela 'topicos'", note: "Campos: id, nome, descricao, topico_pai_id (self-referencing FK para árvore), usuario_id." },
            { id: "m4a5", text: "Criar tabela 'fragmento_topico'", note: "Campos: fragmento_id, topico_id, relevancia." },
          ]
        },
        {
          title: "Prompt Engineering",
          items: [
            { id: "m4b1", text: "Montar prompt do sistema com perfil do usuário (Módulo 0)", note: "O prompt deve incluir: quem é o usuário, suas categorias raiz, regras de categorização e exemplos. Isso é o que torna a categorização precisa." },
            { id: "m4b2", text: "Definir formato de saída JSON estruturado", note: "Pedir à LLM para retornar JSON com: entidades[], topico_principal, topico_secundario, importance_score, resumo_curto. Usar json_mode se disponível." },
            { id: "m4b3", text: "Implementar validação do JSON retornado", note: "LLM às vezes retorna JSON malformado. Validar com try/except json.loads() e ter fallback para reprocessar ou descartar." },
            { id: "m4b4", text: "Testar prompt com 20 transcrições reais manualmente", note: "Antes de automatizar, rodar manualmente e avaliar: as entidades fazem sentido? Os tópicos estão corretos? Ajustar prompt conforme os erros." },
          ]
        },
        {
          title: "Pipeline Batch",
          items: [
            { id: "m4c1", text: "Script de batch processamento", note: "Query: SELECT * FROM transcricoes WHERE status='nao_processado' ORDER BY criado_em. Processar em lotes de 10-20 para não estourar contexto da LLM." },
            { id: "m4c2", text: "Deduplicação de entidades", note: "Antes de inserir entidade, checar se já existe pelo nome (case-insensitive). Se sim, usar a existente. Evita 'João' e 'joão' como entidades separadas." },
            { id: "m4c3", text: "Atualizar status para 'processado' após sucesso", note: "UPDATE transcricoes SET status='processado' WHERE id=X — só após confirmar que todos os dados foram salvos nas tabelas estruturadas." },
            { id: "m4c4", text: "Agendamento do batch (diário, ex: 23h)", note: "Linux: cron job. Windows: Task Scheduler. Ou APScheduler dentro do Python para independência de SO." },
            { id: "m4c5", text: "Log detalhado do batch", note: "Registrar: quantas transcrições processadas, custo estimado em tokens, erros, tempo total de execução." },
            { id: "m4c6", text: "Limite de custo diário", note: "Se o batch está custando mais do que $X/dia, parar e alertar. Proteção contra loop infinito ou volume inesperado." },
          ]
        }
      ]
    },
    {
      id: "modulo6",
      label: "MÓDULO 6 — CONSULTA (MVP)",
      color: "#F472B6",
      icon: "🔍",
      groups: [
        {
          title: "Interface Web Local",
          items: [
            { id: "m6a1", text: "Flask já instalado e rodando (backend usa)", note: "Flask está no requirements.txt e em uso para os webhooks. Reutilizar para endpoints de consulta." },
            { id: "m6a2", text: "Endpoint de busca por texto (GET /search?q=)", note: "ILIKE no banco em texto e retorna fragmentos ordenados por data. Simples, mas muito útil." },
            { id: "m6a3", text: "Endpoint de busca por entidade (GET /entity/:nome)", note: "Retorna todos os fragmentos ligados à entidade com datas e tópicos." },
            { id: "m6a4", text: "Página HTML básica de busca", note: "Campo de input + botão + lista de resultados. Funcionalidade primeiro, estética depois." },
            { id: "m6a5", text: "Exibição de contexto nos resultados", note: "Mostrar: texto, data/hora, tópico, entidades relacionadas. Dar contexto suficiente para o fragmento fazer sentido." },
            { id: "m6a6", text: "Filtro por período (data início / data fim)", note: "'Tudo que falei sobre João em fevereiro' — filtro de data é essencial e simples de implementar." },
          ]
        }
      ]
    },
    {
      id: "modulo7",
      label: "MÓDULO 7 — MEMÓRIA SEMÂNTICA (MVP)",
      color: "#60A5FA",
      icon: "🧠",
      groups: [
        {
          title: "Embeddings Básicos",
          items: [
            { id: "m7a1", text: "Instalar sentence-transformers", note: "pip install sentence-transformers — gera embeddings localmente sem custo de API. Modelo recomendado para PT-BR: paraphrase-multilingual-MiniLM-L12-v2" },
            { id: "m7a2", text: "Instalar pgvector no PostgreSQL", note: "Extensão do Postgres para busca vetorial. CREATE EXTENSION vector; — Evita precisar de banco separado (Pinecone, Weaviate) no MVP." },
            { id: "m7a3", text: "Adicionar coluna embedding na tabela fragmentos", note: "ALTER TABLE fragmentos ADD COLUMN embedding vector(384); — 384 dimensões para o modelo MiniLM." },
            { id: "m7a4", text: "Gerar embeddings no pipeline batch", note: "Após processar cada fragmento, gerar embedding e salvar. Custo zero (local). Adicionar ao tempo estimado do batch." },
            { id: "m7a5", text: "Busca por similaridade semântica", note: "SELECT texto, 1-(embedding <=> $1) AS score FROM fragmentos ORDER BY score DESC LIMIT 10 — sintaxe pgvector." },
          ]
        },
        {
          title: "Importance Score",
          items: [
            { id: "m7b1", text: "Definir lista de palavras-chave de alta importância", note: "Ex: 'importante', 'não esquecer', 'ideia', 'preciso', 'urgente', 'decisão', 'meta'. Fragmentos com essas palavras recebem score mais alto." },
            { id: "m7b2", text: "Implementar cálculo básico de importance_score", note: "Score base = 0.3. Presença de palavras-chave: +0.3. Duração > 30s: +0.2. Múltiplas entidades: +0.2. Clampear entre 0 e 1." },
            { id: "m7b3", text: "Usar importance_score como filtro na consulta", note: "Opção na interface: 'mostrar só importantes' (score > 0.6). Reduz ruído nas buscas." },
          ]
        },
        {
          title: "Query Engine Básico",
          items: [
            { id: "m7c1", text: "Pipeline de consulta combinada", note: "Para cada pergunta: 1) extrair entidades 2) buscar por entidade 3) buscar por embedding 4) unir resultados 5) ranquear por score+data." },
            { id: "m7c2", text: "Montar contexto estruturado para LLM responder", note: "Não enviar todos os fragmentos crus. Formatar: [DATA] [TÓPICO] texto. Top 10-15 fragmentos por consulta." },
            { id: "m7c3", text: "Endpoint de pergunta em linguagem natural (POST /ask)", note: "Body: {pergunta: 'O que eu falei sobre o projeto X?'} — passa pelo pipeline completo e retorna resposta gerada pela LLM." },
          ]
        }
      ]
    },
    {
      id: "modulo0",
      label: "MÓDULO 0 — PERFIL DO USUÁRIO",
      color: "#FB923C",
      icon: "👤",
      groups: [
        {
          title: "Configuração Inicial",
          items: [
            { id: "m0a1", text: "Criar tabela 'perfis'", note: "Campos: id, usuario_id, nome, profissao, empresa, contexto_geral, idioma_principal." },
            { id: "m0a2", text: "Criar tabela 'categorias'", note: "Campos: id, nome, descricao, cor, icone, categoria_pai_id (self-ref), usuario_id." },
            { id: "m0a3", text: "Popular categorias raiz do seu contexto", note: "Definir suas categorias ANTES de usar. Ex: Trabalho, Pessoal, Projetos, Ideias, Saúde. Isso guia toda a categorização." },
            { id: "m0a4", text: "Criar tabela 'regras_categorizacao'", note: "Campos: id, tipo (keyword/pessoa/negativa), valor, categoria_id, usuario_id." },
            { id: "m0a5", text: "Definir regras iniciais de categorização", note: "Associar pessoas conhecidas às categorias corretas. Ex: nomes de clientes → Trabalho > Clientes." },
            { id: "m0a6", text: "Integrar perfil no prompt do batch (Módulo 4)", note: "O prompt deve carregar dinamicamente as categorias e regras do banco. Não hardcodar no prompt." },
          ]
        }
      ]
    },
    {
      id: "sistema",
      label: "SISTEMA & OPERAÇÃO",
      color: "#94A3B8",
      icon: "🔧",
      groups: [
        {
          title: "Script Principal",
          items: [
            { id: "s1", text: "main.py orquestra todas as threads", note: "Sobe: StorageWorker, TranscriptionWorker, MicrophoneSource (se disponível), Flask (Alexa + webhooks). Graceful shutdown com SIGINT/SIGTERM." },
            { id: "s2", text: "Startup automático com o sistema (systemd / Task Scheduler)", note: "Docker: docker-compose up -d já persiste entre reboots se restart: unless-stopped. Pendente: configurar Docker para iniciar com o sistema." },
            { id: "s3", text: "Indicador visual de status nos logs", note: "Logs com ícones: ✅ iniciando | 🎤 capturando | ✍️ transcrevendo | 💾 salvando | ❌ erro. Implementado via utils/logger.py." },
          ]
        },
        {
          title: "Testes & Validação",
          items: [
            { id: "s4", text: "Teste ponta a ponta confirmado: falar → ver no banco", note: "Testado e funcionando. Pipeline completo validado: windows_mic_sender → POST → backend → PostgreSQL. Verificar com make db-debug." },
            { id: "s5", text: "Teste de robustez: rodar 2h seguidas", note: "Pendente: verificar memória crescendo, filas travando, conexões de banco abertas demais, erros silenciosos." },
            { id: "s6", text: "Teste de qualidade de transcrição no ambiente real", note: "Pendente: falar 10 frases e comparar com texto gerado. Precisão < 80% → investigar microfone, ruído, distância." },
            { id: "s7", text: "Teste do batch com dados reais (Módulo 4)", note: "Pendente: após 1 dia de uso, rodar batch e verificar entidades, tópicos, importance scores." },
          ]
        },
        {
          title: "Segurança & Privacidade",
          items: [
            { id: "s8", text: "Nenhum áudio sai do computador", note: "Confirmado: apenas texto transcrito trafega. windows_mic_sender transcreve localmente e envia só o texto. Backend recebe só texto." },
            { id: "s9", text: "Backup do banco configurado (make db-backup)", note: "make db-backup gera backup_YYYYMMDD_HHMMSS.sql via pg_dump. Agendar execução semanal no cron." },
            { id: "s10", text: "Permissões de arquivo do .env e banco", note: "Pendente: chmod 600 .env. Dados pessoais sensíveis não devem ser legíveis por outros usuários do sistema." },
          ]
        }
      ]
    }
  ]
};

export default function CerebroChecklist() {
  const [checked, setChecked] = useState(initialChecked);
  const [expanded, setExpanded] = useState({ ambiente: true });
  const [expandedNotes, setExpandedNotes] = useState({});
  const [filter, setFilter] = useState("all");

  const toggle = (id) => setChecked(p => ({ ...p, [id]: !p[id] }));
  const toggleSection = (id) => setExpanded(p => ({ ...p, [id]: !p[id] }));
  const toggleNote = (id) => setExpandedNotes(p => ({ ...p, [id]: !p[id] }));

  const totalItems = data.sections.flatMap(s => s.groups.flatMap(g => g.items)).length;
  const checkedCount = Object.values(checked).filter(Boolean).length;
  const progress = Math.round((checkedCount / totalItems) * 100);

  const getSectionProgress = (section) => {
    const items = section.groups.flatMap(g => g.items);
    const done = items.filter(i => checked[i.id]).length;
    return { done, total: items.length, pct: Math.round((done / items.length) * 100) };
  };

  return (
    <div style={{
      background: "#0A0A0F",
      minHeight: "100vh",
      fontFamily: "'Courier New', 'Lucida Console', monospace",
      color: "#E2E8F0",
      padding: "0",
    }}>
      {/* Header */}
      <div style={{
        background: "linear-gradient(135deg, #0A0A0F 0%, #0F172A 50%, #0A0A0F 100%)",
        borderBottom: "1px solid #1E293B",
        padding: "32px 24px 24px",
        position: "sticky",
        top: 0,
        zIndex: 100,
        backdropFilter: "blur(10px)",
      }}>
        <div style={{ maxWidth: 900, margin: "0 auto" }}>
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 16 }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                <span style={{ fontSize: 11, letterSpacing: 4, color: "#00FFB2", textTransform: "uppercase", fontWeight: 700 }}>PROJETO</span>
              </div>
              <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0, letterSpacing: -1, color: "#F8FAFC" }}>
                CEREBRO <span style={{ color: "#00FFB2" }}>_</span> CHECKLIST
              </h1>
              <p style={{ margin: "6px 0 0", fontSize: 12, color: "#64748B", letterSpacing: 1 }}>
                MVP CORE — SEGUNDO CÉREBRO COM VOZ
              </p>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 42, fontWeight: 700, color: "#00FFB2", lineHeight: 1, fontFamily: "monospace" }}>
                {progress}<span style={{ fontSize: 20, color: "#334155" }}>%</span>
              </div>
              <div style={{ fontSize: 11, color: "#475569", marginTop: 4 }}>
                {checkedCount} / {totalItems} concluídos
              </div>
            </div>
          </div>

          {/* Progress bar */}
          <div style={{ marginTop: 20, background: "#1E293B", borderRadius: 2, height: 3, overflow: "hidden" }}>
            <div style={{
              height: "100%",
              width: `${progress}%`,
              background: "linear-gradient(90deg, #00FFB2, #60A5FA)",
              transition: "width 0.5s ease",
              borderRadius: 2,
            }} />
          </div>

          {/* Filter */}
          <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
            {["all", "pending", "done"].map(f => (
              <button key={f} onClick={() => setFilter(f)} style={{
                padding: "4px 14px",
                fontSize: 10,
                letterSpacing: 2,
                textTransform: "uppercase",
                border: `1px solid ${filter === f ? "#00FFB2" : "#1E293B"}`,
                background: filter === f ? "rgba(0,255,178,0.08)" : "transparent",
                color: filter === f ? "#00FFB2" : "#475569",
                borderRadius: 2,
                cursor: "pointer",
                fontFamily: "inherit",
              }}>
                {f === "all" ? "Todos" : f === "pending" ? "Pendentes" : "Feitos"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Sections */}
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "24px 16px 80px" }}>
        {data.sections.map(section => {
          const sp = getSectionProgress(section);
          const isOpen = expanded[section.id];

          return (
            <div key={section.id} style={{ marginBottom: 16 }}>
              {/* Section Header */}
              <button
                onClick={() => toggleSection(section.id)}
                style={{
                  width: "100%",
                  background: "rgba(15,23,42,0.8)",
                  border: `1px solid ${isOpen ? section.color + "40" : "#1E293B"}`,
                  borderLeft: `3px solid ${section.color}`,
                  padding: "14px 18px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  borderRadius: "0 4px 4px 0",
                  transition: "all 0.2s",
                  fontFamily: "inherit",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 16 }}>{section.icon}</span>
                  <span style={{ fontSize: 11, letterSpacing: 3, color: section.color, fontWeight: 700 }}>
                    {section.label}
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{ width: 80, height: 2, background: "#1E293B", borderRadius: 1, overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${sp.pct}%`, background: section.color, borderRadius: 1 }} />
                    </div>
                    <span style={{ fontSize: 10, color: "#64748B", fontFamily: "monospace" }}>
                      {sp.done}/{sp.total}
                    </span>
                  </div>
                  <span style={{ color: "#334155", fontSize: 14 }}>{isOpen ? "▲" : "▼"}</span>
                </div>
              </button>

              {/* Groups */}
              {isOpen && section.groups.map((group, gi) => (
                <div key={gi} style={{ marginTop: 1 }}>
                  <div style={{
                    padding: "8px 18px",
                    background: "#0D1626",
                    borderLeft: `3px solid ${section.color}20`,
                    fontSize: 9,
                    letterSpacing: 3,
                    color: "#475569",
                    textTransform: "uppercase",
                  }}>
                    {group.title}
                  </div>

                  {group.items
                    .filter(item => {
                      if (filter === "pending") return !checked[item.id];
                      if (filter === "done") return checked[item.id];
                      return true;
                    })
                    .map((item) => (
                      <div key={item.id} style={{
                        borderLeft: `3px solid ${checked[item.id] ? section.color + "60" : "#1E293B"}`,
                        background: checked[item.id] ? "rgba(15,23,42,0.4)" : "#0D1420",
                        marginBottom: 1,
                        transition: "all 0.15s",
                      }}>
                        <div
                          style={{
                            display: "flex",
                            alignItems: "flex-start",
                            gap: 12,
                            padding: "12px 18px",
                            cursor: "pointer",
                          }}
                          onClick={() => toggle(item.id)}
                        >
                          {/* Checkbox */}
                          <div style={{
                            width: 16,
                            height: 16,
                            border: `1px solid ${checked[item.id] ? section.color : "#2D3748"}`,
                            background: checked[item.id] ? section.color : "transparent",
                            borderRadius: 2,
                            flexShrink: 0,
                            marginTop: 2,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            transition: "all 0.15s",
                          }}>
                            {checked[item.id] && <span style={{ fontSize: 10, color: "#0A0A0F", fontWeight: 900 }}>✓</span>}
                          </div>

                          {/* Text */}
                          <div style={{ flex: 1 }}>
                            <span style={{
                              fontSize: 13,
                              color: checked[item.id] ? "#475569" : "#CBD5E1",
                              textDecoration: checked[item.id] ? "line-through" : "none",
                              lineHeight: 1.5,
                            }}>
                              {item.text}
                            </span>

                            {/* Note toggle */}
                            {item.note && (
                              <button
                                onClick={(e) => { e.stopPropagation(); toggleNote(item.id); }}
                                style={{
                                  marginLeft: 10,
                                  fontSize: 9,
                                  letterSpacing: 1,
                                  color: expandedNotes[item.id] ? section.color : "#334155",
                                  background: "transparent",
                                  border: `1px solid ${expandedNotes[item.id] ? section.color + "40" : "#1E293B"}`,
                                  padding: "1px 6px",
                                  borderRadius: 2,
                                  cursor: "pointer",
                                  fontFamily: "inherit",
                                  verticalAlign: "middle",
                                }}
                              >
                                {expandedNotes[item.id] ? "▲ OBS" : "▼ OBS"}
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Note expanded */}
                        {item.note && expandedNotes[item.id] && (
                          <div style={{
                            margin: "0 18px 12px 46px",
                            padding: "10px 14px",
                            background: "rgba(0,0,0,0.3)",
                            borderLeft: `2px solid ${section.color}30`,
                            fontSize: 11,
                            color: "#64748B",
                            lineHeight: 1.7,
                            borderRadius: "0 2px 2px 0",
                          }}>
                            <span style={{ color: section.color, fontSize: 9, letterSpacing: 2, marginRight: 8 }}>OBS</span>
                            {item.note}
                          </div>
                        )}
                      </div>
                    ))}
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

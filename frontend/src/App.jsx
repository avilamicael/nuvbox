import { useState } from "react";

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
            { id: "a1", text: "Verificar versão do Python instalada", note: "Requer Python 3.10 ou superior. Versões antigas causam incompatibilidade com Whisper e silero-vad." },
            { id: "a2", text: "Instalar Python 3.10+ se necessário", note: "Recomendado: usar pyenv para gerenciar versões sem conflito com o sistema." },
            { id: "a3", text: "Criar ambiente virtual dedicado ao projeto", note: "Use: python -m venv jarvis-env | Evita conflito de dependências com outros projetos." },
            { id: "a4", text: "Ativar o ambiente virtual", note: "Linux/Mac: source jarvis-env/bin/activate | Windows: jarvis-env\\Scripts\\activate" },
            { id: "a5", text: "Verificar pip atualizado dentro do venv", note: "pip install --upgrade pip" },
          ]
        },
        {
          title: "Dependências de Sistema",
          items: [
            { id: "b1", text: "Instalar ffmpeg no sistema operacional", note: "Whisper depende do ffmpeg para processar áudio. Sem isso, a transcrição não funciona. Linux: apt install ffmpeg | Mac: brew install ffmpeg | Windows: baixar binário e adicionar ao PATH." },
            { id: "b2", text: "Instalar PortAudio (dependência do PyAudio)", note: "Linux: apt install portaudio19-dev | Mac: brew install portaudio | Windows: geralmente não precisa, PyAudio tem wheel pré-compilado." },
            { id: "b3", text: "Verificar se microfone USB está reconhecido pelo sistema", note: "Linux: arecord -l | Mac: Preferências > Som > Entrada | Windows: Painel de Som. Faça isso ANTES de instalar qualquer biblioteca." },
          ]
        },
        {
          title: "Pacotes Python",
          items: [
            { id: "c1", text: "Instalar openai-whisper", note: "pip install openai-whisper — vai baixar o modelo small (~460MB) na primeira execução." },
            { id: "c2", text: "Instalar silero-vad", note: "pip install silero-vad — ou via torch: depende da versão do PyTorch instalada." },
            { id: "c3", text: "Instalar PyTorch (CPU ou GPU)", note: "Se tiver GPU NVIDIA: instalar versão CUDA para acelerar Whisper significativamente. CPU já funciona para o MVP. Ver pytorch.org para o comando correto." },
            { id: "c4", text: "Instalar PyAudio", note: "pip install PyAudio — em caso de erro no Windows, usar: pip install pipwin && pipwin install pyaudio" },
            { id: "c5", text: "Instalar psycopg2-binary", note: "pip install psycopg2-binary — conector Python para PostgreSQL. A versão binary não exige compilação local." },
            { id: "c6", text: "Instalar python-dotenv", note: "pip install python-dotenv — para gerenciar variáveis de ambiente (API keys, credenciais do banco) sem deixar no código." },
            { id: "c7", text: "Instalar openai (cliente Python)", note: "pip install openai — para chamar GPT-4o mini no processamento batch." },
            { id: "c8", text: "Gerar arquivo requirements.txt", note: "pip freeze > requirements.txt — documenta todas as dependências para reproducibilidade." },
          ]
        },
        {
          title: "PostgreSQL",
          items: [
            { id: "d1", text: "Instalar PostgreSQL localmente", note: "Versão 14+ recomendada. Linux: apt install postgresql | Mac: brew install postgresql | Windows: installer oficial em postgresql.org." },
            { id: "d2", text: "Iniciar serviço do PostgreSQL", note: "Linux: sudo systemctl start postgresql | Mac: brew services start postgresql" },
            { id: "d3", text: "Criar banco de dados para o projeto", note: "createdb jarvis_db ou via psql: CREATE DATABASE jarvis_db;" },
            { id: "d4", text: "Criar usuário dedicado ao projeto", note: "Não usar o usuário postgres padrão em desenvolvimento. CREATE USER jarvis_user WITH PASSWORD 'senha'; GRANT ALL ON DATABASE jarvis_db TO jarvis_user;" },
            { id: "d5", text: "Testar conexão com psycopg2", note: "Escrever um script simples de 5 linhas que conecta e imprime a versão do banco. Se falhar aqui, não adianta avançar." },
          ]
        },
        {
          title: "API OpenAI",
          items: [
            { id: "e1", text: "Criar conta na OpenAI se não tiver", note: "platform.openai.com" },
            { id: "e2", text: "Adicionar créditos (mínimo $5)", note: "GPT-4o mini é barato. $5 dura semanas em uso moderado. Mas sem saldo a API rejeita as chamadas silenciosamente às vezes." },
            { id: "e3", text: "Gerar API key", note: "Guardar em arquivo .env: OPENAI_API_KEY=sk-... | NUNCA commitar essa chave no git." },
            { id: "e4", text: "Adicionar .env ao .gitignore", note: "Passo crítico antes de qualquer commit. Vazamento de API key é um problema sério." },
            { id: "e5", text: "Testar chamada simples à API", note: "Uma chamada de teste com 'Olá' para confirmar que a key funciona e tem crédito." },
          ]
        },
        {
          title: "Estrutura de Pastas",
          items: [
            { id: "f1", text: "Criar estrutura de diretórios do projeto", note: "Sugestão: /jarvis | /modules (input, transcricao, storage, ia, consulta) | /config | /scripts | /tests | /logs" },
            { id: "f2", text: "Inicializar repositório git", note: "git init + criar .gitignore com: .env, __pycache__, *.pyc, jarvis-env/, logs/*.log" },
            { id: "f3", text: "Criar arquivo de configuração central", note: "config/settings.py ou config.yaml centralizando: paths, thresholds do VAD, modelo do Whisper, schedule do batch." },
          ]
        }
      ]
    },
    {
      id: "modulo1",
      label: "MÓDULO 1 — INPUT & VAD",
      color: "#FF6B35",
      icon: "🎙️",
      groups: [
        {
          title: "Captura de Áudio",
          items: [
            { id: "m1a1", text: "Listar dispositivos de áudio disponíveis", note: "Script simples com PyAudio para listar todos os inputs. Anotar o índice do microfone USB que vai usar." },
            { id: "m1a2", text: "Implementar captura contínua em chunks", note: "Capturar em janelas de 30ms a 100ms. Chunks muito grandes atrasam a detecção de voz. Muito pequenos aumentam overhead." },
            { id: "m1a3", text: "Configurar taxa de amostragem em 16kHz", note: "Whisper espera 16kHz. Se capturar em outra taxa (44.1kHz do microfone), precisa fazer resample antes de passar para o Whisper." },
            { id: "m1a4", text: "Testar captura básica salvando em arquivo .wav", note: "Antes de conectar ao Whisper, salvar 10 segundos de áudio e ouvir. Se o arquivo soar bem, o hardware está OK." },
          ]
        },
        {
          title: "VAD — Detecção de Voz",
          items: [
            { id: "m1b1", text: "Carregar modelo silero-vad", note: "O modelo é carregado via torch.hub. Na primeira vez faz download. Depois fica em cache local." },
            { id: "m1b2", text: "Implementar detecção de início de fala", note: "Quando VAD detecta voz: começar a acumular chunks de áudio em buffer." },
            { id: "m1b3", text: "Implementar detecção de fim de fala", note: "Após X segundos de silêncio (ex: 1.5s), considerar utterance completa e enviar para transcrição. Ajustar threshold conforme ambiente." },
            { id: "m1b4", text: "Calibrar threshold de sensibilidade", note: "Ambientes barulhentos precisam de threshold mais alto. Testar com ruído real do seu ambiente (ac, teclado, etc)." },
            { id: "m1b5", text: "Implementar modo sleep por inatividade", note: "Após 10 min sem voz detectada, pausar captura e reduzir uso de CPU." },
            { id: "m1b6", text: "Implementar wake por detecção de voz", note: "Manter uma thread leve ouvindo mesmo no sleep para reativar quando voz aparecer." },
          ]
        },
        {
          title: "Contexto de Ativação",
          items: [
            { id: "m1c1", text: "Implementar janela de horário configurável", note: "Ler do config: hora_inicio=8, hora_fim=22. Não gravar fora desse horário. Simples de implementar com datetime." },
            { id: "m1c2", text: "Log de ativação e desativação", note: "Registrar quando o sistema ligou, desligou e quantos fragmentos capturou. Útil para debug." },
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
            { id: "m2a1", text: "Baixar e testar modelo Whisper Small", note: "whisper.load_model('small') — ~460MB. Testar com arquivo .wav de 30 segundos. Medir tempo de transcrição no seu hardware." },
            { id: "m2a2", text: "Implementar função de transcrição de buffer", note: "Recebe array numpy de áudio (16kHz), retorna string com texto transcrito + confidence se disponível." },
            { id: "m2a3", text: "Configurar idioma fixo (pt-BR)", note: "Passar language='pt' para o Whisper. Sem isso ele tenta detectar o idioma e desperdiça tempo e tokens." },
            { id: "m2a4", text: "Implementar fila de transcrição", note: "VAD produz fragmentos mais rápido do que Whisper processa (em CPU). Usar queue.Queue para não perder fragmentos." },
            { id: "m2a5", text: "Medir latência de transcrição", note: "Quanto tempo demora para transcrever 10s de áudio no seu hardware? Isso define se a fila vai crescer ou não." },
            { id: "m2a6", text: "Implementar filtro de transcrições curtas/inúteis", note: "Transcrições com menos de 3 palavras ou apenas ruído ('hmm', 'ah', 'né') devem ser descartadas ou marcadas com importance_score baixo." },
          ]
        },
        {
          title: "Metadados",
          items: [
            { id: "m2b1", text: "Capturar timestamp de início e fim de cada fragmento", note: "datetime.now() no início do chunk e no fim. Duração = diferença entre os dois." },
            { id: "m2b2", text: "Registrar fonte do input", note: "Para o MVP: sempre 'microfone_pc'. Mas já deixar o campo preparado para 'alexa', 'esp32', 'arquivo'." },
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
            { id: "m3a1", text: "Criar tabela 'transcricoes'", note: "Campos: id (serial PK), texto (text), data_hora (timestamptz), duracao_segundos (float), fonte (varchar), status (varchar default 'nao_processado'), usuario_id (int)." },
            { id: "m3a2", text: "Criar tabela 'usuarios'", note: "Campos: id (serial PK), nome (varchar), criado_em (timestamptz). Mesmo para uso solo, multi-usuário desde o início evita refatoração dolorosa depois." },
            { id: "m3a3", text: "Criar índice em data_hora e status", note: "CREATE INDEX idx_transcricoes_status ON transcricoes(status); — o batch vai fazer query por status='nao_processado' toda noite." },
            { id: "m3a4", text: "Criar script de migration versionado", note: "Não rodar SQL manual. Criar scripts numerados: 001_create_transcricoes.sql, 002_create_usuarios.sql. Facilita replicar o banco em outra máquina." },
          ]
        },
        {
          title: "Persistência",
          items: [
            { id: "m3b1", text: "Implementar função save_transcricao()", note: "Recebe: texto, data_hora, duracao, fonte, usuario_id. Salva no banco. Retorna o ID gerado. Tratar exceções de conexão." },
            { id: "m3b2", text: "Implementar retry em caso de falha de conexão", note: "Banco pode estar temporariamente indisponível. 3 tentativas com backoff exponencial antes de logar erro." },
            { id: "m3b3", text: "Implementar log de erros de persistência", note: "Se não conseguir salvar no banco, salvar em arquivo local temporário para não perder a transcrição." },
            { id: "m3b4", text: "Testar volume: inserir 1000 transcrições simuladas", note: "Garante que o schema aguenta uso real sem degradação de performance." },
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
            { id: "m4b4", text: "Testar prompt com 20 transcrições diversas manualmente", note: "Antes de automatizar, rodar manualmente e avaliar: as entidades fazem sentido? Os tópicos estão corretos? Ajustar prompt conforme os erros encontrados." },
          ]
        },
        {
          title: "Pipeline Batch",
          items: [
            { id: "m4c1", text: "Implementar script de batch processamento", note: "Query: SELECT * FROM transcricoes WHERE status='nao_processado' ORDER BY data_hora. Processar em lotes de 10-20 para não estourar contexto." },
            { id: "m4c2", text: "Implementar deduplicação de entidades", note: "Antes de inserir entidade, checar se já existe pelo nome (case-insensitive). Se sim, usar a existente. Evita 'João' e 'joão' como entidades separadas." },
            { id: "m4c3", text: "Atualizar status para 'processado' após sucesso", note: "UPDATE transcricoes SET status='processado' WHERE id=X — só após confirmar que todos os dados foram salvos nas tabelas estruturadas." },
            { id: "m4c4", text: "Implementar agendamento do batch", note: "Linux/Mac: cron job às 23:00. Windows: Task Scheduler. Ou usar APScheduler dentro do próprio Python." },
            { id: "m4c5", text: "Implementar log detalhado do batch", note: "Registrar: quantas transcrições processadas, custo estimado em tokens, erros encontrados, tempo total de execução." },
            { id: "m4c6", text: "Implementar limite de custo diário", note: "Se o batch está custando mais do que $X no dia, parar e alertar. Proteção contra loop infinito ou volume inesperado." },
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
            { id: "m6a1", text: "Instalar Flask ou FastAPI", note: "Flask é mais simples para MVP. FastAPI é melhor se quiser async e documentação automática. Para começar: Flask." },
            { id: "m6a2", text: "Criar endpoint de busca por texto", note: "GET /search?q=termo — faz ILIKE no banco em texto e retorna fragmentos ordenados por data." },
            { id: "m6a3", text: "Criar endpoint de busca por entidade", note: "GET /entity/João — retorna todos os fragmentos ligados à entidade 'João' com datas e tópicos." },
            { id: "m6a4", text: "Criar página HTML básica de busca", note: "Não precisa ser bonita. Campo de input + botão + lista de resultados. Funcionalidade primeiro." },
            { id: "m6a5", text: "Implementar exibição de contexto nos resultados", note: "Mostrar: texto do fragmento, data/hora, tópico, entidades relacionadas. Dar contexto suficiente para o fragmento fazer sentido." },
            { id: "m6a6", text: "Adicionar filtro por período (data início / data fim)", note: "'Tudo que falei sobre João em fevereiro' — filtro de data é essencial e simples de implementar." },
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
            { id: "m7a4", text: "Gerar embeddings no pipeline batch", note: "Após processar cada fragmento, gerar embedding do texto e salvar. Adicionar ao custo estimado do batch (é local, sem custo de API)." },
            { id: "m7a5", text: "Implementar busca por similaridade semântica", note: "SELECT texto, 1-(embedding <=> $1) AS score FROM fragmentos ORDER BY score DESC LIMIT 10 — sintaxe pgvector. Retorna os fragmentos mais similares à pergunta." },
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
            { id: "m7c1", text: "Implementar pipeline de consulta combinada", note: "Para cada pergunta: 1) extrair entidades 2) buscar por entidade 3) buscar por embedding 4) unir resultados 5) ranquear por score+data." },
            { id: "m7c2", text: "Montar contexto estruturado para LLM responder", note: "Não enviar todos os fragmentos crus. Montar um contexto formatado: [DATA] [TÓPICO] texto do fragmento. Top 10-15 fragmentos por consulta." },
            { id: "m7c3", text: "Implementar endpoint de pergunta em linguagem natural", note: "POST /ask com body {pergunta: 'O que eu falei sobre o projeto X?'} — passa pelo pipeline completo e retorna resposta gerada pela LLM." },
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
            { id: "m0a3", text: "Popular categorias raiz do seu contexto", note: "Definir suas categorias principais ANTES de começar a usar. Ex: Trabalho, Pessoal, Projetos, Ideias, Saúde. Isso guia toda a categorização." },
            { id: "m0a4", text: "Criar tabela 'regras_categorizacao'", note: "Campos: id, tipo (keyword/pessoa/negativa), valor, categoria_id, usuario_id." },
            { id: "m0a5", text: "Definir regras iniciais de categorização", note: "Associar pessoas conhecidas às categorias corretas. Ex: nomes de clientes → Trabalho > Clientes. Isso treina a LLM para o seu contexto específico." },
            { id: "m0a6", text: "Integrar perfil no prompt do batch (Módulo 4)", note: "O prompt deve carregar dinamicamente as categorias e regras do banco antes de processar. Não hardcodar no prompt." },
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
            { id: "s1", text: "Criar script main.py que inicia o sistema completo", note: "Deve subir: thread de captura, thread do VAD, thread de transcrição+fila, conexão com banco. Graceful shutdown com Ctrl+C." },
            { id: "s2", text: "Implementar startup automático com o PC", note: "Linux: systemd service ou @reboot no crontab | Windows: Task Scheduler com trigger 'logon' | Mac: launchd plist." },
            { id: "s3", text: "Implementar indicador visual de status", note: "Pode ser simples: print no terminal com ícone. 🔴 Dormindo | 🟢 Gravando | 🔵 Transcrevendo. Ajuda a saber se o sistema está funcionando." },
          ]
        },
        {
          title: "Testes & Validação",
          items: [
            { id: "s4", text: "Teste de ponta a ponta: falar → ver no banco", note: "Falar uma frase clara, esperar processamento, verificar no banco se chegou. Se isso funciona, o pipeline core está OK." },
            { id: "s5", text: "Teste de robustez: deixar rodar 2h seguidas", note: "Verificar: memória crescendo? Filas travando? Banco com conexões abertas demais? Erros silenciosos?" },
            { id: "s6", text: "Teste de qualidade de transcrição no seu ambiente", note: "Falar 10 frases diferentes e comparar com o texto gerado. Se precisão < 80%, investigar: qualidade do microfone, ruído ambiente, distância do microfone." },
            { id: "s7", text: "Teste do batch de processamento com dados reais", note: "Após 1 dia de uso, rodar o batch e verificar: entidades corretas? Tópicos fazem sentido? Importance scores razoáveis?" },
          ]
        },
        {
          title: "Segurança & Privacidade",
          items: [
            { id: "s8", text: "Confirmar que nenhum áudio sai do PC", note: "Só texto transcrito vai para a OpenAI. Verificar código: nenhum arquivo .wav ou buffer de áudio está sendo enviado para fora." },
            { id: "s9", text: "Implementar rotina de backup do banco", note: "pg_dump jarvis_db > backup_$(date +%Y%m%d).sql — agendar weekly. Meses de dados perdidos por falha de HD é devastador." },
            { id: "s10", text: "Configurar permissões de arquivo do banco e .env", note: "chmod 600 .env | Dados pessoais sensíveis não devem ser legíveis por outros usuários do sistema." },
          ]
        }
      ]
    }
  ]
};

export default function JarvisChecklist() {
  const [checked, setChecked] = useState({});
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
                JARVIS <span style={{ color: "#00FFB2" }}>_</span> CHECKLIST
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
                    .map((item, idx) => (
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

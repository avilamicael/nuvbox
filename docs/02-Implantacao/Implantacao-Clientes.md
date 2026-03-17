---
title: Implantação para Clientes
tags: [implantacao, clientes, deployment, produção, guia]
aliases: [Cliente Setup, Deployment]
---

# 🎯 Implantação para Clientes

Guia passo a passo para entregar e configurar o sistema em ambiente de cliente.

## 📋 Pré-requisitos

Cliente precisa ter:
- ✅ **Docker Desktop** (Mac/Windows) ou Docker + Compose (Linux)
- ✅ **Microfone** (USB ou integrado)
- ✅ **Disco**: ~5GB (sistema + modelos)
- ✅ **Internet**: Uma vez para baixar imagens

## 🚀 Entrega (O que você envia)

Empacote:
```
projeto-jarvis/
├── docker-compose.yml
├── .env.example
├── backend/
├── docs/
├── scripts/
└── README.md
```

**Forma de entrega:**
- Zip file
- GitHub private repo
- Cloud storage
- Pendrive

## 📋 Instruções para Cliente

### Passo 1: Extrair/Clonar
```bash
# Zip
unzip projeto-jarvis.zip
cd projeto-jarvis

# Ou: Git
git clone https://seu-repo.git
cd projeto-jarvis
```

### Passo 2: Instalar Docker

Se não tem:
- **Mac**: https://www.docker.com/products/docker-desktop
- **Windows**: https://www.docker.com/products/docker-desktop
- **Linux**:
  ```bash
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker $USER
  ```

Verifique:
```bash
docker --version
docker-compose --version
```

### Passo 3: Configurar

```bash
# Copiar template
cp .env.example .env

# Editar (mudanças OBRIGATÓRIAS)
nano .env
```

**Campos para MUDAR (obrigatório):**
```env
# Linha: DB_PASSWORD
DB_PASSWORD=senha_forte_unica_123!

# Linha: ALEXA_WEBHOOK_SECRET (se usar Alexa)
ALEXA_WEBHOOK_SECRET=chave_secreta_abc123
```

**Campos opcionais:**
```env
# Se tiver múltiplos microfones
MIC_DEVICE_ID=0    # Execute: docker-compose run --rm backend python -c "import sounddevice as sd; print(sd.query_devices())"

# Se quiser modelo menor/maior
WHISPER_MODEL=small    # tiny/base/small/medium/large

# Se quiser log mais detalhado
LOG_LEVEL=DEBUG
```

### Passo 4: Iniciar

```bash
docker-compose up -d
```

Aguarde 30 segundos (primeira vez baixa ~2GB).

### Passo 5: Verificar

```bash
# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f backend | head -20
```

Procure por:
```
✅ JARVIS BACKEND RODANDO
🎤 Microfone: escutando fala
📊 Banco de dados: armazenando transcrições
```

### Passo 6: Testar

```bash
# Fale 3 segundos no microfone
# Depois execute:
docker-compose logs backend | grep "Transcribed"
```

Se vir sua fala como texto → **Funcionando!**

## 🔄 Operação Diária

### Iniciar Sistema
```bash
docker-compose up -d
```

### Monitorar
```bash
# Ver logs em tempo real
docker-compose logs -f backend

# Ou (melhor):
./scripts/healthcheck.sh
```

### Parar Sistema
```bash
docker-compose down
```

(Dados são preservados)

### Ver Transcrições
```bash
docker-compose exec postgres psql -U jarvis -d jarvis_db \
  -c "SELECT criado_em, fonte, LEFT(texto, 80) FROM transcricoes ORDER BY id DESC LIMIT 10;"
```

## 🗓️ Manutenção

### Semanal
- Monitorar logs
- Verificar espaço em disco

### Mensal
```bash
# Backup do banco
docker-compose exec postgres pg_dump \
  -U jarvis jarvis_db > backup_$(date +%Y%m%d).sql

# Atualizar imagens
docker-compose pull
docker-compose up -d
```

### Limpeza (Opcional)
```bash
# Remover logs antigos (>7 dias)
find logs/ -name "*.log" -mtime +7 -delete

# Remover transcrições antigas
docker-compose exec postgres psql -U jarvis -d jarvis_db << EOF
DELETE FROM transcricoes WHERE criado_em < NOW() - INTERVAL '90 days';
VACUUM transcricoes;
EOF
```

## 🆘 Se Tiver Problemas

### "Connection refused"
```bash
docker-compose logs postgres
docker-compose down
docker-compose up -d
```

### "Microfone não detectado"
```bash
docker-compose run --rm backend \
  python -c "import sounddevice as sd; print(sd.query_devices())"
# Encontre seu microfone, mude MIC_DEVICE_ID em .env
docker-compose restart backend
```

### "Disco cheio"
```bash
# Ver tamanho
docker system df

# Deletar transcrições antigas
docker-compose exec postgres psql -U jarvis -d jarvis_db \
  -c "DELETE FROM transcricoes WHERE criado_em < NOW() - INTERVAL '30 days';"

# Aumentar espaço em disco
```

### "Whisper muito lento"
```bash
# Em .env, mude para modelo menor:
WHISPER_MODEL=tiny    # ou base
docker-compose restart backend
```

## 📞 Suporte ao Cliente

### O que você deve saber
- Local de instalação
- Como reiniciar (`docker-compose up -d`)
- Como ver logs (`docker-compose logs -f`)
- Contato para problemas

### O que cliente deve fazer antes de chamar você
1. Execute: `./scripts/healthcheck.sh`
2. Salve output
3. Execute: `docker-compose logs backend > debug.log`
4. Salve `debug.log`
5. Envie ambos quando entrar em contato

## ✅ Checklist para Cliente

Depois de setup:
- [ ] `docker-compose ps` mostra tudo "Up"
- [ ] Falei no mic, apareceu texto
- [ ] Banco tem minhas transcrições
- [ ] `./scripts/healthcheck.sh` passou
- [ ] Entendi como reiniciar
- [ ] Entendi como ver logs
- [ ] Entendi como parar/iniciar

---

## 🔗 Ver Também

- [[Variaveis-Ambiente|Variáveis de Ambiente]]
- [[Comandos|Comandos]]
- [[Erros-Comuns|Erros Comuns]]
- [[Diagnostico|Diagnóstico]]
- [[Deployment-Checklist|Checklist de Deployment]]

---

#implantacao #clientes #deployment #producao #guia

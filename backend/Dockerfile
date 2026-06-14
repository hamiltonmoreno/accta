FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# Scripts de operação (create_admin, find_orphan_uploads, …). Ficam em
# /app/scripts/ — o runbook corre-os com `docker compose exec backend`.
COPY scripts/ ./scripts/

RUN mkdir -p /app/uploads

# Porta 8000 (decisão do dono) — é a porta interna do container em produção
# (NPM: api.controlador.cv → accta-backend:8000). Antes a imagem era 8001-native
# e o compose de prod compensava com um override `command: --port 8000`; alinhar
# aqui torna o default da imagem honesto e remove essa divergência. O dev local
# bare-metal continua a usar `uvicorn --reload --port 8001` (não é o container).
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:8000/api/ || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

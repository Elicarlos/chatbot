FROM python:3.11-slim

# Instala dependencias do SO necessarias para pacotes Python (como psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Cria usuario nao-root para seguranca
RUN useradd -m -s /bin/bash botuser

WORKDIR /app

# Copia e instala dependencias primeiro (para melhor cache no docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o codigo fonte
COPY . .

# Altera permissoes para o usuario restrito
RUN chown -R botuser:botuser /app

# Ativa usuario nao-root
USER botuser

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]

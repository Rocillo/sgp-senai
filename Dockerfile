# ====================================================================
# [BLOCO] DEPLOY
# [NOME] Dockerfile
# [RESPONSABILIDADE] Containerizar a aplicação Flask SGP para execução em produção
# ====================================================================

# Usar uma imagem base oficial do Python slim (compatível com a versão 3.11 do projeto)
FROM python:3.11-slim

# Definir variáveis de ambiente para otimização do Python no container
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Definir diretório de trabalho no container
WORKDIR /app

# Instalar dependências básicas do sistema operacional
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas os requisitos primeiro para otimizar o cache de camadas do Docker
COPY requirements.txt .

# Instalar as dependências do Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar todo o código-fonte da aplicação para o container
COPY . .

# Expor a porta padrão da aplicação (Flask/Gunicorn)
EXPOSE 5000

# Comando padrão para rodar a aplicação em produção com Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "main:app"]

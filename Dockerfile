# Usa uma imagem Python leve
FROM python:3.10-slim

# Define variáveis de ambiente para otimizar o Python no Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependências do sistema operacional necessárias para GIS (Shapely/GEOS)
RUN apt-get update && apt-get install -y \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de requisitos e instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto para dentro do container
COPY . .

# Expõe a porta 5000
EXPOSE 5000

# Comando para iniciar a aplicação usando Gunicorn (Servidor de Produção)
# "app:create_app()" chama a função factory que definimos no app.py
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
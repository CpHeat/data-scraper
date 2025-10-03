# Utiliser une image Python officielle
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires pour psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier le fichier requirements.txt
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le projet
COPY . .

# Rendre le script exécutable
RUN chmod +x /app/run-scraper.sh

# Créer le répertoire pour le cache HTTP de Scrapy
RUN mkdir -p /app/httpcache

# Définir le répertoire de travail pour Scrapy
WORKDIR /app/data_scraper

# Commande par défaut pour exécuter le scraper
CMD ["bash", "/app/run-scraper.sh"]
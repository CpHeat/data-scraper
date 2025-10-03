# 📚 Book & Quote Scraper - Scrapy Training Project

Un projet de formation full-stack démontrant l'utilisation de **Scrapy** pour scraper des données, les enrichir avec des **embeddings vectoriels** (Azure OpenAI), et les stocker dans **Azure PostgreSQL** avec **pgvector** pour alimenter un moteur de recommandation sémantique.

## 🎯 Objectif

Ce projet fait partie d'un écosystème de formation comprenant :
- **Ce scraper** : Collecte automatisée de données (livres + citations) avec enrichissement vectoriel
- **API REST** : Expose les données et un moteur de recommandation intelligent
  - 🔗 [API Documentation](https://cpetit-bookscraperapi.kindglacier-2234e5a4.francecentral.azurecontainerapps.io/docs)
- **Infrastructure Azure** : Déploiement containerisé avec exécution périodique (cron jobs)

## 🏗️ Architecture

```
┌─────────────────────┐
│  Scrapy Spiders     │
│  ├─ Books Spider    │  ──→  books.toscrape.com
│  └─ Quotes Spider   │  ──→  quotes.toscrape.com/js
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Azure OpenAI API    │  ──→  Embeddings (text-embedding-3-small)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Azure PostgreSQL    │
│ + pgvector          │  ──→  Recherche vectorielle
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  FastAPI Backend    │  ──→  API + Moteur de recommandation
└─────────────────────┘
```

## ✨ Fonctionnalités

### 🕷️ Spiders

#### 1. **Books Spider** (`books`)
- **Source** : https://books.toscrape.com/
- **Technologie** : CrawlSpider avec règles de navigation
- **Données collectées** :
  - Métadonnées : titre, prix, rating, stock, UPC, genre
  - Description enrichie avec embeddings vectoriels (1536 dimensions)
  - Historique des variations (prix, stock, reviews) avec randomisation
- **Stockage** : 3 tables PostgreSQL (`books`, `genres`, `updates`)

#### 2. **Quotes Spider** (`quotes`)
- **Source** : https://quotes.toscrape.com/js
- **Technologie** : Parsing JavaScript avec `chompjs`
- **Données collectées** :
  - Citations avec tags
  - Auteurs avec liens Goodreads
- **Stockage** : 2 tables PostgreSQL (`quotes`, `authors`)

### 🧠 Intelligence Artificielle

- **Embeddings vectoriels** générés via Azure OpenAI (modèle `text-embedding-3-small`)
- **Index IVFFLAT** pour recherche sémantique ultra-rapide
- Utilisés par le moteur de recommandation de l'API

### 📊 Randomisation des données

Les données de `books.toscrape.com` étant statiques, le scraper ajoute des variations aléatoires :
- Prix : ±5€
- Stock : +0 à +5 unités
- Reviews : +0 à +5 avis
- Rating : ±1 étoile (limité entre 0 et 5)

Cela permet de simuler l'évolution temporelle des données pour l'endpoint de monitoring de l'API.

## 🚀 Installation & Usage

### Prérequis

- Python 3.11+
- Azure PostgreSQL avec extension `pgvector`
- Azure OpenAI API (déploiement embeddings)

### 1️⃣ Installation locale

```bash
# Cloner le repository
git clone https://github.com/CpHeat/data-scraper.git
cd Scraping

# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 2️⃣ Configuration

Créer un fichier `data_scraper/.env` avec vos credentials Azure :

```env
# Azure PostgreSQL
AZURE_PG_HOST=your-server.postgres.database.azure.com
AZURE_PG_PORT=5432
AZURE_PG_DB=your-database
AZURE_PG_USER=your-username
AZURE_PG_PASSWORD=your-password
AZURE_PG_SSL_MODE=require

# Azure OpenAI
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

### 3️⃣ Exécution locale

```bash
cd data_scraper

# Lister les spiders disponibles
scrapy list

# Exécuter un spider spécifique
scrapy crawl books
scrapy crawl quotes

# Exécuter avec logs détaillés
scrapy crawl books -L DEBUG
```

## 🐳 Docker

### Build et exécution locale

```bash
# Build de l'image
docker build -t data-scraper .

# Exécution avec docker-compose
docker-compose up --build

# Exécution manuelle
docker run --env-file data_scraper/.env data-scraper
```

## 🗄️ Schéma de base de données

### Tables créées automatiquement

#### **Books**
```sql
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    type VARCHAR(500),
    title VARCHAR(500),
    thumbnail VARCHAR(500),
    link VARCHAR(500),
    description TEXT,
    genre VARCHAR(100),
    upc VARCHAR(100) UNIQUE,
    availability BOOLEAN,
    description_embedding vector(1536)  -- Embeddings OpenAI
);

-- Index vectoriel pour recherche sémantique
CREATE INDEX books_description_embedding_idx
ON books USING ivfflat (description_embedding vector_cosine_ops);
```

#### **Updates** (Historique temporel)
```sql
CREATE TABLE updates (
    id SERIAL PRIMARY KEY,
    book_id INTEGER,
    tax INTEGER,
    rating INTEGER,
    price INTEGER,
    stock INTEGER,
    reviews INTEGER,
    scraped_at TIMESTAMPTZ
);
```

#### **Quotes**
```sql
CREATE TABLE quotes (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    author VARCHAR(200) NOT NULL,
    tags VARCHAR(500),
    scraped_at TIMESTAMPTZ,
    UNIQUE (content, author)
);
```

#### **Authors**
```sql
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(100) UNIQUE,
    name VARCHAR(200),
    link VARCHAR(200)
);
```

## 📦 Dépendances principales

```
scrapy          # Framework de scraping
psycopg2        # Driver PostgreSQL
pgvector        # Extension vectorielle
openai          # Client Azure OpenAI
chompjs         # Parser JavaScript
python-dotenv   # Gestion variables d'environnement
```

## 🔧 Configuration Scrapy

Le scraper est configuré pour un scraping efficace :

```python
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 32
CONCURRENT_REQUESTS_PER_DOMAIN = 32
DOWNLOAD_DELAY = 0.1
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 60*60*24  # 24h
```

## 🎓 Points d'apprentissage

Ce projet illustre :

1. **Scrapy avancé**
   - CrawlSpider avec règles de navigation
   - ItemLoaders pour normalisation
   - Pipelines personnalisés
   - Gestion du cache HTTP

2. **Parsing complexe**
   - Extraction CSS/XPath
   - Parsing de données JavaScript avec `chompjs`

3. **IA & Embeddings**
   - Génération d'embeddings avec Azure OpenAI
   - Optimisation (génération uniquement si description modifiée)

4. **Base de données vectorielle**
   - Extension pgvector
   - Index IVFFLAT pour recherche cosine
   - Gestion des upserts et duplicatas

5. **DevOps & Cloud**
   - Dockerisation
   - Azure Container Apps (Jobs)
   - Cron scheduling
   - Configuration via variables d'environnement

6. **Architecture Microservices**
   - Séparation scraper/API
   - Communication via base de données partagée

## 🔗 Ressources

- **API du projet** : [https://cpetit-bookscraperapi.kindglacier-2234e5a4.francecentral.azurecontainerapps.io/docs](https://cpetit-bookscraperapi.kindglacier-2234e5a4.francecentral.azurecontainerapps.io/docs)
- **Source des données** :
  - [books.toscrape.com](https://books.toscrape.com)
  - [quotes.toscrape.com](https://quotes.toscrape.com)
- **Documentation Scrapy** : [docs.scrapy.org](https://docs.scrapy.org)
- **pgvector** : [github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)

## 📝 Licence

MIT License - Voir le fichier [LICENSE](LICENSE)

## 👤 Auteur

**Charles Petit**
Projet de formation - Portfolio développeur IA
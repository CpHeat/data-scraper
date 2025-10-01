from random import randint, uniform
import random

import psycopg2
import os
from openai import AzureOpenAI

from itemadapter import ItemAdapter

from data_scraper.items.book import Book
from data_scraper.items.genre import Genre


class BookPGPersistencePipeline:
    collection_name = "books"

    def __init__(self, db_settings, openai_settings):
        self.db_settings = db_settings
        self.openai_settings = openai_settings
        self.connection = None
        self.openai_client = None

    @classmethod
    def from_crawler(cls, crawler):
        db_settings = {
            'host': crawler.settings.get('POSTGRES_HOST'),
            'port': crawler.settings.get('POSTGRES_PORT'),
            'database': crawler.settings.get('POSTGRES_DB'),
            'user': crawler.settings.get('POSTGRES_USER'),
            'password': crawler.settings.get('POSTGRES_PASSWORD'),
            'sslmode': crawler.settings.get('POSTGRES_SSL_MODE')
        }
        openai_settings = {
            'api_key': crawler.settings.get('AZURE_OPENAI_API_KEY'),
            'endpoint': crawler.settings.get('AZURE_OPENAI_ENDPOINT'),
            'api_version': crawler.settings.get('AZURE_OPENAI_API_VERSION'),
            'deployment': crawler.settings.get('AZURE_OPENAI_EMBEDDING_DEPLOYMENT')
        }
        return cls(db_settings, openai_settings)

    def open_spider(self, spider):
        # Open connection to DB
        try:
            self.connection = psycopg2.connect(**self.db_settings)
            spider.logger.info("✅ Azure PostgreSQL connected")

            # Initialize Azure OpenAI client
            if all(self.openai_settings.values()):
                self.openai_client = AzureOpenAI(
                    api_key=self.openai_settings['api_key'],
                    api_version=self.openai_settings['api_version'],
                    azure_endpoint=self.openai_settings['endpoint']
                )
                spider.logger.info("✅ Azure OpenAI client initialized")
            else:
                spider.logger.warning("⚠️ Azure OpenAI settings incomplete, embeddings will be skipped")

            # Create table if needed
            self._create_tables()

        except Exception as e:
            spider.logger.error(f"❌ Azure PostgreSQL connection error : {e}")
            raise

    def _create_tables(self):
        cursor = self.connection.cursor()

        # Activer l'extension pgvector
        cursor.execute('CREATE EXTENSION IF NOT EXISTS vector')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                type VARCHAR(500),
                title VARCHAR(500),
                thumbnail VARCHAR(500),
                link VARCHAR(500),
                description TEXT,
                genre VARCHAR(100),
                upc VARCHAR(100) UNIQUE,
                availability BOOLEAN,
                description_embedding vector(1536)
            )
        ''')

        # Create vector index for similarity search
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS books_description_embedding_idx
            ON books USING ivfflat (description_embedding vector_cosine_ops)
            WITH (lists = 100)
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS genres (
                id SERIAL PRIMARY KEY,
                genre VARCHAR(500) UNIQUE NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS updates (
                id SERIAL PRIMARY KEY,
                book_id INTEGER,
                tax INTEGER,
                rating INTEGER,
                price INTEGER,
                stock INTEGER,
                reviews INTEGER,
                scraped_at TIMESTAMPTZ
            )
        ''')
        self.connection.commit()
        cursor.close()

    def _ensure_connection(self, spider):
        """Vérifie et rétablit la connexion si nécessaire"""
        try:
            if self.connection is None or self.connection.closed:
                self.connection = psycopg2.connect(**self.db_settings)
                spider.logger.info("🔄 Reconnected to Azure PostgreSQL")
        except Exception as e:
            spider.logger.error(f"❌ Reconnection error: {e}")
            raise

    def close_spider(self, spider):
        # Close connection to DB
        if self.connection and not self.connection.closed:
            self.connection.close()
            spider.logger.info("✅ Disconnected from Azure PostgreSQL")

    def process_item(self, item, spider):
        if isinstance(item, Book):
            adapter = ItemAdapter(item).asdict()
            self._save_book(adapter, spider)
            return item
        elif isinstance(item, Genre):
            adapter = ItemAdapter(item).asdict()
            self._save_genre(adapter, spider)
            return item
        else:
            return item

    def _generate_embedding(self, text, spider):
        """Génère un embedding pour le texte donné"""
        if not self.openai_client or not text:
            return None

        try:
            text_clean = text.strip().replace('\n', ' ')
            response = self.openai_client.embeddings.create(
                input=text_clean,
                model=self.openai_settings['deployment']
            )
            return response.data[0].embedding
        except Exception as e:
            spider.logger.error(f"❌ Embedding generation error: {e}")
            return None

    def _save_book(self, adapter, spider):
        # Vérifier la connexion avant toute opération
        self._ensure_connection(spider)

        cursor = self.connection.cursor()
        # Save item in DB and replace values if it already exists
        try:
            # Check if the item already exists
            cursor.execute('SELECT id, description FROM books WHERE upc = %s', (adapter.get('upc'),))
            existing = cursor.fetchone()

            description = adapter.get('description')
            embedding = None

            if existing is None:
                # New item: generate embedding
                embedding = self._generate_embedding(description, spider) if description else None
            elif existing[1] != description:
                # Description updated: generate embedding
                embedding = self._generate_embedding(description, spider) if description else None
            else:
                # Description unchanged: keep original embedding
                pass

            if embedding is not None:
                cursor.execute('''
                    INSERT INTO books (
                        type, title, thumbnail, link, description,
                        genre, upc, availability, description_embedding
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (upc) DO UPDATE SET
                        type = EXCLUDED.type,
                        title = EXCLUDED.title,
                        thumbnail = EXCLUDED.thumbnail,
                        link = EXCLUDED.link,
                        description = EXCLUDED.description,
                        genre = EXCLUDED.genre,
                        availability = EXCLUDED.availability,
                        description_embedding = EXCLUDED.description_embedding
                    RETURNING id
                ''',
                   (adapter.get('type'),
                    adapter.get('title'),
                    adapter.get('thumbnail'),
                    adapter.get('link'),
                    description,
                    adapter.get('genre'),
                    adapter.get('upc'),
                    bool(random.getrandbits(1)),
                    embedding))
                book_id = cursor.fetchone()[0]

                cursor.execute('''
                        INSERT INTO updates (
                            book_id, rating, price, stock,
                            tax, reviews, scraped_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''',
                   (book_id,
                    max(0, min(5, int(adapter.get('rating')) + randint(-1,1))),
                    float(adapter.get('price')) + uniform(-5, 5),
                    int(adapter.get('stock')) + uniform(0, 5),
                    float(adapter.get('tax')) + uniform(0, 2),
                    int(adapter.get('reviews')) + randint(0,5),
                    adapter.get('scraped_at')))
                self.connection.commit()
            else:
                cursor.execute('''
                        INSERT INTO books (
                            type, title, thumbnail, link, description,
                            genre, upc, availability
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (upc) DO UPDATE SET
                            type = EXCLUDED.type,
                            title = EXCLUDED.title,
                            thumbnail = EXCLUDED.thumbnail,
                            link = EXCLUDED.link,
                            description = EXCLUDED.description,
                            genre = EXCLUDED.genre,
                            availability = EXCLUDED.availability
                        RETURNING id
                    ''',
                   (adapter.get('type'),
                    adapter.get('title'),
                    adapter.get('thumbnail'),
                    adapter.get('link'),
                    description,
                    adapter.get('genre'),
                    adapter.get('upc'),
                    bool(random.getrandbits(1))))
                book_id = cursor.fetchone()[0]

                cursor.execute('''
                            INSERT INTO updates (
                                book_id, rating, price, stock,
                                tax, reviews, scraped_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ''',
                   (book_id,
                    int(adapter.get('rating')) + randint(-1, 1),
                    float(adapter.get('price')) + randint(-200, 200),
                    int(adapter.get('stock')) + uniform(0, 5),
                    float(adapter.get('tax')) + uniform(0, 2),
                    int(adapter.get('reviews')) + randint(0, 5),
                    adapter.get('scraped_at')))
                self.connection.commit()

            spider.logger.info(f"✅ Persisted book: {adapter.get('title')}" + (" with embedding" if embedding else "without embedding"))

        except Exception as e:
            self.connection.rollback()
            spider.logger.error(f"❌ Book persistence error : {e}")
        finally:
            cursor.close()

    def _save_genre(self, adapter, spider):
        # Vérifier la connexion avant toute opération
        self._ensure_connection(spider)

        cursor = self.connection.cursor()
        # Save item in DB and replace values if it already exists
        try:
            cursor.execute('''
                INSERT INTO genres (
                    genre
                ) VALUES (%s)
                ON CONFLICT (genre) DO NOTHING
            ''',
               (adapter.get('genre'),))
            self.connection.commit()
            spider.logger.info(f"✅ Persisted genre: {adapter.get('genre')}")

        except Exception as e:
            self.connection.rollback()
            spider.logger.error(f"❌ Genre persistence error : {e}")
        finally:
            cursor.close()
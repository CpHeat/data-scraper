import psycopg2

from itemadapter import ItemAdapter

from data_scraper.items.book import Book
from data_scraper.items.genre import Genre


class BookPGPersistencePipeline:
    collection_name = "books"

    def __init__(self, db_settings):
        self.db_settings = db_settings
        self.connection = None

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
        return cls(db_settings)

    def open_spider(self, spider):
        # Open connection to DB
        try:
            self.connection = psycopg2.connect(**self.db_settings)
            spider.logger.info("✅ Azure PostgreSQL connected")

            # Create table if needed
            self._create_tables()

        except Exception as e:
            spider.logger.error(f"❌ Azure PostgreSQL connection error : {e}")
            raise

    def _create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                type VARCHAR(500),
                title VARCHAR(500),
                thumbnail VARCHAR(500),
                link VARCHAR(500),
                description TEXT,
                genre VARCHAR(100),
                rating INTEGER,
                price INTEGER,
                availability BOOLEAN,
                stock INTEGER,
                upc VARCHAR(100) UNIQUE,
                tax INTEGER,
                reviews INTEGER,
                scraped_at TIMESTAMPTZ
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS genres (
                id SERIAL PRIMARY KEY,
                genre VARCHAR(500) UNIQUE NOT NULL
            )
        ''')
        self.connection.commit()
        cursor.close()

    def close_spider(self, spider):
        # Close connection to DB
        if self.connection:
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

    def _save_book(self, adapter, spider):
        cursor = self.connection.cursor()
        # Save item in DB and replace values if it already exists
        try:
            cursor.execute('''
                INSERT INTO books (
                    type, title, thumbnail, link, description,
                    genre, rating, price, availability, stock,
                    upc, tax, reviews, scraped_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (upc) DO UPDATE SET
                    type = EXCLUDED.type,
                    title = EXCLUDED.title,
                    thumbnail = EXCLUDED.thumbnail,
                    link = EXCLUDED.link,
                    description = EXCLUDED.description,
                    genre = EXCLUDED.genre,
                    rating = EXCLUDED.rating,
                    price = EXCLUDED.price,
                    availability = EXCLUDED.availability,
                    stock = EXCLUDED.stock,
                    tax = EXCLUDED.tax,
                    reviews = EXCLUDED.reviews,
                    scraped_at = EXCLUDED.scraped_at
            ''',
               (adapter.get('type'),
                adapter.get('title'),
                adapter.get('thumbnail'),
                adapter.get('link'),
                adapter.get('description'),
                adapter.get('genre'),
                adapter.get('rating'),
                adapter.get('price'),
                adapter.get('availability'),
                adapter.get('stock'),
                adapter.get('upc'),
                adapter.get('tax'),
                adapter.get('reviews'),
                adapter.get('scraped_at')))
            self.connection.commit()
            spider.logger.info(f"✅ Persisted book: {adapter.get('title')}")

        except Exception as e:
            self.connection.rollback()
            spider.logger.error(f"❌ Book persistence error : {e}")
        finally:
            cursor.close()

    def _save_genre(self, adapter, spider):
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
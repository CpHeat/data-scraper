import psycopg2

from itemadapter import ItemAdapter

from data_scraper.items.quote import Quote
from data_scraper.items.author import Author


class QuotePGPersistencePipeline:
    collection_name = "quotes"

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
            CREATE TABLE IF NOT EXISTS quotes (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                author VARCHAR(200) NOT NULL,
                tags VARCHAR(500),
                scraped_at TIMESTAMPTZ,
                UNIQUE (content, author)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS authors (
                id SERIAL PRIMARY KEY,
                slug VARCHAR(100) UNIQUE,
                name VARCHAR(200),
                link VARCHAR(200)
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
        if isinstance(item, Quote):
            adapter = ItemAdapter(item).asdict()
            self._save_quote(adapter, spider)
            return item
        elif isinstance(item, Author):
            adapter = ItemAdapter(item).asdict()
            self._save_author(adapter, spider)
            return item
        else:
            return item

    def _save_quote(self, adapter, spider):
        cursor = self.connection.cursor()
        # Save item in DB and replace values if it already exists
        try:
            cursor.execute('''
                INSERT INTO quotes (
                    content, author, tags, scraped_at
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT (content, author) 
                DO UPDATE SET
                    tags = EXCLUDED.tags,
                    scraped_at = EXCLUDED.scraped_at
            ''',
               (adapter.get('content'),
                adapter.get('author'),
                adapter.get('tags'),
                adapter.get('scraped_at'),))
            self.connection.commit()
            spider.logger.info(f"✅ Persisted quote : {adapter.get('content')}")

        except Exception as e:
            self.connection.rollback()
            spider.logger.error(f"❌ Quote persistence error : {e}")
        finally:
            cursor.close()

    def _save_author(self, adapter, spider):
        cursor = self.connection.cursor()
        # Save item in DB and replace values if it already exists
        try:
            cursor.execute('''
                INSERT INTO authors (
                    slug, name, link
                ) VALUES (%s, %s, %s)
                ON CONFLICT (slug) 
                DO UPDATE SET
                    name = EXCLUDED.name,
                    link = EXCLUDED.link
            ''',
               (adapter.get('slug'),
                adapter.get('name'),
                adapter.get('link'),))
            self.connection.commit()
            spider.logger.info(f"✅ Persisted author: {adapter.get('name')}")

        except Exception as e:
            self.connection.rollback()
            spider.logger.error(f"❌ Author persistence error : {e}")
        finally:
            cursor.close()
#!/bin/bash
set -e

echo "Starting scraper at $(date)"

# Exécuter le spider books
echo "Running books spider..."
scrapy crawl books

echo "Scraping completed at $(date)"
## Immobilien Data Fetching to Flat Data Structure

This project is designed to fetch Immobilien (real estate) data from a given source (e.g., a web API or website) and convert it into a flat data structure for easier manipulation and further analysis, reporting, or storage.
The system handles data extraction, transformation, and flattening of complex hierarchical structures into a tabular format, which is ideal for integration into data warehouses, spreadsheets, or databases.

## Features
- **Data Fetching**: Fetches real estate data from multiple sources, such as APIs or web scraping.
- **Data Transformation**: Transforms complex nested JSON or XML data into a simplified flat structure.
- **Flat Data Structure**: Outputs data in a tabular format (e.g., CSV, JSON, or database-friendly format).
- **Flexible Configuration**: Easily configurable to support various real estate APIs or websites.
- **Error Handling**: Includes error handling to ensure robust data fetching, such as retries on failed requests and logging errors for debugging.

## Installation
To get started, clone this repository and install the necessary dependencies:

Python 3.10+
```bash
pip install -r script/requirements.txt
```

## Usage
Run the scraper.py script to fetch data from the source and convert it into a flat structure. This will fetch the Immobilien data, process it, and save it in the specified output format (e.g., CSV ).
```bash
http_proxy=  python script/scraper.py
```

## Visualize
[Go to the Flat Viewer URL for data](https://flatgithub.com/neverset123/ImmoFlatData)


## others
scraping discord: https://discord.com/channels/737009125862408274/774298515123208233/1331328539785429055
https://github.com/lavague-ai/LaVague
https://www.youtube.com/watch?v=QxHE4af5BQE
https://github.com/jina-ai/reader

### scrapy and playwright
use scrapy and playwright: Since cookies are assigned for the first time, use Playwright to collect them and then inject them in a Scrapy POST call
```
scrapy startproject immo
scrapy genspider quotes_pagination http://quotes.toscrape.com/scroll
scrapy crawl quotes_pagination
```

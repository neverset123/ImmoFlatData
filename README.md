## run 
http_proxy=  python scraper.py

## scrapy and playwright
use scrapy and playwright
```
scrapy startproject immo
scrapy genspider quotes_pagination http://quotes.toscrape.com/scroll
scrapy crawl quotes_pagination
```
Since these cookies are assigned when we browse the website for the first time, why don’t we use Playwright to collect them and then inject them in a Scrapy POST call?


## others
scraping discord: https://discord.com/channels/737009125862408274/774298515123208233/1331328539785429055

https://github.com/lavague-ai/LaVague
https://www.youtube.com/watch?v=QxHE4af5BQE
https://github.com/jina-ai/reader

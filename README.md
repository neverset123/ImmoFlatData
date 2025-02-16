## run 
use python310
```
http_proxy=  python script/scraper.py
```
## Visualize
Go to the Flat Viewer URL for your repository: all you need to do to go to the Flat Viewer is change the domain of your repository from “github.com” to “flatgithub.com”.

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

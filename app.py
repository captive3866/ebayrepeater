from flask import Flask, request, abort, Response
import requests
from EBayRepeater import EBayScrapers
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import re

app = Flask(__name__)

BASE_URL = "https://www.ebay.com/"

EBAY_ITEM_PAGE_BASE = "https://www.ebay.com/itm/"
ROOT_URL = "https://path/to/your/endpoint"
session = requests.session()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36"
}

proxies = {
}

@app.route('/')
def index():
    return "no data"

@app.route('/<path:path>')
def write_rss(path: str):  # put application's code here
    path_url = request.url.replace(ROOT_URL, "")
    url = BASE_URL + path_url
    try:
         data = session.get(url, timeout=5, proxies=proxies)
    except Exception as e: 
        print(e)
        abort(500)

    print(url)

    if data.status_code != 200:
        print(data.status_code)
        abort(404)

    soup = BeautifulSoup(data.text)

    title_string_container = soup.find("title")
    if title_string_container is None:
        title_string = "ebay_repeater"
    else:
        title_string = title_string_container.text
    
    fg = FeedGenerator()
    fg.id(ROOT_URL)
    fg.title(title_string)
    fg.description("ebay Routing System")
    fg.link(href=ROOT_URL)
    fg.author({'name': 'John Doe', 'email': 'john@example.de'})
    fg.language('en')

    for item in EBayScrapers.select(soup):
        fe = fg.add_entry()
        fe.id(item.ebay_id)
        fe.title(item.title)
        fe.link(href=EBAY_ITEM_PAGE_BASE + item.ebay_id)

        if item.image_url is not None:
            fe.description(item.description + '\n<img src="{0}">'.format(item.image_url))

    response = Response(fg.rss_str(), headers={"Contant-Type": "application/rdf+xml"})

    return response


if __name__ == '__main__':
    app.run(port=31401)

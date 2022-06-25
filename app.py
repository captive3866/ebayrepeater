from flask import Flask, request, abort, Response
import requests
from EBayRepeater import EBayScrapers
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import re

app = Flask(__name__)
BASE_URL = "https://www.ebay.com/"
EBAY_ITEM_PAGE_BASE = "https://www.ebay.com/itm/"

@app.route('/<path:path>')
def write_rss(path: str):  # put application's code here
    path_url = request.url.replace(request.root_url, "")
    url = BASE_URL + path_url
    data = requests.get(url)

    if data.status_code != 200:
        abort(404)

    soup = BeautifulSoup(data.text, "lxml")

    fg = FeedGenerator()
    fg.id(request.root_url)
    fg.title('eBay Router')
    fg.description("ebay Routing System")
    fg.link(href=request.root_url)
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
    app.run()

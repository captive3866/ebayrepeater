from bs4 import BeautifulSoup
import logging
import requests
from datetime import datetime
import re
from feedgen.feed import FeedGenerator
from typing import Optional
from time import sleep

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:68.0) Gecko/20100101 Firefox/68.0",
    "Accept-Language": "en-US,en;q=0.5"
}


class EBayEntry:
    EBAY_URL_BASE = "https://www.ebay.com/itm/"

    def __init__(self, title: str, ebay_id: str, image_url: str, description: str, timestamp: datetime):
        self.title = title
        self.ebay_id = ebay_id
        self.image_url = image_url
        self.description = description
        self.timestamp = timestamp

    @property
    def ebay_url(self):
        return self.EBAY_URL_BASE + self.ebay_id


class EBayScrapers:

    @classmethod
    def photo(cls, list_container: BeautifulSoup):
        items_soup = list_container.find_all("li", class_="s-item")
        if items_soup is None:
            logging.error("stopepd due to photo")

        for item_soup in items_soup:
            image_soup = item_soup.find("img", class_="s-item__image-img")

            ebay_dict = {
            }

            if image_soup is None or "src" not in image_soup.attrs:
                logging.warning("no photo skip")
                continue

            ebay_dict["image_url"] = image_soup["src"]

            title_soup = item_soup.find("div", class_="s-item__title")
            if title_soup is None:
                logging.warning("no title skip")
                continue

            ebay_dict["title"] = title_soup.text

            link_soup = item_soup.find("a")
            if link_soup is None or "href" not in link_soup.attrs:
                logging.warning("no link skip")
                continue
            # https://www.ebay.com/itm/183510989326
            ebay_id_match = re.match(r"https://www\.ebay\.[a-z0-9.]+/itm/([0-9+]+).*", link_soup["href"])
            if ebay_id_match is None:
                logging.warning("no link skip")
                continue

            ebay_dict["ebay_id"] = ebay_id_match.group(1)

            info_soup = item_soup.find("div", class_="s-item__info")
            if info_soup is None:
                logging.warning("no description")
            info_text = re.sub(r"\s+", r" ", info_soup.text)

            ebay_dict["description"] = info_text
            ebay_dict["timestamp"] = datetime.fromtimestamp(int(ebay_dict["ebay_id"]) / 1000)
            yield EBayEntry(**ebay_dict)

    @classmethod
    def normal(cls, list_container: BeautifulSoup):
        items_soup = list_container.find_all("li", class_="lvresult")
        for item_soup in items_soup:

            if "Results matching fewer words" in item_soup.text:
                logging.info("stopped due to ferwer")
                break

            image_container = item_soup.find("div", class_="lvpic")
            if image_container is None:
                logging.warning("err no good li")
                continue

            ebay_id = image_container.attrs["iid"]

            ebay_image_soup = image_container.find("img", class_="img")
            if ebay_image_soup is None or "src" not in ebay_image_soup.attrs:
                logging.warning("err no image tag")
                continue

            ebay_image_url = ebay_image_soup.attrs["src"]

            title_container = item_soup.find("h3", class_="lvtitle")
            if title_container is None:
                logging.warning("err no such title")
                continue

            link_soup = title_container.find("a")
            if link_soup is None:
                logging.warning("no title tag")

            if "data-mtdes" in link_soup.attrs:
                title_text = link_soup.attrs["data-mtdes"]
                logging.debug("from-mtdes: " + title_text)
            else:
                title_text = link_soup.text
                logging.debug("from-title text: " + title_text)

            description = ""

            detail_sub_container = item_soup.find("div", class_="lvsubtitle")
            if detail_sub_container is not None:
                new_description = re.sub(r"\s+", " ", detail_sub_container.text)
                description += new_description

            details_container = item_soup.find("ul", class_="lvprices")
            if details_container is None:
                description += "no description"
            else:
                new_description = re.sub(r"\s+", " ", details_container.text)
                description += new_description

            yield EBayEntry(title=title_text,
                                  ebay_id=ebay_id,
                                  image_url=ebay_image_url,
                                  description=description,
                                  timestamp=datetime.fromtimestamp(int(ebay_id) / 1000)
                                  )

    @classmethod
    def select(cls, soup: BeautifulSoup) -> EBayEntry:
        list_soup = soup.find("ul", id="ListViewInner")
        if list_soup is not None:
            for line in cls.normal(list_container=list_soup):
                yield line

        else:
            photo_soup = soup.find("ul", class_="srp-results")
            if photo_soup is not None:
                for line in cls.photo(list_container=photo_soup):
                    yield line
            else:
                logging.error("no list")


import bs4
import urllib
import csv
from urllib.request import urlopen
from urllib.request import urlretrieve
import os

def scrape(url):
    # Make beautiful soup object
    with urlopen(url) as url:
        html = url.read()
        soup = bs4.BeautifulSoup(html, "html.parser")
        img = soup.findAll('img')[-1]
        if img['src'].startswith("files/"):
            url = "http://spritedatabase.net/"+img['src']
            # print(url)
            if "Background" in url:
                print('bg', url)
                urlretrieve(url, "images/bg/"+os.path.basename(url))
            elif "Sprite" in url:

                urlretrieve(url, "images/sprites/"+os.path.basename(url))
                print("sprite", url)
            else:
                print("other", url)

for i in range(1000):
    scrape("http://spritedatabase.net/random")

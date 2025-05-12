import wikipedia
import sqlite3
import random
import requests
import os
from bs4 import BeautifulSoup

url = requests.get("https://en.wikipedia.org/wiki/Special:Random")
soup = BeautifulSoup(url.content, "html.parser")
title = soup.find(class_="firstHeading").text
url = "https://en.wikipedia.org/wiki/%s" % title

# Fetch summary
wikipedia.set_lang("en")
try:
    page = wikipedia.page(title)
    summary = wikipedia.summary(title, sentences=2)
    image_url = next((img for img in page.images if img.lower().endswith(('.jpg', '.jpeg', '.png'))), None)
    credit = f"Fact from Wikipedia: {page.url}"

    # Save the image
    if image_url:
        headers = {'User-Agent': 'Mozilla/5.0'}
        img_data = requests.get(image_url, headers=headers).content
        image_path = os.path.join('static', 'images', 'featured_fact.jpg')
        with open(image_path, 'wb') as handler:
            handler.write(img_data)

    # Write summary and credit to a text file
    fact_text = f"🧠 Fact of the Day:\n\n{summary}\n\n📸 {credit}"
    with open(os.path.join('static', 'featured_fact.txt'), 'w') as f:
        f.write(fact_text)

except wikipedia.exceptions.PageError:
    print(f"Page not found for topic: {title}")
    exit(1)

# Save to your database
conn = sqlite3.connect('calefamily.db')
cur = conn.cursor()

# Use a system user ID for auto-posts (e.g. 1)
user_id = 1
subcale = 'caleducation'
content = f"{summary}\n\n📸 {credit}"
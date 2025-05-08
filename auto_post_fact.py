import wikipedia
import sqlite3
import random
import requests
import os

# Choose a topic
topics = ['History for kids', 'Geography for kids', 'Science for kids']
topic = random.choice(topics)

# Fetch summary
wikipedia.set_lang("en")
try:
    page = wikipedia.page(topic)
    summary = wikipedia.summary(topic, sentences=2)
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
    fact_text = f"{summary}\n\n📸 {credit}"
    with open(os.path.join('static', 'featured_fact.txt'), 'w') as f:
        f.write(fact_text)

except wikipedia.exceptions.PageError:
    print(f"Page not found for topic: {topic}")
    exit(1)

# Save to your database
conn = sqlite3.connect('calefamily.db')
cur = conn.cursor()

# Use a system user ID for auto-posts (e.g. 1)
user_id = 1
subcale = 'caleducation'
content = f"{summary}\n\n📸 {credit}"

# cur.execute('INSERT INTO posts (user_id, subcale_name, content) VALUES (?, ?, ?)',
#             (user_id, subcale, content))

#print("Posting as user_id:", user_id)
#print("Post content:\n", content)
# Optionally: Download and store the image or link it in the content
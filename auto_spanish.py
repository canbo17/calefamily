import requests
from bs4 import BeautifulSoup
import json, re
import os, sqlite3

url = "https://www.spanishdict.com/wordoftheday"
headers = {'User-Agent': 'Mozilla/5.0'}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Find the script tag containing "window.SD_COMPONENT_DATA"
script_tag = soup.find('script', string=re.compile("window.SD_COMPONENT_DATA"))

# Extract and clean the JSON from the JS assignment
json_text = re.search(r'window\.SD_COMPONENT_DATA\s*=\s*(\{.*\});', script_tag.string).group(1)
data = json.loads(json_text)

# Extract today's word info
wotd = data['wotdList'][0]

word_es = wotd['word']                  # e.g., "el ocio"
word_en = wotd['translation']           # e.g., "leisure"
example_es = wotd['exampleSource']      # e.g., "Es importante dejar tiempo para el ocio."
example_en = wotd['exampleTranslated']  # e.g., "It is important to leave time for leisure."
image_url = wotd['imageJPG']            # JPG image

# Download the image
os.makedirs('static/images', exist_ok=True)
img_path = os.path.join('static', 'images', 'word_of_the_day.jpg')
img_data = requests.get(image_url).content
with open(img_path, 'wb') as f:
    f.write(img_data)

# Print results
with open("static/spanish.txt", "w", encoding="utf-8") as f:
    f.write(f"📌 La palabra del día\n")
    f.write(f"(Word of the Day):\n\n") 
    f.write(f"🇪🇸 Spanish     : {word_es}\n")
    f.write(f"🇺🇸 Translation : {word_en}\n\n")
    f.write("📝 Example:\n")
    f.write(f"  🇪🇸 {example_es}\n")
    f.write(f"  🇺🇸 {example_en}\n")

# Save to your database
conn = sqlite3.connect('calefamily.db')
cur = conn.cursor()

# Use a system user ID for auto-posts (e.g. 1)
credit = "https://www.spanishdict.com/wordoftheday"
user_id = 1
subcale = 'calespanol'
content = f"{word_es}\n\n📸 {credit}"
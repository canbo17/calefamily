import requests
from bs4 import BeautifulSoup
import json, re
import os, sqlite3
from googletrans import Translator
from gtts import gTTS

url = "https://www.spanishdict.com/wordoftheday"
headers = {'User-Agent': 'Mozilla/5.0'}
translator = Translator()

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
example_tr = translator.translate(example_en, src='en', dest='tr')
example_tr = example_tr.text
image_url = wotd['imageJPG']            # JPG image

# now translate to Turkish
word_tr = translator.translate(word_en, src='en', dest='tr')
word_tr = word_tr.text

# Generate audio tracks
tts_en = gTTS(text=word_en, lang='en')
tts_en.save("static/sounds/english.mp3")

tts_es = gTTS(text=word_es, lang='es')
tts_es.save("static/sounds/spanish.mp3")

tts_tr = gTTS(text=word_tr, lang='tr')
tts_tr.save("static/sounds/turkish.mp3")


# Download the image
os.makedirs('static/images', exist_ok=True)
img_path = os.path.join('static', 'images', 'word_of_the_day.jpg')
img_data = requests.get(image_url).content
with open(img_path, 'wb') as f:
    f.write(img_data)

# Print results
with open("static/spanish.txt", "w", encoding="utf-8") as f:
    f.write(f"-" * 30 + "\n")
    f.write(f"🇪🇸 La palabra del día  \n")
    f.write(f"🇺🇸 Word of the Day     \n")
    f.write(f"🇹🇷 Günün kelimesi      \n\n") 
    f.write("-" * 30 + "\n")
    # Aligned rows
    f.write(f"🇪🇸  {'Español':<10} : {word_es}\n")
    f.write(f"🇺🇸  {'English':<10} : {word_en}\n")
    f.write(f"🇹🇷  {'Türkçe':<10} : {word_tr}\n\n")
    f.write("-" * 30 + "\n")
    # Examples
    f.write("📝 Ejemplo\Example:\Örnek \n")
    f.write(f"  🇪🇸 {example_es}\n")
    f.write(f"  🇺🇸 {example_en}\n")
    f.write(f"  🇹🇷 {example_tr}\n")
 
# Save to your database
conn = sqlite3.connect('calefamily.db')
cur = conn.cursor()

# Use a system user ID for auto-posts (e.g. 1)
credit = "https://www.spanishdict.com/wordoftheday"
user_id = 1
subcale = 'calespanol'
content = f"{word_es}\n\n📸 {credit}"
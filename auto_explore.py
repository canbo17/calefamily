import requests, random, sqlite3 
import os, folium, time
from bs4 import BeautifulSoup
from selenium import webdriver
from PIL import Image
from io import BytesIO

# Find a random country
response = requests.get("https://restcountries.com/v3.1/all")
countries = response.json()
random_country = random.choice(countries)
countries = response.json()


# Safely information fields
name = random_country.get('name', {}).get('common', 'N/A')
capital = random_country.get('capital', ['N/A'])[0]
languages = ', '.join(random_country.get('languages', {}).values()) or 'N/A'
currencies = ', '.join(
    f"{v.get('name')} ({v.get('symbol')})"
    for v in random_country.get('currencies', {}).values()
) or 'N/A'
region = random_country.get('region', 'N/A')
population = f"{random_country.get('population', 0):,}"
borders = ', '.join(random_country.get('borders', [])) or 'None'
latlng = random_country.get('latlng', ['N/A', 'N/A'])
flag = random_country.get('flags', {}).get('png', 'N/A')
google_maps = random_country.get('maps', {}).get('googleMaps', 'N/A')

# Write results to a file
with open("static/explore.txt", "w", encoding="utf-8") as f:
    f.write(f"🌍 Country      : {name}\n")
    f.write(f"🏛️ Capital      : {capital}\n")
    f.write(f"🗣️ Languages    : {languages}\n")
    f.write(f"💱 Currency     : {currencies}\n")
    f.write(f"📍 Region       : {region}\n")
    f.write(f"👥 Population   : {population}\n")
    f.write(f"🌐 Borders      : {borders}\n")
    f.write(f"📌 Coordinates  : {latlng}\n")
    f.write(f"🗺️ Google Maps  : {google_maps}\n")
    #f.write(f"🚩 Flag Image URL: {flag}")


# Create map with borders as a PNG file

# Coordinates
lat, lon = latlng[0], latlng[1]
zoom = 4
output_path = "static/images/country_satellite_map.png"

# Create map
m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None)

# Add Esri satellite layer
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri', name='Esri Satellite'
).add_to(m)

# Add labels/boundaries
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
    attr='Esri', name='Boundaries & Labels'
).add_to(m)

# Save HTML
html_path = "map_temp.html"
m.save(html_path)

# Headless browser to capture PNG
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--window-size=800,600")

driver = webdriver.Chrome(options=options)
driver.get(f"file://{os.path.abspath(html_path)}")

# Wait to load
time.sleep(3)
driver.save_screenshot(output_path)
driver.quit()

# Optional: crop whitespace
img = Image.open(output_path)
cropped = img.crop(img.getbbox())
cropped.save(output_path)

# Combine map and flag
# Load map image
map_img = Image.open("static/images/country_satellite_map.png").convert("RGBA")
map_width, map_height = map_img.size

# Load flag image from URL
flag_url = flag  # your flag image URL
flag_img = Image.open(BytesIO(requests.get(flag_url).content)).convert("RGBA")

# Resize flag if it's too big (optional)
flag_size = (160, 100)
flag_img = flag_img.resize(flag_size, Image.Resampling.LANCZOS)

# Calculate top-right position
padding = 10
pos_x = map_width - flag_size[0] - padding
pos_y = padding

# Paste flag with transparency
map_img.paste(flag_img, (pos_x, pos_y), flag_img)

# Save result
output_path = "static/images/map_with_flag.png"
map_img.save(output_path)

#print(f"✅ Map saved as: {output_path}")

# Save to your database
conn = sqlite3.connect('calefamily.db')
cur = conn.cursor()

# Use a system user ID for auto-posts (e.g. 1)
credit = "https://restcountries.com/"
user_id = 1
subcale = 'calexplore'
content = f"{name}\n\n📸 {credit}"

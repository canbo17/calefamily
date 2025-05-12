import requests, random, sqlite3 
from PIL import Image, ImageDraw
from io import BytesIO

# STEP 1) : Find a random country write details into a txt file
# Find a random country 
response = requests.get("https://restcountries.com/v3.1/all")
countries = response.json()
random_country = random.choice(countries)

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
credit = "📸 Information from https://restcountries.com/"

#print(name)

# Write results to a file
with open("static/explore.txt", "w", encoding="utf-8") as f:
    f.write(f"-" * 30 + "\n")
    f.write(f"Country of the day\n")
    f.write(f"🌍 Country      : {name}\n")
    f.write(f"🏛️ Capital      : {capital}\n")
    f.write(f"🗣️ Languages    : {languages}\n")
    f.write(f"💱 Currency     : {currencies}\n")
    f.write(f"📍 Region       : {region}\n")
    f.write(f"👥 Population   : {population}\n")
    f.write(f"🌐 Borders      : {borders}\n")
    f.write(f"📌 Coordinates  : {latlng}\n")
    f.write(f"🗺️ Google Maps  : {google_maps}\n\n")
    f.write(f"{credit}")
    #f.write(f"🚩 Flag Image URL: {flag}")

# STEP 2) Create map with borders as a PNG file
# Coordinates
lat, lon = latlng[0], latlng[1]
output_path = "static/images/country_satellite_map.png"

# Bounding box (lat/lon): [minx, miny, maxx, maxy]
delta = 20  # degrees
bbox = [lon - delta, lat - delta, lon + delta, lat + delta]

# Common export params
params = {
    "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
    "bboxSR": "4326",
    "size": "800,600",
    "format": "png32",  # use png32 for transparency support
    "f": "image"
}

# Satellite image (World_Imagery)
sat_url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
sat_response = requests.get(sat_url, params=params)
sat_img = Image.open(BytesIO(sat_response.content)).convert("RGBA")
map_width, map_height = sat_img.size

# Boundaries and labels (transparent overlay)
bound_url = "https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/export"
bound_response = requests.get(bound_url, params=params)
bound_img = Image.open(BytesIO(bound_response.content)).convert("RGBA")

# Blend: boundaries on top with some transparency
bound_img.putalpha(90)  # optional: reduce opacity to 70%
composite = Image.alpha_composite(sat_img, bound_img)

# 🎨 Add pin (convert lat/lon to pixel x/y)
def geo_to_pixel(lat, lon, bbox, img_size):
    minx, miny, maxx, maxy = bbox
    x = (lon - minx) / (maxx - minx) * img_size[0]
    y = (maxy - lat) / (maxy - miny) * img_size[1]  # y-axis is top-down
    return int(x), int(y)

draw = ImageDraw.Draw(composite)
# 📐 Image size
width, height = 800, 600
pin_x, pin_y = geo_to_pixel(lat, lon, bbox, (width, height))

# Draw a red circle pin
pin_radius = 8
draw.ellipse(
    [(pin_x - pin_radius, pin_y - pin_radius), (pin_x + pin_radius, pin_y + pin_radius)],
    fill=(255, 0, 0, 255),
    outline=(255, 255, 255, 255),
    width=2
)

# Save result
composite.save(output_path)
#print(f"✅ Map with labels saved to {output_path}")

# Combine map flag with the map
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
user_id = 1
subcale = 'calexplore'
content = f"{name}\n\n📸 {credit}"
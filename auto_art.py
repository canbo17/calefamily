import requests
import random, os

# Step 1: Get all object IDs
ids = requests.get("https://collectionapi.metmuseum.org/public/collection/v1/objects").json()["objectIDs"]
random_id = random.choice(ids)

# Step 2: Fetch a random object
art = requests.get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{random_id}").json()

# Step 3: Extract and print info
print(f"🎨 Title: {art['title']}")
print(f"👤 Artist: {art['artistDisplayName'] or 'Unknown'}")
print(f"🗓️ Date: {art['objectDate']}")
print(f"🖼️ Image URL: {art['primaryImage'] or 'No image available'}")

# Create txt
credit = "📸 Information from https://collectionapi.metmuseum.org"
summary = f"{art['title']} is a {art['objectName']} from the {art['culture']} culture, created around {art['objectDate']}. It is part of the {art['department']} collection at the Met. The piece is classified as {art['classification']} and was made using {art['medium']}."
with open("static/art.txt", "w", encoding="utf-8") as f:
    f.write(f"-" * 30 + "\n")
    f.write(f"Art of the day\n")
    f.write(f"🎨 Title : {art['title']}\n")
    f.write(f"👤 Artist: {art['artistDisplayName'] or 'Unknown'}\n")
    f.write(f"🗓️ Date  : {art['objectDate']}\n")
    f.write(f"Summary  : {summary}\n\n")
    f.write(f"{credit}")

# Download the image
os.makedirs('static/images', exist_ok=True)
img_path = os.path.join('static', 'images', 'art_of_the_day.jpg')
image_url = art['primaryImage']
img_data = requests.get(image_url).content
with open(img_path, 'wb') as f:
    f.write(img_data)    
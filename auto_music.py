import requests
import random, os

base_url = "https://musicbrainz.org/ws/2/release-group/"
headers = {
    "User-Agent": "CaleFamilyApp/1.0 (you@example.com)"  # Required!
}
params = {
    "fmt": "json",
    "limit": 1,
    "query": "type:album"
}

# Initial request to get total
initial = requests.get(base_url, params=params, headers=headers).json()
total = initial.get('count', 0)

if total == 0:
    print("No albums found or API blocked.")
    print(initial)
    exit()

# Pick a valid offset
album = None
while not album:
    offset = random.randint(0, total - 1)
    params['offset'] = offset
    response = requests.get(base_url, params=params, headers=headers).json()
    album_list = response.get('release-groups', [])
    if album_list:
        album = album_list[0]
        release_id = album['releases'][0]['id']
        cover_url = f"https://coverartarchive.org/release/{release_id}/front"

# Artist info
title = album['title']
artist_id = album['artist-credit'][0]['artist']['id']
artist_data = requests.get(f'https://musicbrainz.org/ws/2/artist/{artist_id}?fmt=json', headers=headers).json()
artist_name = artist_data['name']

# Release year
release_year = album.get('first-release-date', 'Unknown')

# Genre (tags)
tags = album.get('tags', [])
genres = ', '.join(tag['name'] for tag in tags) if tags else 'Unknown'

# Other albums by artist
artist_albums_url = f"https://musicbrainz.org/ws/2/release-group?artist={artist_id}&type=album&fmt=json&limit=5"
other_albums_data = requests.get(artist_albums_url, headers=headers).json()
other_albums = [rg['title'] for rg in other_albums_data.get('release-groups', []) if rg['title'] != title]

# Display
# print(f"💿 Album: {title}")
# print(f"👤 Artist: {artist_name}")
# print(f"📅 Year: {release_year}")
# print(f"🎼 Genre: {genres}")
# print(f"🖼️ Cover Art: {cover_url}")
# if other_albums:
#     print("🎵 Other albums by this artist:")
#     for album_title in other_albums:
#         print(f"   - {album_title}")

credit = "📸 Information from https://musicbrainz.org"
with open("static/music.txt", "w", encoding="utf-8") as f:
    f.write(f"-" * 30 + "\n")
    f.write(f"Music of the Day\n")
    f.write(f"💿 Album     : {title}\n")
    f.write(f"👤 Artist    : {artist_name}\n")
    f.write(f"📅 Year      : {release_year}\n")
    f.write(f"🎼 Genre     : {genres}\n")
    if other_albums:
        f.write("🎵 Other albums by this artist:\n")
        for album_title in other_albums:
            f.write(f"   - {album_title}\n")
    f.write(" \n")            
    f.write(f"{credit}")

# Download the image
os.makedirs('static/images', exist_ok=True)
img_path = os.path.join('static', 'images', 'music_of_the_day.jpg')
image_url = cover_url
img_data = requests.get(image_url).content
with open(img_path, 'wb') as f:
    f.write(img_data)
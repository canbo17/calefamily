import random
from imdb import IMDb
import requests
import os 

genres = ['Documentary', 'History', 'Family',
          'Fantasy', 'Mystery', 'Romance', 
          'Sci-Fi','Thriller', 'Western']

movie_names = []
with open('movie_list.txt', 'r') as file:
    for line in file:
        parts = line.strip().split(',')  # comma-separated
        for entry in parts[:]:  # skip the index
            if '(' in entry:
                name = entry.rsplit('(', 1)[0].strip()
                movie_names.append(name)

random_number = random.randint(1,len(movie_names))
selected_movie = movie_names[random_number]
print("Chosen Movie : ", selected_movie)

ia = IMDb()
movie = ia.search_movie(str(selected_movie))
full_info = ia.get_movie(movie[0].movieID)

print(f"Title: {full_info['title']}")
print(f"Year: {full_info.get('year')}")
print(f"Genres: {', '.join(full_info.get('genres', []))}")
print(f"Plot: {full_info.get('plot')[0]}")
print(f"Directors: {', '.join([d['name'] for d in full_info.get('directors', [])])}")
print(f"Cover URL: {full_info.get('cover url')}")

page_url = f"https://www.imdb.com/title/tt{movie[0].movieID}/"
credit = f"Movie details are from IMDB: {page_url}"
print(credit)
poster_url = full_info.get('cover url')
plot = full_info.get('plot')[0]


movie_plot = f"{plot}\n\n🎬 {credit}"
with open(os.path.join('static', 'movie_plot.txt'), 'w') as f:
    f.write(movie_plot)

if poster_url:
    headers = {'User-Agent': 'Mozilla/5.0'}
    img_data = requests.get(poster_url, headers=headers).content
    image_path = os.path.join('static', 'images', 'movie_of_the_day.jpg')
    with open(image_path, 'wb') as handler:
        handler.write(img_data)

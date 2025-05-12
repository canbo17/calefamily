import random
from imdb import IMDb
import requests
import os 

# genres = ['Documentary', 'History', 'Family',
#           'Fantasy', 'Mystery', 'Romance', 
#           'Sci-Fi','Thriller', 'Western']

movie_names = []
with open('movie_list.txt', 'r') as file:
    for line in file:
        name = line.strip()
        if name:
            movie_names.append(name)

print(len(movie_names))

random_number = random.randint(1,len(movie_names))
print(random_number)
selected_movie = movie_names[random_number]
print("Chosen Movie : ", selected_movie)

ia = IMDb()
movie = ia.search_movie(str(selected_movie))
full_info = ia.get_movie(movie[0].movieID)

page_url = f"https://www.imdb.com/title/tt{movie[0].movieID}/"
credit = f"Movie details are from IMDB: {page_url}"
print(credit)
poster_url = full_info.get('cover url')
plot = full_info.get('plot')[0]
print(poster_url)
poster_url = poster_url.split('._V1_')[0] + '._V1_.jpg'
print(poster_url)

# update poster URL
#imdb_id = "tt0111161"
#poster_url = f"https://m.media-amazon.com/images/M/{movieID}.jpg"

movie_plot = f"{plot}\n\n🎬 {credit}"
with open(os.path.join('static', 'movie_plot.txt'), 'w') as f:
    f.write(f"-" * 30 + "\n")
    f.write(f"Movie of the day\n")
    f.write(f"Title: {full_info['title']}\n")
    f.write(f"Year: {full_info.get('year')}\n")
    f.write(f"Genres: {', '.join(full_info.get('genres', []))}\n")
    f.write(f"Plot: {full_info.get('plot')[0]}\n")
    f.write(f"Directors: {', '.join([d['name'] for d in full_info.get('directors', [])])}\n")
    f.write(f"Plot: {movie_plot}")

if poster_url:
    headers = {'User-Agent': 'Mozilla/5.0'}
    img_data = requests.get(poster_url, headers=headers).content
    image_path = os.path.join('static', 'images', 'movie_of_the_day.jpg')
    with open(image_path, 'wb') as handler:
        handler.write(img_data)

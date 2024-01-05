from bs4 import BeautifulSoup
import requests
import mysql.connector

conn = mysql.connector.connect(host='localhost', username='root', database='kiddoread')
my_cursor = conn.cursor()

conn.commit()

url = f'https://freekidsbooks.org/reading-level/children/'
r = requests.get(url).text
soup = BeautifulSoup(r, 'html.parser')
item = soup.find_all('div', class_='wrapper cleafix')

for i in item:
    page_text = i.find_all('div', class_='post-nav')
    for p in page_text:
        last_page = p.find('li', class_='next')
        last_page_link = last_page.find('a').get('href')
        last_page_num = int(last_page_link[54:-1])

urls = []
for page in range(1, last_page_num + 1):
    link = f"https://freekidsbooks.org/reading-level/children/page/{page}/"
    page = requests.get(url).text
    doc = BeautifulSoup(page, "html.parser")
    urls.append(link)

count = 1
for u in urls:
    print(u)
    response = requests.get(u)
    soup = BeautifulSoup(response.text, 'html.parser')
    book = soup.find_all('div', class_='col-xs-12 col-sm-12 col-md-12 left-side')
    for b in book:
        image = b.find('img').get('data-src')
        title = b.find('h2').text
        author = b.find('p', class_='author').text
        desc = b.find('div', class_='book_description_middle')
        description = desc.find_all('p')[1].text
        genre = b.find('p', class_="age_group").find_all('a')
        genre_list = [c.text.strip() for c in genre]
        download = b.find('a', class_='download-book my-post-like').get('href')
        print('%s) Title: %s , Author: %s, Link: %s, Image: %s, Description: %s, Genre: %s' % (
            count, title, author, download, image, description, genre_list))

        # Convert genre_list to a string representation
        genre_str = ', '.join(genre_list)

        # Save data to MySQL
        sql = "INSERT INTO books (image, title, author, description, download, genre) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (image, title, author, description, download, genre_str)
        my_cursor.execute(sql, values)
        conn.commit()

        count = count + 1

conn.close()
print('Connection successfully closed!')

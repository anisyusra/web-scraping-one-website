from bs4 import BeautifulSoup
import requests
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask

app = Flask(__name__)

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

@app.route('/')
def scrape_and_store():
    url = f"https://www.pdfdrive.com/"
    page = requests.get(url).text
    doc = BeautifulSoup(page, "html.parser")
    item = doc.find_all('div', class_='dialog')

    links = []
    aLink = []
    bLinks = []
    page_dict = {}
    count = 1

    for i in item:
        category_list = i.find_all('div', id='categories')
        for c in category_list:
            category = c.find_all('a')
            for c in category:
                cateLink = c.get('href')
                link = "https://www.pdfdrive.com"+cateLink
                links.append(link)

    for l in links:
        response = requests.get(l)
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.find(class_='Zebra_Pagination').ul
        total_pages = str(page_text).split("li")[-2].split(">")[-2][:-3]
        if total_pages.isdigit():
            pages = int(str(page_text).split("li")[-2].split(">")[-2][:-3])
        else:
            pages = int(str(page_text).split("li")[-4].split(">")[-2][:-3])
        page_dict[l] = pages

    urls = []
    for links, page in page_dict.items():
        for p in range(1, pages + 1):
            link = links+f"/p{p}/"
            urls.append(link)

    for i in urls:
        response = requests.get(i)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', class_='col-sm')
        for i in items: 
            author_link = i.find('div', class_='file-left').a
            bookAuthor = author_link.get('href')
            urlss = "https://www.pdfdrive.com" + bookAuthor  
            aLink.append(urlss)

    for a in aLink:
        if count > 20:
            break
        response = requests.get(a)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', class_='ebook-main')
        for i in items:
            categoryName = i.find_all('div', class_ = 'ebook-tags')
            for c in categoryName:
                categories = c.find_all('a')
                for a in categories:
                    genre_list = [a.text for a in categories]
            title = i.find('h1', class_ = 'ebook-title').text
            info = i.find_all('span', class_='info-green')
            years = str(info[1].text)
            if years.isdigit():
                year = info[1].text
            else:
                year = info[0].text
            image = i.find('img', class_ = 'ebook-img').get('src')
            bookLink = i.find('a', id = 'download-button-link').get('href')
            authors = i.find('div', class_= 'ebook-author').span
            page = str(info[0].text)
            if authors is not None:
                author = authors.text
            else:
                author = "No author available"
            id = db.collection('Ebook').document()
            data = {
                    'id': id.id,
                    'title': title,
                    'year': year,
                    'author': author,
                    'link': 'https://www.pdfdrive.com'+bookLink,
                    'image': image,
                    'page': page,
                    'description': "No descripttion available",
                    'genres': genre_list
                }
            db.collection('eBook').document(id.id).set(data)
            print('%s) Title: %s , Year: %s, Author: %s, Link: https://www.pdfdrive.com%s, Image: %s, Page: %s Category: %s' % (count, title, year, author, bookLink, image, page, genre_list))
            count = count + 1

    return "Scraped Successful"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
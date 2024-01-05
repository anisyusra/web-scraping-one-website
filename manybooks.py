from bs4 import BeautifulSoup
import requests
import re
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/')
def scrape_and_store():
    url = f'https://manybooks.net/categories'
    r = requests.get(url).text
    soup = BeautifulSoup(r, 'html.parser')
    item = soup.find_all('div', class_ = 'clearfix bs-genres-list')

    urls = []
    catslink = []
    page_number = {}
    linkBook = []
    nextLinks = []
    ids = 1
    count = 0
    links = 0
    cates = []

    for i in item:
        category = i.find_all('div', class_ = 'views-row')
        for c in category:
            cates = c.find_all('a')
            for l in cates:
                catlink = l.get('href')
                catslink = f"https://manybooks.net"+catlink
                page = requests.get(url).text
                doc = BeautifulSoup(page, "html.parser")
                urls.append(catslink)

    for u in urls:
        response = requests.get(u)
        soup = BeautifulSoup(response.text, 'lxml')
        pages = soup.find_all('nav', class_ = 'pager-nav text-center')
        for p in pages:
            lpage = p.find_all('li', class_ = 'pager__item pager__item--last')
            for l in lpage:
                lastPage = l.find('a')['href']
                totalPages = re.search(r'page=(\d+)', lastPage).group(1)
                page = int(totalPages)
                page_number[u] = page
        
    for urls, page in page_number.items():
        if ids <= 20:
            for p in range(0, page+1):
                linkBook.append(urls+f"?language=All&sort_by=field_downloads&page={p}")
                ids = ids + 1
        else:
            break

    for k in linkBook:
        response = requests.get(k)
        soup = BeautifulSoup(response.text, 'lxml')
        items = soup.find_all('div', class_='view-content')
        for i in items:
            titleDiv = soup.select('.col-xs-4.col-sm-4.col-md-4.col-lg-3.views-row')
            for t in titleDiv:
                titleLink = t.find_all('div', class_ = 'content')
                for b in titleLink:
                    if links <= 20:
                        nextLink = b.find('div',class_ = 'field field--name-field-title field--type-string field--label-hidden field--item').a
                        link = nextLink.get('href')
                        links = links + 1
                        nextLinks.append(f"https://manybooks.net"+link)                        
                    else:
                        break
        
    l=[]
    for n in nextLinks:
        print(n)
        response = requests.get(n)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', class_='bs-region--top')
        for i in items:
            image = i.find('div', class_= 'field field--name-field-cover field--type-image field--label-hidden field--item')
            img = image.find('img').get('src')
            year = i.find('div', class_ = 'field field--name-field-published-year field--type-integer field--label-hidden field--item').text
            pa = i.find('div', class_ = 'field field--name-field-pages field--type-integer field--label-hidden field--item')
            if pa is not None:
                pages = pa.text
            else:
                pages = "None"
            title = i.find('div', class_ = 'field field--name-field-title field--type-string field--label-hidden field--item').text
            author = i.find('div', class_ = 'field field--name-field-author-er field--type-entity-reference field--label-hidden field--items').a.text
            desc = i.find('div', class_ = 'field field--name-field-description field--type-string-long field--label-hidden field--item')
            if desc is not None:
                description = desc.text
            else:
                description = "None"
            downloadLink = n
            print(downloadLink)
            categories = i.find('div', class_='field--name-field-genre').find_all('div', class_='field--item')
            genre_list = [c.text.strip() for c in categories]
            id = db.collection('Ebook').document()
            data = {
                'id': id.id,
                'title': title,
                'year': year,
                'author': author,
                'link': downloadLink,
                'image': 'https://manybooks.net/'+img,
                'page': pages,
                'description': description,
                'genres': genre_list
            }
            db.collection('eBook').document(id.id).set(data)
            count = count + 1
            print(title)

    return "Scraped Successful"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
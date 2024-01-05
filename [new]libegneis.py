import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import re
from flask import Flask

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/')
def scrape_and_store():
    url = f'https://libgen.is/'
    r = requests.get(url).text
    soup = BeautifulSoup(r, 'html.parser')
    item = soup.find_all('ul', id = 'menu')

    category_link = []
    page_dict = {}
    page_link = []
    colors = "#C0C0C0"
    all_book_link = []

    for i in item:
        link_text = i.find_all('ul', class_ = 'greybox')
        for l in link_text:
            all_category = l.find_all('a', class_ = 'drop')
            for a in all_category:
                category = a.get('href')
                category_name = a.text
                link = f"https://libgen.is/"+category+"&res=100"
                category_link.append(link)

    for c in category_link:
        response = requests.get(c)
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script')
        for script in scripts:
            match = re.search(r'(\d+), // общее', str(script))
            if match:
                total_pages = int(match.group(1))
                page_dict[c] = total_pages
                break

    page_count = 0
    for category_link, page in page_dict.items():
        if page_count < 20:
            for p in range(1, page+1):
                link = category_link+f"&sort=def&sortmode=ASC&page={p}"
                page_link.append(link)
                page_count = page_count + 1
        else:
            break

    link_count = 0
    for p in page_link:
        response = requests.get(p)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('table', class_ = 'c')
        for i in items:
            table_text = i.find_all('tr')
            for t in table_text:
                bgcolors = t['bgcolor']
                if bgcolors != colors:
                    table = t.find_all('td')
                    book_link = table[2].find('a').get('href')
                    if 'book/index' in book_link:
                        if (link_count < 20):
                            all_book_link.append(f"https://libgen.is/"+book_link)
                            link_count = link_count + 1
                        else:
                            break

    count = 1
    title = {}
    author = {}
    pages = {}
    year = {}
    description = {}
    downloadLink = {}
    image = {}

    for a in all_book_link:
        response = requests.get(a)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('table')
        for i in items:
            table = i.find_all('tr', valign="top")
            if len(table) > 1:
                year_text = table[5].find_all('td')
                year = year_text[1].text
                pages_text = table[6].find_all('td')
                pages = pages_text[3].text.split("\\")
            else:
                None
            for t in table:            
                image_text = t.find('td', rowspan = '22')
                if image_text is not None:
                    image = image_text.find('img').get('src')
                title_text = t.find('td', colspan = '2')
                if title_text is not None:            
                    title = title_text.find('a').text
                else:
                    None
                author_text = t.find('td', colspan = '3')
                if author_text is not None:            
                    authors = author_text.find('b')
                    if authors is None:
                        None
                    else:
                        author = authors.text
                description_text = t.find('td', colspan = '4', style='padding: 25px')
                if description_text is not None:            
                    description = description_text.text
                else:
                    description = "No description available"
                downloadLink_text = t.find('td', width="17%")
                if downloadLink_text is not None:            
                    downloadLink = downloadLink_text.find('a').get('href')
                else:
                    None
                
                # Save the data in the 'Books' collection
                id = db.collection('Ebook').document()
                data = {
                    'id': id.id,
                    'title': title,
                    'year': year,
                    'author': author,
                    'link': downloadLink,
                    'image': f"https://libgen.is{image}",
                    'page': pages[0].strip("[]'").split(',')[1].strip(),
                    'description': description,
                    'genres': category_name
                }
                db.collection('eBook').document(id.id).set(data)
                print(' %s), Title: %s , Year: %s, Author: %s, Link: %s, Image: https://libgen.is%s, Page: %s ' % (count, title, year, author, downloadLink, image, pages))
                count = count + 1

    return "Scraped Successful"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from flask import Flask, jsonify, request, redirect, render_template ,Blueprint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine ,func,desc
from models import Source,SourcePage,ScrapedPerson
import re

app = Flask(__name__)

scrap_app = Blueprint('scrap', __name__)

engine = create_engine('sqlite:///savior.db', echo=True)
Session = sessionmaker(bind=engine)

# create a session
session = Session()

@scrap_app.route('/scraper')
def scrap_img():
    pages = session.query(SourcePage).filter_by(scraped=False).all()
    if not pages:
       return jsonify("No more pages to scrape.")

    for page in pages:
        url = page.url
        for i in range(1, page.max_page_numbers):
          try:
             source_page = re.sub(r'max_page_numbers', str(i), url)
             print(source_page)
             htmldata = requests.get(source_page).text
             soup = BeautifulSoup(htmldata, 'html.parser')
             items = soup.find_all('div', class_='slid_img')
             for item in items:
                name = item.h1.text
                image = "https://atfalmafkoda.com" + item.img["src"]
                date = item.p.text

                scraped_person = ScrapedPerson(name=name, image=image, date=date, type=page.type, source=page.source)
                session.add(scraped_person)
          except Exception as e:
            print(f"An error occurred for page {i}: {str(e)}")
            continue
        page.scraped=True
        session.commit()
    return jsonify("Done!")

@scrap_app.route('/api/scrapedpersons', methods=['GET'])
def get_scraped_persons():
    scraped_persons = session.query(ScrapedPerson).order_by(func.random()).limit(200).all()
    result = []
    for scraped_person in scraped_persons:
        result.append({
            'name': scraped_person.name,
            'image': scraped_person.image,
            'date': scraped_person.date,
            'type': scraped_person.type,
            'source':scraped_person.source.name
        })

    return jsonify(result)


@scrap_app.route('/scraping')
def show_scraped_persons():
    # Fetch 200 random scraped persons from the database
    scraped_persons = session.query(ScrapedPerson).order_by(func.random()).limit(200).all()

    # Count the total number of ScrapedPerson records
    scraped_person_count = session.query(ScrapedPerson).count()

    return render_template('scraped_persons.html', scraped_persons=scraped_persons, scraped_person_count=scraped_person_count)


@scrap_app.route('/add_source', methods=['GET', 'POST'])
def add_source():
    if request.method == 'POST':
        name = request.form['name']
        url = request.form['url']

        # Create a new Source instance and add it to the database
        new_source = Source(name=name, url=url)
        session.add(new_source)
        session.commit()

        return redirect('/source/{}'.format(new_source.id))

    return render_template('/add_source.html')

@scrap_app.route('/source/<int:source_id>/add_page', methods=['GET', 'POST'])
def add_page(source_id):
    if request.method == 'POST':
        name = request.form['name']
        url = request.form['url']
        selectors = request.form['selectors']
        type=request.form['type']
        max_page_numbers=request.form['max_page_numbers']
        # Retrieve the Source object based on source_id
        source = session.query(Source).get(source_id)
        # Create a new SourcePage instance and add it to the database
        new_page = SourcePage(name=name, url=url, selectors=selectors,type=type,max_page_numbers=max_page_numbers, source=source)
        session.add(new_page)
        session.commit()

        return redirect('/source/{}'.format(source_id))

    return render_template('add_page.html', source_id=source_id)

@scrap_app.route('/source/<int:source_id>', methods=['GET'])
def source(source_id):
    source = session.query(Source).get(source_id)
    # pages = source.pages
    pages=source.pages
    return render_template('source.html', source=source, pages=pages)

@scrap_app.route('/source_page/<int:page_id>', methods=['DELETE'])
def delete_source_page(page_id):
    page = session.query(SourcePage).get(page_id)

    if not page:
        return jsonify({'message': 'Source page not found'}), 404

    session.delete(page)
    session.commit()
    session.close()  # Close the session

    return jsonify({'message': 'Source page deleted successfully'})

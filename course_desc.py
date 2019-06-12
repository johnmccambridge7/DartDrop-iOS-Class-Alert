import requests
import urllib
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from lxml import html
from lxml.etree import tostring

USERNAME = "john.l.macdonald.22@dartmouth.edu"
PASSWORD = "Unity2013"

LOGIN_URL = "https://www.layuplist.com/accounts/login/"
URL = "https://www.layuplist.com/best?page="
SERVICE_KEY = "service_key.json"

def main():
    cred = credentials.Certificate(SERVICE_KEY)
    firebase_admin.initialize_app(cred)

    db = firestore.client()

    session_requests = requests.session()

    # Get login csrf token
    result = session_requests.get(LOGIN_URL)
    tree = html.fromstring(result.text)
    authenticity_token = list(set(tree.xpath("//input[@name='csrfmiddlewaretoken']/@value")))[0]
    
    total_reviews = 0
    review_rankings = {}

    # Create payload
    payload = {
        "email": USERNAME, 
        "password": PASSWORD, 
        "csrfmiddlewaretoken": authenticity_token
    }

    # Perform login
    result = session_requests.post(LOGIN_URL, data = payload, headers = dict(referer = LOGIN_URL))
    addresses = []
    # Obtain all the course data

    for i in range(1,44):

        # Scrape url
        result = session_requests.get(URL + str(i), headers = dict(referer = URL))
        tree = html.fromstring(result.content)

        print("Fetching partition: " + str(i) + "/44")

        for link in tree.xpath("//a[starts-with(@href, '/course/')]"):
            address = link.get("href")

            if address not in addresses:
                addresses.append(address)

    # For each course get the list of professors that teach the course

    for address in addresses:
        # address for each course
        url = "https://www.layuplist.com" + address

        result = session_requests.get(url, headers = dict(referer = URL))
        tree = html.fromstring(result.content)

        num_reviews = 0

        print("Gathering data from: " + address)

        if address not in review_rankings:
            review_rankings[address] = dict()

        div_column = "//div[@class='col-md-12']"
        course_name = tree.xpath("//title/text()")[0].split("|")[0].strip()
        description = ""

        for desc in tree.xpath(div_column + "//p/text()"):
            desc = desc.strip()
            if(len(desc) > 100):
                description = desc
                break
            else:
                description = "Description not available for " + course_name + "."
                break

        description.replace("Please choose from the suggestions if you can.", "Description not available for " + course_name + ".")
        description.replace("said it was good", "Description not available for " + course_name + ".")
        description.replace("called it a layup", "Description not available for " + course_name + ".")
        description.replace("Crosslisted with", "Description not available for " + course_name + ".")

        #print(course_name + "\n")
        #print(description + "\n")
        #print("\n")

        doc_ref = db.collection(u'class_desc').document(course_name)
        
        doc_ref.set({
            u'desc': description
        })

        print("Inserting: " + str(course_name))

if __name__ == '__main__':
    main()
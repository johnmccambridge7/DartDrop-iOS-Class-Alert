# gather all the required textbooks from the output.json file
import requests
import urllib
import time
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from lxml import html
from lxml.etree import tostring
URL = "https://oracle-www.dartmouth.edu/dart/groucho/course_desc.display_non_fys_req_mat?p_term=DATE&p_crn=CODE"

JSON_FILE = "courses/output.json"
SERVICE_KEY = "service_key.json"

json_file = open(JSON_FILE, "r")
json = json.load(json_file)

cred = credentials.Certificate(SERVICE_KEY)
firebase_admin.initialize_app(cred)

db = firestore.client()

for course_id in json:
    class_data = json[course_id]
    term = class_data["Term"]
    crn = class_data["CRN"]
    class_name = str(class_data["Subj"]) + str(class_data["Num"])
    session_requests = requests.session()

    textbook_url = URL.replace("DATE", term).replace("CODE", crn)
    result = session_requests.get(textbook_url, headers = dict(referer = textbook_url))
    tree = html.fromstring(result.content)

    t = ""

    for textbook in tree.xpath("//center//p/text()"):
        textbook_data = textbook.strip().replace("\n", "")
        
        if t == "":
            t = textbook_data
        else:
            t += "\n"
            t += textbook_data

    print("Inserting textbook data for: " + class_name)

    doc_ref = db.collection(u'textbooks').document(class_name)
        
    doc_ref.set({
        u'textbook': t
    })
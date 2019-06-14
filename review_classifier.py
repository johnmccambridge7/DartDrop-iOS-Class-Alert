import time
import requests
import json
import re
import math
import hashlib
import urllib
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from lxml import html
from lxml.etree import tostring

API_KEY = "AIzaSyDQajRqj-uuVvUzXpw4ZAAjp0VoqGF0_uU"

# FILE_NAME = "cormen.txt"
# FILE_RATINGS_NAME = "review_data/PRODUCTION_reviews_rating.txt"
# FILE_RAW_NAME = "reviews_rating_raw_cor.txt"

USERNAME = "john.l.macdonald.22@dartmouth.edu"
PASSWORD = "Unity2013"

LOGIN_URL = "https://www.layuplist.com/accounts/login/"
URL = "https://www.layuplist.com/best?page="

FILE_NAME = "professor_reviews_full.txt"
FILE_RATINGS_NAME = "ACTUAL_professor_review_ratings.txt"
FILE_NORMALIZED_NAME = "FALL_professor_review_ratings.txt"
FILE_RAW_NAME = "RAW_professor_review_ratings.txt"

# fix the course ID issue in the file
# number of reviews not updated
# consider sigmoid of the differnce as the rating

def sigmoid(x, scale):
  return 100 / (1 + math.exp(-(scale * x)))

# will determine if a sentence is relative to a professor
# check for prof and professor, pronouns, and the name of the professor
def relative_to_professor(prof, sentence):
    pronouns = ['he', 'she', 'him', 'her']
    titles = ['prof', 'professor']
    regex = re.compile('[^a-zA-Z]')

    prof = prof.lower()
    prof = regex.sub(" ", prof)
    professor = prof.split(" ")

    # normalize text
    sentence = sentence.lower()
    sentence = regex.sub(" ", sentence)
    sentence = sentence.split(" ")

    # check if the sentence contains pronouns
    for pronoun in pronouns:
        if pronoun in sentence:
            # print("* Pronoun Detected! *\n");
            return True
    
    # check if the sentence makes reference to a professor

    for title in titles:
        if title in sentence:
            # print("* Title Detected! *\n");
            return True
    
    # check if the professors name is mentioned

    for prof_name in professor:
        if len(prof_name) > 2:
            if prof_name in sentence:
                # print("* Professor Name Detected! * \n")
                return True

    return False

# Analyses tone of the provided review and returns the quantifed
# anger vs joy tuple
def analyze_tone(prof, text):
    data = {}
    data["document"] = {"type": "PLAIN_TEXT", "content": text}
    data["encodingType"] = "UTF8";

    formatted_json = json.dumps(data)
    # print(formatted_json)

    headers = { 'Content-Type': 'application/json', }

    params = ( ('key', API_KEY), )

    data = formatted_json
    response = requests.post('https://language.googleapis.com/v1/documents:analyzeSentiment', headers=headers, params=params, data=data)

    scores = json.loads(response.content)

    # too many requests or out of money lol
    if "sentences" not in scores:
        print(response.content)
        return False

    sentences = scores["sentences"]

    anger = 0
    joy = 0
    number_of_items = 1
    
    for sentence in sentences:
        text = sentence["text"]["content"]
        score = sentence["sentiment"]["score"]
    
        if score < 0:
            # this is an angry sentence
            score = abs(score) # get the magnitude

            if relative_to_professor(prof, text):
                anger += ((score * 10)**2) / 10 # anger factor squares for comment relative to professor
            else:
                anger += (score) / 5 # anger factor which is not relative is diluted
        elif score > 0:
            if relative_to_professor(prof, text):
                joy += ((score * 10)**2) / 10 # joy factor squares for comment relative to professor
            else:
                joy += (score) / 5 # joy factor which is not relative is diluted

        number_of_items += 1

    return (anger, joy, number_of_items)

# data-structure:
    # course-id: prof -> [angry rating, joy rating, number of reviews]

def generate_analysis():
    professor_reviews = open(FILE_NAME, "r").read().split("@")
    
    reviews = {}
    review_file = open(FILE_RATINGS_NAME, "w")
    review_file_raw = open(FILE_RAW_NAME, "w")
    start_time = time.time()

    i = 0
    for data in professor_reviews:
        review_data = data.split("\n")
        
        if len(review_data) == 5:
            
            professor = review_data[1]
            course_id = review_data[2]
            review = review_data[3]

            anger_rating = 0
            joy_rating = 0

            if course_id not in reviews.keys():
                reviews[course_id] = {}

            if professor not in reviews[course_id].keys():
                reviews[course_id][professor] = [0, 0, 0]

            # perform nlp on the review here
            anger_rating, joy_rating, review_no = analyze_tone(professor, review)

            review_file_raw.write(professor + "\n")
            review_file_raw.write(course_id + "\n")
            review_file_raw.write("Review #" + str(i) + "\n")
            review_file_raw.write("Anger: " + str(anger_rating) + "\n")
            review_file_raw.write("Joy: " + str(joy_rating) + "\n")
            review_file_raw.write("Normalization: " + str(review_no) + "\n")

            print(professor + "\n")
            print(course_id + "\n")
            print("Review #" + str(i) + "\n")
            print("Anger: " + str(anger_rating) + "\n")
            print("Joy: " + str(joy_rating) + "\n")
            print("Normalization: " + str(review_no) + "\n")
            print("\t\n")
            print("Time Elasped Since Start: " + str(time.time() - start_time) + " seconds")

            reviews[course_id][professor][0] += anger_rating
            reviews[course_id][professor][1] += joy_rating
            reviews[course_id][professor][2] += review_no
            
            i += 1

    for course in reviews.keys():
        professors = reviews[course]
        for professor in professors.keys():
            scores = reviews[course][professor]
            review_file.write(professor + "\n")
            review_file.write(course + "\n")
            review_file.write(str(scores[0]) + "\n")
            review_file.write(str(scores[1]) + "\n")
            review_file.write(str(scores[2]) + "\n")
            review_file.write("@\n")

def normalize(review_file, output_file):
    SERVICE_KEY = "service_key.json"

    cred = credentials.Certificate(SERVICE_KEY)
    firebase_admin.initialize_app(cred)

    db = firestore.client()

    reviews = open(review_file, "r").read().split("@")
    output_file = open(output_file, "w")

    for review in reviews:
        review_data = review.split("\n")
        review_data = list(filter(None, review_data))            

        if len(review_data) > 2:
            try:
                joy_score = float(review_data[2])
                angry_score = float(review_data[3])
                normalization_score = float(review_data[4])

                prof = review_data[0]
                course_id = review_data[1]
                course_name = course_id_to_name(course_id)

                course_code = generate_class_code(course_name, prof)
                score = rate_class(joy_score, angry_score, normalization_score)

                print("Attempting Insertion: " + str(course_code) + " (prof. " + prof + " ) score = " + str(score) + " n = " + str(normalization_score))

                if db.collection(u'classes').document(course_code).get().exists:
                    print("Inserted: " + str(course_code) + " (prof. " + prof + " ) score = " + str(score) + " n = " + str(normalization_score))

                    class_table = db.collection(u'classes').document(course_code)

                    class_table.set({
                        u'course_rating': str(score),
                        u'normalization': str(normalization_score)
                    }, merge=True)

                    output_file.write(str(course_code))
                    output_file.write(str(prof))
                    output_file.write(str(score))
                    output_file.write(str(normalization_score))
                    # add score and normalization score the database

            except IndexError:
                print("ERROR" + str(review_data))

def rate_class(joy, angry, normalization):
    if normalization == 0: return False

    j = float(joy)  / float(normalization)
    a = float(angry) / float(normalization)

    delta_score = sigmoid(a - j, 5)

    return delta_score

def generate_class_code(class_name, prof):
    class_hash = hashlib.md5(prof.encode()).hexdigest()
    class_hash = class_hash[0:10]

    return class_name + "-" + class_hash


def course_id_to_name(course_id):
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

    url = "https://www.layuplist.com" + course_id

    result = session_requests.get(url, headers = dict(referer = URL))
    tree = html.fromstring(result.content)

    div_column = "//div[@class='col-md-12']"
    course_name = tree.xpath("//title/text()")[0].split("|")[0].strip()


    return course_name

normalize(FILE_RATINGS_NAME, FILE_NORMALIZED_NAME)
#generate_analysis()
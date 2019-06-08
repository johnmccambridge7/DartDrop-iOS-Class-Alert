import time
import requests
import json
import re
import math

API_KEY = "AIzaSyDQajRqj-uuVvUzXpw4ZAAjp0VoqGF0_uU"
FILE_NAME = "professor_reviews_full.txt"
FILE_RATINGS_NAME = "professor_review_ratings_PRODUCTION.txt"
FILE_RAW_NAME = "professor_review_ratings_PRODUCTION_RAW.txt"
THRESHOLD = 0.6

# fix the course ID issue in the file
# number of reviews not updated
# consider sigmoid of the differnce as the rating

def sigmoid(x):
  return 1 / (1 + math.exp(-x))

# will determine if a sentence is relative to a professor
# check for prof and professor, pronouns, and the name of the professor
def relative_to_professor(prof, sentence):
    pronouns = ['he', 'she', 'him', 'her']
    titles = ['prof', 'professor']
    regex = re.compile('[^a-zA-Z]')

    prof = prof.lower()
    prof = regex.sub(" ", prof)
    professor = prof.split(" ")

    # print(professor)

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

def main():
    start_time = time.time()
    professor_reviews = open(FILE_NAME, "r").read().split("@")
    reviews = {}
    review_file = open(FILE_RATINGS_NAME, "w")
    review_file_raw = open(FILE_RAW_NAME, "w")

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

            print(professor + "\n")
            print(course_id + "\n")
            print("Review #" + str(i) + "\n")
            print("Anger: " + str(anger_rating) + "\n")
            print("Joy: " + str(joy_rating) + "\n")
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
            review_file.write(course_id + "\n")
            review_file.write(str(scores[0]) + "\n")
            review_file.write(str(scores[1]) + "\n")
            review_file.write(str(scores[2]) + "\n")
            review_file.write("@\n")

    print("\n Analysis Completed in: " + str(time.time() - start_time) + " second. \n")
main()

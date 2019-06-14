"""
Aggregates courses with their 'quality score'
This is going to be used to formulate a competitive-ness score
"""

import json
import hashlib
import math
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

SERVICE_KEY = "service_key.json"

cred = credentials.Certificate(SERVICE_KEY)
firebase_admin.initialize_app(cred)

db = firestore.client()

def generate_class_code(class_name, prof):
    class_hash = hashlib.md5(prof.encode()).hexdigest()
    class_hash = class_hash[0:10]

    return class_name + "-" + class_hash

#String quality_index = String.valueOf(Database.sigmoid(10 * waitlist * Double.valueOf(items.get(2))/100.0));
def quality_index(x):
  x = 10 * (x / 100)
  return 1 / (1 + math.exp(-(x)))

TERM_ID = "201909";
json_file = open('FALL_course_output.json')
parsed_json = json.loads(json_file.read())
quality_scores = open('FALL_quality_scores.txt').read().split('\n')
names = []

score_dict = dict()

for score in quality_scores:
	label = score.split(" ")[0]
	s = score.split("@")[1]
	score_dict[label] = s

for crn in parsed_json.keys():
	course_data = parsed_json[crn]

	if course_data['Term'] == TERM_ID:
		# this may not be correct
		name = course_data['Subj'] + '' + course_data['Num'];
		score = 1

		if name in score_dict.keys():
			score = score_dict[name]

		prof = course_data['Instructor']
		course_id = generate_class_code(course_data['Subj'] + course_data['Num'], prof)
		title = course_data['Subj'] + course_data['Num'] + " " + course_data['Title']
		competitiveness = quality_index(int(score))
		q_index = int(score)

		print("class: " + course_id + "\n")
		print("desc: " + title + "\n")
		print("competitve: " + str(competitiveness) + "\n")
		print("teacher: " + prof + "\n")
		print("quality_index: " + str(q_index) + "\n")

		doc_ref = db.collection(u'classes').document(course_id)
        
		doc_ref.set({
			u'class': course_data['Subj'] + course_data['Num'],
			u'competitiveness': str(competitiveness),
			u'desc': title,
			u'quality_index': str(q_index),
			u'teacher': prof
		})
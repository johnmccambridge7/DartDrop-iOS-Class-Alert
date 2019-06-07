"""
Aggregates courses with their 'quality score'
This is going to be used to formulate a competitive-ness score
"""

import json

term_id = "201903";
json_file = open('output.json')
parsed_json = json.loads(json_file.read())
quality_scores = open('quality_scores.txt').read().split('\n')
names = []

score_dict = dict()

for score in quality_scores:
	label = score.split(" ")[0]
	s = score.split("@")[1]
	score_dict[label] = s

file = open("quality_scores_firebase.txt", "w")

i = 0
for crn in parsed_json.keys():
	course_data = parsed_json[crn]

	if course_data['Term'] == "201903":
		name = course_data['Subj'] + '' + course_data['Num'];
		score = 1

		if name in score_dict.keys():
			score = score_dict[name]

		print("Processing " + str(i) + "/" + str(len(parsed_json.keys())))
		file.write(name + " " + course_data['Title'] + "@" + course_data['Instructor'] + "@" + str(score) + "\n")
		i += 1 

file.close()
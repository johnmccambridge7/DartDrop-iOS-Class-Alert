# iterate over the professor reviews file
# use IBM sentiment analysis to find angry and happy reviews
# algo to decide the rating of the professor
# write to file the ratings of the professor

FILE_NAME = "professor_reviews.txt"

def rate_review(review):
    print(review)

professor_reviews = open(FILE_NAME, "r").read().split("@")
reviews = {}

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

        # perform nlp on the review here

        reviews[course_id][professor] = (anger_rating, joy_rating)


rate_review("Hello world my ame is johN!!")

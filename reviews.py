import requests
import urllib
import time
import json
from lxml import html
from lxml.etree import tostring

USERNAME = "john.l.macdonald.22@dartmouth.edu"
PASSWORD = "Unity2013"

LOGIN_URL = "https://www.layuplist.com/accounts/login/"
URL = "https://www.layuplist.com/best?page="

SEARCH_URL = "https://www.layuplist.com/search?q="
FILE_OUTPUT = "FALL_professor_reviews_full.txt"
TERM_ID = "201909"
COURSE_JSON = "courses/FALL_course_output.json"

# example ITAL010
# bug when fetching page with multiple search results
# scan through and find table row with Offered 19F


def main():
    json_file = open(COURSE_JSON)
    parsed_json = json.loads(json_file.read())
    
    try:
        open(FILE_OUTPUT, "r")
        print("File has already been generated!")
        return True
    except FileNotFoundError:
        print("Creating necessary file");

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

    # Obtain all the course data
    # open json file and iterate over each file

    # For each course get the list of professors that teach the course
    for crn in parsed_json:
        course_data = parsed_json[crn]

        if course_data['Term'] == TERM_ID:
            course_name = course_data['Subj'] + course_data['Num']
            url = SEARCH_URL  + course_name

            result = session_requests.get(url, headers = dict(referer = URL))
            tree = html.fromstring(result.content)

            num_reviews = 0
            course_url_id = result.url.split("/")

            if len(course_url_id) > 4: 
                course_url_id = "/" + course_url_id[3] + "/" + course_url_id[4]
            else:
                course_url_id = 0

            print("Gathering data from: " + url)

            if course_url_id != 0:
                if course_url_id not in review_rankings:
                    review_rankings[course_url_id] = dict()

                div_column = "//div[@class='col-md-12']"

                # search for each professor
                for professor in tree.xpath(div_column + "//table[@class='table table-striped']//tbody//tr//td//a/text()"):
                    if ":" not in professor:
                        professor = professor.strip()
                    
                        # go to the professors review page
                        professor_reviews_url = "https://www.layuplist.com" + course_url_id + "/review_search?q=" + urllib.parse.quote(professor)

                        professor_review_page = session_requests.get(professor_reviews_url, headers = dict(referer = URL))
                        professor_tree = html.fromstring(professor_review_page.content)

                        for review in professor_tree.xpath(div_column + "//table[@class='table table-striped']//tbody//tr//td[@class='highlight-review']/text()"):
                            clean_review = review.replace(":", "").strip()
                            
                            if clean_review != "":

                                if professor not in review_rankings[course_url_id]:
                                    review_rankings[course_url_id][professor] = []
                                
                                # dictionary to a class a professor teaches which stores a tuple of good bad rating
                                num_reviews += 1
                                total_reviews += 1

                                review_rankings[course_url_id][professor].append(clean_review)
                
                print("\tCollected " + str(num_reviews) + " from " + result.url)
                num_reviews = 0
            else:
                print("Failed to collect some information.\n")

    time.sleep(2)

    print("=======================")
    print("Total Reviews Collected: " + str(total_reviews))
    print("=======================")
    
    review_file = open(FILE_OUTPUT, "w")

    for course in review_rankings.keys():
        course_reviews = review_rankings[course]
        
        for professor in course_reviews.keys():
            professor_reviews = review_rankings[course][professor]

            for review in professor_reviews:
                review = review.replace("\n", " ").replace("\r", "")
                
                review_file.write(professor + "\n")
                review_file.write(course + "\n")
                review_file.write(review + "\n")
                review_file.write("@\n")

    review_file.close()

if __name__ == '__main__':
    main()
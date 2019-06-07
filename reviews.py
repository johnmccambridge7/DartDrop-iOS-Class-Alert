import requests
import urllib
import time
from lxml import html
from lxml.etree import tostring

USERNAME = "john.l.macdonald.22@dartmouth.edu"
PASSWORD = "Unity2013"

LOGIN_URL = "https://www.layuplist.com/accounts/login/"
URL = "https://www.layuplist.com/best?page="

def main():

    try:
        open("professor_reviews.txt", "r")
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
    addresses = []

    # Obtain all the course data

    for i in range(1,2):

        # Scrape url
        result = session_requests.get(URL + str(i), headers = dict(referer = URL))
        tree = html.fromstring(result.content)

        print("Fetching partition: " + str(i) + "/51")

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

        # search for each professor

        for professor in tree.xpath(div_column + "//table[@class='table table-striped']//tbody//tr//td//a/text()"):
            if ":" not in professor:
                professor = professor.strip()
                
                # go to the professors review page
                professor_reviews_url = "https://www.layuplist.com" + address + "/review_search?q=" + urllib.parse.quote(professor)

                professor_review_page = session_requests.get(professor_reviews_url, headers = dict(referer = URL))
                professor_tree = html.fromstring(professor_review_page.content)

                for review in professor_tree.xpath(div_column + "//table[@class='table table-striped']//tbody//tr//td[@class='highlight-review']/text()"):
                    clean_review = review.replace(":", "").strip()
                    
                    if clean_review != "":

                        if professor not in review_rankings[address]:
                            review_rankings[address][professor] = []
                        
                        # dictionary to a class a professor teaches which stores a tuple of good bad rating
                        num_reviews += 1
                        total_reviews += 1

                        review_rankings[address][professor].append(clean_review)

        print("\tCollected " + str(num_reviews) + " from " + address)
        num_reviews = 0

    time.sleep(2)

    print("=======================")
    print("Total Reviews Collected: " + str(total_reviews))
    print("=======================")

    review_file = open("professor_reviews.txt", "w")

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
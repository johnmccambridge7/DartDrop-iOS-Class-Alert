import requests
from lxml import html

USERNAME = "john.l.macdonald.22@dartmouth.edu"
PASSWORD = "Unity2013"

LOGIN_URL = "https://www.layuplist.com/accounts/login/"
URL = "https://www.layuplist.com/best?page="

def main():
    session_requests = requests.session()

    # Get login csrf token
    result = session_requests.get(LOGIN_URL)
    tree = html.fromstring(result.text)
    authenticity_token = list(set(tree.xpath("//input[@name='csrfmiddlewaretoken']/@value")))[0]

    # Create payload
    payload = {
        "email": USERNAME, 
        "password": PASSWORD, 
        "csrfmiddlewaretoken": authenticity_token
    }

    # Perform login
    result = session_requests.post(LOGIN_URL, data = payload, headers = dict(referer = LOGIN_URL))
    classes = []
    scores = []

    for i in range(1,52):

        # Scrape url
        result = session_requests.get(URL + str(i), headers = dict(referer = URL))
        tree = html.fromstring(result.content)

        print("Scraping page: " + str(i) + "/51");

        for s in tree.xpath("//h2[@class='score']/text()"):
            if s == "0": s = "1"
            scores.append(s)

        for c in tree.xpath("//h3/a/text()"):
          classes.append(c)

    file = open("quality_scores.txt", "w")

    k = 0;
    for j in range(0, len(classes)):
        file.write(classes[j].replace(":", "") + "@" + scores[j] + "\n")

    file.close()

if __name__ == '__main__':
    main()
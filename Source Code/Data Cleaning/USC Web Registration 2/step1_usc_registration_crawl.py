'''
pip install selenium
pip install webdriver_manager
pip install bs4

'''
import time

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By

from webdriver_manager.chrome import ChromeDriverManager

def extract_terms(html: str) -> list:
    """
    extract term id and name from usc web registration page
    input html: string, usc web registration html
    output terms: list with each item as (term_id, term_title)
    """
    soup = BeautifulSoup(html, "html.parser")
    terms = []

    for li in soup.find_all("li"):  # Find all <li> elements
        term_id = li.get("id")  # Extract the <li> id (e.g., "termmenuFall")
        term_title = li.find("h3", class_="term-title").get_text(strip=True)  # Extract the term title

        if term_id and term_title:
            terms.append((term_id, term_title))  # Store as (id, title) tuple

    return terms


USERNAME = 'szmejia@usc.edu'
PASSWORD = 'AA009akb4z!Zshui1996'
URL =  'https://my.usc.edu/'

# browser = webdriver.Chrome(ChromeDriverManager().install())
cService = webdriver.ChromeService(executable_path=ChromeDriverManager().install())
browser = webdriver.Chrome(service = cService)

browser.get(URL)
time.sleep(5)

# enter username
input_name = browser.find_element(By.ID, "netid")
input_name.clear()
input_name.send_keys(USERNAME)
print("Username entered successfully!")

# enter password
input_pass = browser.find_element(By.ID, 'password')
input_pass.clear()
input_pass.send_keys(PASSWORD)
print("Password entered successfully!")

# login to MyUSC
login_button = browser.find_element(By.ID, 'signInBtn')
login_button.click()
print("MyUSC logged in successfully")
time.sleep(2)

"""
DUO authentication
how to do this step?
need to manually click approve before moving to next step
"""

# trust the browser
trust_browser_button = browser.find_element(By.ID, 'trust-browser-button')
trust_browser_button.click()
print("Trust browser clicked successfully")
time.sleep(10)

# usc web registration
web_reg_button = browser.find_element(By.ID, 'services-1030')
web_reg_button.click()
print("Web Registration logged in successfully")
time.sleep(2)

# get a list of terms
# TODO: not working properly
terms_list = browser.find_element(By.CSS_SELECTOR, "ul.terms-list")
test = browser.find_element(By.ID, 'termmenuFall')
test = browser.find_element(By.CSS_SELECTOR, "a[id='termLink2']")

terms_html = terms_list.get_attribute("innerHTML")
term_list = extract_terms(terms_html)

# click into each term page and extract classes
PROGRAM_SCRAP_LIST = {
    'DataScience': "a.deptSub[href*='DSCI']",
    'ComputerScience': ""
}

term_id = 'termmenuFall'
term_title = 'Fall 2025'

for term_id, term_title in term_list:
    print(f"processing - term_id: {term_id}, term_title: {term_title}")

    # click by term_id
    terms_ix = browser.find_element(By.ID, term_id)
    terms_ix.click()
    print(f"=== clicked into {term_title} class registration successfully")

    # click the "Continue" button to accept the acknowledgement
    continue_button = browser.find_element(By.CSS_SELECTOR, "a.btn.btn-default")
    continue_button.click()
    print("=== Acknowledgement accepted. Clicked Continue button successfully")

    # expand "Viterbi School of Engineering"
    viterbi_header = browser.find_element(By.CSS_SELECTOR, "a[href='#deptDiv13']")
    viterbi_header.click()
    print("Expanded Viterbi School of Engineering")
    time.sleep(2)

    for program_name, program_ref in PROGRAM_SCRAP_LIST.items():
        # click program
        program_link = browser.find_element(By.CSS_SELECTOR, )
        program_link.click()
        print(f"Clicked into {program_name} department successfully")

        # Find all class elements that need to be expanded
        class_elements = browser.find_elements(By.CSS_SELECTOR, "div.course-header a[data-toggle='collapse']")

        # Loop through each class, expand it, and extract information
        class_data = []
        for class_element in class_elements:
            # Expand the class
            browser.execute_script("arguments[0].click();", class_element)
            time.sleep(2)  # Wait for content to load

            # Extract crsID (Course ID)
            crsID = class_element.find_element(By.CSS_SELECTOR, "span.crsID").text.strip()

            # Extract crsTitl (Course Title)
            crsTitl = class_element.find_element(By.CSS_SELECTOR, "span.crsTitl").text.strip()

            # Extract course info (Description inside the expanded section)
            course_bin_id = class_element.get_attribute("href").split("#")[-1]  # Get the ID of the expanded section
            course_info_element = browser.find_element(By.ID, course_bin_id)
            course_info = course_info_element.find_element(By.CSS_SELECTOR,
                                                           "div.bs-callout.bs-callout-default span").text.strip()

            # Store data
            class_data.append({
                "crsID": crsID,
                "crsTitl": crsTitl,
                "course_info": course_info
            })

            print(f"Extracted: {crsID} - {crsTitl}")

        # Print all extracted data
        for course in class_data:
            print(course)
















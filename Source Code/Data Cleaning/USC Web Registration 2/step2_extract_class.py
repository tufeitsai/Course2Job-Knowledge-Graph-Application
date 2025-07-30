import os
from bs4 import BeautifulSoup
import pandas as pd


def extract_courses(html):
    soup = BeautifulSoup(html, 'html.parser')
    output = []

    course_headers = soup.select('.course-header')
    for header in course_headers:
        course_id_tag = header.select_one('.crsID') #<span class="crsID">CSCI-476:</span>
        course_title_tag = header.select_one('.crsTitl') #<span class="crsTitl">Cryptography: Secure Communication and Computation </span>
        course_href = header['href'] ##courseBin_CSCI-476
        course_code = course_id_tag.text.strip().replace(":", "") if course_id_tag else "" #CSCI-476
        course_name = course_title_tag.text.strip() if course_title_tag else "" #Cryptography: Secure Communication and Computation'

        # Locate corresponding content area by ID
        content_id = course_href.lstrip('#')
        content_div = soup.find('div', id=content_id)

        # Extract description
        desc_div = content_div.select_one('.bs-callout span')
        course_description = desc_div.text.strip() if desc_div else ""

        # Extract prerequisites
        prereq_span = content_div.select_one('.prereqcoreq_val')
        course_prereq = prereq_span.text.strip() if prereq_span else ""

        # Look for D-Clearance information
        d_clearance = ""
        if "D-Clearance" in course_description:
            d_clearance = course_description

        # Parse section info
        sections = content_div.select('.section')

        for section in sections:
            row = section.select_one('.section_crsbin')
            if not row:
                continue

            get_text = lambda sel: (row.select_one(sel).text.strip().replace('\n', '') if row.select_one(sel) else "")

            output.append({
                "courseNum": course_code,
                "courseName": course_name,
                "courseDescription": course_description,
                "coursePrequisites": course_prereq,
                "Section": get_text('span:nth-of-type(1) b'),
                "Session": get_text('span:nth-of-type(2) a'),
                "Type": get_text('span:nth-of-type(3)').replace('Type:', '').strip(),
                "Units": get_text('span:nth-of-type(4)').replace('Units:', '').strip(),
                "Registered": row.select('span.section_row')[4].find_all('span')[-1].text.strip(),
                "Time": row.select('span.section_row')[5].find_all('span')[-1].text.strip(),
                "Days": row.select('span.section_row')[6].find_all('span')[-1].text.strip().replace('Days:', ''),
                "Instructor": row.select('span.section_row')[7].find_all('span')[-1].text.strip().replace('Instructor:', ''),
                "Location": row.select('span.section_row')[8].find_all('span')[-1].text.strip(),
                "D-Clearance": d_clearance
            })

    return output


# Example usage
file_path_ls = [
    # 'fall2025_cs_page1.html',
    # 'fall2025_cs_page2.html',
    # 'fall2025_cs_page3.html',
    'summer2025_cs_page1.html',
    'summer2025_ds_page1.html',
    'spring2025_cs_page1.html',
    'spring2025_cs_page2.html',
    'spring2025_cs_page3.html',
    'spring2025_ds_page1.html'
]

folder_path = '/Users/shuijingzhang/Library/Mobile Documents/com~apple~CloudDocs/USC/DSCI558 - Building Knowledge Graphs/project/data/'


for file_path in file_path_ls:
    print(f'Reading in : {file_path}')
    with open(os.path.join(folder_path, file_path), "r", encoding="utf-8") as f:
        html_content = f.read()

    print(f'Extract courses')
    courses = extract_courses(html_content)

    # Pretty print JSON
    output_file = file_path.replace('.html', '.csv')
    print(f'Saving course to: {output_file}')
    pd.DataFrame(courses).to_csv(os.path.join(folder_path, output_file), index=False)

    print('======')


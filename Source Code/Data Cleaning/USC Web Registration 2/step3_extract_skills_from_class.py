import os
import pandas as pd
from tqdm import tqdm

import ollama
from openai import OpenAI

API_KEY = "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"
MODEL = "gpt-4o-2024-08-06"
# MODEL = 'deepseek-r1:7b'


client = OpenAI(api_key=API_KEY)

file_path_ls = [
    'fall2025_ds_page1.csv',
    'fall2025_cs_page1.csv',
    'fall2025_cs_page2.csv',
    'fall2025_cs_page3.csv',
    'summer2025_cs_page1.csv',
    'summer2025_ds_page1.csv',
    'spring2025_cs_page1.csv',
    'spring2025_cs_page2.csv',
    'spring2025_cs_page3.csv',
    'spring2025_ds_page1.csv'
]

folder_path = '/Users/shuijingzhang/Library/Mobile Documents/com~apple~CloudDocs/USC/DSCI558 - Building Knowledge Graphs/project/data/'

print('Reading in all classes')
data = pd.DataFrame()
for file_path in file_path_ls:
    data_ix = pd.read_csv(os.path.join(folder_path, file_path))
    data_ix['term'] = file_path.split('_')[0]
    data = pd.concat([data, data_ix])

print('Sanity Check')
print(data.shape)
# (524, 17)
print(data.term.value_counts(dropna = False))
# spring2025    240
# fall2025      235
# summer2025     49


print('Removing duplication')
data_clean = data.drop_duplicates(subset=['courseNum','courseName', 'courseDescription'])
data_clean.reset_index(inplace=True, drop=True)
print(data_clean.shape)
# (133, 15)

print('Setting up prompt messages')
prompt = """Your task is to extract *skills and topics* from the following course description text to help students better understand what each course teaches. Use **exact words or phrases** from the input text, and list all extracted skills/topics separated by commas in a Python list format."""
input_example = """Introduction to Computational Thinking and Data Science – Introduction to data analysis techniques and associated computing concepts for non-programmers. Topics include foundations for data analysis, visualization, parallel processing, metadata, provenance, and data stewardship. Recommended preparation: mathematics and logic undergraduate courses."""
ouput_example = """['data analysis', 'visualization', 'parallel processing', 'metadata', 'provenance', 'data stewardship']"""

prompt_message = [
    {'role':'system', 'content': prompt},
    {'role': 'user', "content": input_example},
    {'role': 'assistant', "content": ouput_example}
]

print('Extracting skills based on courseName and courseDescription')
for ix in tqdm(range(len(data_clean))):
    course_name = data_clean.loc[ix, 'courseName']
    course_description = data_clean.loc[ix, 'courseDescription']

    input_ix = f'{course_name} - {course_description}'
    messages = prompt_message + [{'role': 'user', "content": input_ix}]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    # response = ollama.chat(
    #   model=MODEL,
    #     messages=messages
    # )

    try:
        data_clean.loc[ix, 'extracted_skills'] = response.choices[0].message.content
    except:
        print('Skiped')

data_clean[['term', 'courseNum','courseName', 'courseDescription', 'extracted_skills']].to_csv(os.path.join(folder_path, 'course_skills.csv'), index = False)

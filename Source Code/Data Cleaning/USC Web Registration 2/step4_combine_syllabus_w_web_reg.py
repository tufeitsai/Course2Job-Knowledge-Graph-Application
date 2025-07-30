import os
import itertools

import json
import pandas as pd
import numpy as np
from tqdm import tqdm

from sklearn.cluster import AgglomerativeClustering

from sentence_transformers import SentenceTransformer
# MODEL = SentenceTransformer('distilbert-base-nli-mean-tokens')
MODEL = SentenceTransformer('all-MiniLM-L6-v2')


FOLDER_PATH = '/Users/shuijingzhang/Library/Mobile Documents/com~apple~CloudDocs/USC/DSCI558 - Building Knowledge Graphs/project/data/'

def clean_and_concat_job_posting(job_posting_ls):
    final_ls = []
    for job_posting in job_posting_ls:
        if job_posting and len(job_posting) > 0:
            final_ls += [c.lower() for c in job_posting if c]
    final_ls = list(set(final_ls))
    final_ls.sort()
    return final_ls


def agglomerative_clustering(sentence_ls, model, distance_threshold=2):
    clustering_model = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold, #1.5
    )

    corpus_embeddings = model.encode(sentence_ls)

    clustering_model.fit(corpus_embeddings)
    cluster_assignment = clustering_model.labels_

    clustered_sentences = {}
    for sentence_id, cluster_id in enumerate(cluster_assignment):
        if cluster_id not in clustered_sentences:
            clustered_sentences[cluster_id] = []

        clustered_sentences[int(cluster_id)].append(sentence_ls[sentence_id])

    for i, cluster in clustered_sentences.items():
        print("Cluster ", i + 1)
        print(cluster)
        print("")
    return clustered_sentences, clustering_model


def find_cluster_representatives(clustered_sentences, model):
    cluster_reps = {}

    for cluster_id, sentences in tqdm(clustered_sentences.items()):
        embeddings = model.encode(sentences)
        centroid = np.mean(embeddings, axis=0)

        # Find the sentence closest to the centroid
        distances = np.linalg.norm(embeddings - centroid, axis=1)
        representative_idx = np.argmin(distances)

        cluster_reps[cluster_id] = {
            'representative': sentences[representative_idx],
            'members': sentences
        }

    return cluster_reps


def match_word_w_cluster(word, clusters_w_rep):
    for cluster_dict_ix in clusters_w_rep.values():
        if word in cluster_dict_ix['members']:
            return cluster_dict_ix['representative']
    return None


print('Reading in syllabus')
with open(os.path.join(FOLDER_PATH, 'syllabus', 'gpt_extraction.json'), 'r') as source:
    syllabus = json.load(source)
syllabus = dict((key, [c.lower() for c in value]) for key, value in syllabus.items())


print('Reading in web_reg')
web_reg = pd.read_csv(os.path.join(FOLDER_PATH, 'web_registration', 'course_skills.csv'))
web_reg['extracted_skills_clean'] = web_reg.extracted_skills.apply(lambda v: [c.lower() for c in eval(v)])


print('Reading in job posting')
with open(os.path.join(FOLDER_PATH, 'job_posting_website', 'Final_mapped_keywords.json'), 'r') as source:
    job_posting = json.load(source)


print('Cleaning syllabus skills')
syllabs_skills_ls = list(itertools.chain(*[c for c in syllabus.values()]))
print(f'There are {len(syllabs_skills_ls)} skills in syllabus')
# There are 1044 skills in syllabus
syllabs_skills_ls = list(set(syllabs_skills_ls))
print(f'There are {len(syllabs_skills_ls)} UNIQUE skills in syllabus')
# There are 771 UNIQUE skills in syllabus


print('Cleaning web registration skills')
web_reg_skills_ls = list(itertools.chain(*web_reg.extracted_skills_clean.tolist()))
print(f'There are {len(web_reg_skills_ls)} skills in web_reg')
# There are 726 skills in syllabus
web_reg_skills_ls = list(set(web_reg_skills_ls))
print(f'There are {len(web_reg_skills_ls)} UNIQUE skills in web_reg')
# There are 535 UNIQUE skills in web_reg


print('Cleaning job posting skills')
job_posting_skills_ls = [c.get('Technologies', []) for c in job_posting]
job_posting_skills_ls = clean_and_concat_job_posting(job_posting_skills_ls)
print(f'There are {len(job_posting_skills_ls)} UNIQUE skills in job posting')
# There are 7209 UNIQUE skills in job posting


print('Combining three sources skills')
combine_skills = syllabs_skills_ls + web_reg_skills_ls + job_posting_skills_ls
combine_skills = list(set(combine_skills))
print(f'There are {len(combine_skills)} UNIQUE skills in combined sources')
# There are 8177 UNIQUE skills in combined sources

DISTANCE = 1
print('Start performing agglomerative clustering')
clusters, model = agglomerative_clustering(combine_skills, MODEL, DISTANCE)
print(f'Clustered all skills into {len(clusters)} clusters')
# Clustered all skills into 3570 clusters


print('Getting representation for each cluster')
clusters_w_rep = find_cluster_representatives(clusters, MODEL)

print('Saving all clusters')
key_ls = list(clusters_w_rep.keys())
for key in key_ls:
    clusters_w_rep[int(key)] = clusters_w_rep.pop(key)
with open(os.path.join(FOLDER_PATH, f'three_sources_skills_clusters_all_{DISTANCE}.json'), 'w') as source:
    json.dump(clusters_w_rep, source, indent=2)

print('Sanity Check')
cluster_len_dict = {}
for key, cluster in clusters_w_rep.items():
    cluster_len = len(cluster['members'])
    if cluster_len in cluster_len_dict:
        cluster_ix = cluster_len_dict[cluster_len]
        cluster_ix.append(cluster)

    else:
        cluster_len_dict[cluster_len] = [cluster]


# cluster_len_dict_sort = sorted(cluster_len_dict.items())
# cluster_len_dict_sort = dict(cluster_len_dict_sort)
# cluster_len_dict_sort.keys()
# # dict_keys([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 17])
# print(cluster_len_dict_sort[17])

for key, cluster in clusters_w_rep.items():
    if cluster['representative'] == 'data scientist':
        print(cluster)
        cluster['representative']  = 'data science'


print('Saving cleaned clusters')
with open(os.path.join(FOLDER_PATH, f'three_sources_skills_clusters_{DISTANCE}_cleaned.json'), 'w') as source:
    json.dump(clusters_w_rep, source, indent=2)


# read in cluster back in again
with open(os.path.join(FOLDER_PATH,  f'three_sources_skills_clusters_{DISTANCE}_cleaned.json'), 'r') as source:
    clusters_w_rep = json.load(source)

print('Replacing job posting skills with cluster representations')
job_posting_final = []
for job_dict in tqdm(job_posting):
    tech_ls_clean = []
    if 'Technologies' in job_dict and job_dict['Technologies']:
        tech_ls = [c.lower() for c in job_dict['Technologies'] if c]
        tech_ls_clean = list(set([match_word_w_cluster(c, clusters_w_rep) for c in tech_ls]))
        if None in tech_ls_clean:
            tech_ls_clean.remove(None)
    job_posting_final.append({'index': job_dict['index'], 'Technologies': tech_ls_clean})


print('Saving finalized job posting skills')
with open(os.path.join(FOLDER_PATH, 'final_job_posting.json'), 'w') as source:
    json.dump(job_posting_final, source, indent=2)


print('Combining syllabus with web_reg and replacing skills')
course_ls =  list(syllabus.keys()) + web_reg.courseNum.tolist()
course_ls = list(set(course_ls))

syllabus_web_dict = dict()
for courseNum in course_ls:
    skill_syllabus = syllabus.get(courseNum, [])
    skill_web_reg = list(itertools.chain(*[c for c in web_reg[web_reg.courseNum == courseNum].extracted_skills_clean.tolist()]))

    skills_ls = skill_syllabus + skill_web_reg
    skill_ls_clean = list(set([match_word_w_cluster(c, clusters_w_rep) for c in skills_ls]))
    if None in skill_ls_clean:
        skill_ls_clean.remove(None)

    syllabus_web_dict[courseNum] = {
        'extracted_skills_clean': skill_ls_clean
    }


print('Saving finalized syllabus and web reg skills')
with open(os.path.join(FOLDER_PATH, 'final_syllabus_web_reg.json'), 'w') as source:
    json.dump(syllabus_web_dict, source, indent=2)
















# print('Calculating similarities')
# sentence_embeddings = MODEL.encode(combine_skills)
# similarities = MODEL.similarity(sentence_embeddings, sentence_embeddings)
#
# SIMILARITY_THRESHOLD = 0.75
#
# similar_skill_idx_ls = []
# no_match_skill_idx_ls = set()
# for skill_ix in range(len(similarities)):
#     arr = similarities[skill_ix]
#     max_index = np.argmax(arr)
#
#     temp_arr = arr.clone().detach()
#     temp_arr[max_index] = float('-inf')
#
#     if max(temp_arr) > SIMILARITY_THRESHOLD:
#         second_max_index = int(np.argmax(temp_arr))
#         similar_skill_idx_ls.append(set([skill_ix, second_max_index]))
#     else:
#         no_match_skill_idx_ls.add(skill_ix)
#
# print('Sanity check some unmatched skills')
# no_match_skill_ls = [combine_skills[ix] for ix in no_match_skill_idx_ls]
# no_match_skill_ls.sort()
# print(len(no_match_skill_ls))
# for c in no_match_skill_ls:
#     print(c)
#
#
# # move similar sets in one group
# cluster_ls = []
# for similar_pair in similar_skill_idx_ls:
#     word1, word2 = similar_pair
#     selected_cluster = []
#     for cluster_idx in range(len(cluster_ls)):
#         if word1 in cluster_ls[cluster_idx] or word2 in cluster_ls[cluster_idx]:
#             selected_cluster.append(cluster_idx)
#
#     if len(selected_cluster) == 0:
#         cluster_ls.append(list(similar_pair))
#
#     if len(selected_cluster) == 1:
#         cluster_ls[selected_cluster[0]] = list(set(cluster_ls[selected_cluster[0]] + list(similar_pair)))
#
#     if len(selected_cluster) == 2:
#         cluster_combine_1 = cluster_ls[selected_cluster[0]]
#         cluster_combine_2 = cluster_ls[selected_cluster[1]]
#
#         new_cluster = cluster_combine_1 + cluster_combine_2
#         cluster_ls.remove(cluster_combine_1)
#         cluster_ls.remove(cluster_combine_2)
#         cluster_ls.append(new_cluster)
#
# print(len(cluster_ls))
# # 194
#
# print('Sanity Check')
# match_skill_ls = []
# for cluster in cluster_ls:
#     match_skill_ix = []
#     for ix in cluster:
#         match_skill_ix.append(combine_skills[ix])
#     match_skill_ls.append(match_skill_ix)
#
# match_skill_ls.sort(key=len, reverse=True)
# for cluster in match_skill_ls:
#     print(cluster)
#
#
# all_skill_ls = match_skill_ls + [[c] for c in no_match_skill_ls]
#
# def clean_skill(skill_to_search, all_skill_ls):
#     for cluster in all_skill_ls:
#         if skill_to_search in cluster:
#             return cluster[0]
#
# for ix in range(len(all_data_df)):
#     syllabus_skill_ls = all_data_df.loc[ix, 'extracted_skills_clean_syllabus']
#     webreg_skill_ls = all_data_df.loc[ix, 'extracted_skills_clean_webreg']
#
#     if pd.isna(syllabus_skill_ls):
#         skill_ls_ix = list(set(webreg_skill_ls))
#     else:
#         skill_ls_ix = list(set(eval(syllabus_skill_ls) + webreg_skill_ls))
#
#     skill_clean_ls_ix = [clean_skill(c, all_skill_ls) for c in skill_ls_ix]
#     all_data_df.loc[ix, 'extracted_skills_final'] = str(skill_clean_ls_ix)
#
# all_data_df.to_csv(os.path.join(FOLDER_PATH, 'syllabus_web_reg_skills.csv'), index = False)

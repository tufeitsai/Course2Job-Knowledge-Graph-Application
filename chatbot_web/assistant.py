import os
from openai import OpenAI
import json
import rltk
from gensim.models import KeyedVectors
import numpy as np
import pandas as pd
from collections import defaultdict, deque
from neo4j import GraphDatabase

API_KEY = "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"
MODEL = "llama3-8b-8192"

URI = "neo4j+s://9ea9d411.databases.neo4j.io"
USERNAME = "neo4j"
PASSWORD = "lW2dXVTTyJE_xI30dyV-AxsoeD7HMn-VP23wTw0JFfI"

tokenizer = rltk.tokenizer.crf_tokenizer.crf_tokenizer.CrfTokenizer()
word2vec_model = KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)

class Course2JobAssistant:
    def __init__(self):
        self.slot =  {"role": None, "courseLevel": None, "major": None, "courseNum": [], "skills": []}
        self.intent = {"role2course": True, "course2job": False, "skill2job": False}

        self.roles = ["Software Engineer", "Data Scientist", "Machine Learning Engineer", "AI Researcher", "Web Developer", "Cybersecurity Specialist", "Cloud Engineer"]
        self.courseNums = ["CSCI-570", "CSCI-561", "CSCI-566", "CSCI-585", "CSCI-576", "CSCI-555", "DSCI-558"]
        with open('skills.json', 'r') as f:
            self.skills = json.load(f)['skills']

        self.driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

        self.driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

    def intent_recognition(self, user_input):
        pass

    def entity_extraction(self, user_input):
        prompt = f"""
            You are a strict information extractor.

            Extract the following fields from the user's input, and return a **valid JSON object** with:
            - role: desired career or job role
            - courseLevel: academic level, e.g., "undergraduate", "graduate"
            - major: academic major, e.g., "Computer Science"
            - courseNum: list of course codes (e.g., ["CS101", "STAT202"])
            - skills: list of skills mentioned (e.g., ["Python", "Machine Learning"])

            If a field is not mentioned, set it to null (for strings) or [] (for lists).
            Only output a strict JSON object. No explanation.  
            Input: "{user_input}"
        """

        client = OpenAI(api_key=API_KEY, base_url="https://api.groq.com/openai/v1")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an intelligent assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=100
        )

        res = response.choices[0].message.content
        print("\U0001F9BE Raw LLM output:", res)
        try:
            new_slot = json.loads(res)
        except json.JSONDecodeError:
            print("❌ Failed to parse LLM output as JSON")
            new_slot = {}

        print("\U0001F9E0 Parsed LLM output:", new_slot)
        for key in self.slot:
            if key in new_slot and new_slot[key]:
                self.slot[key] = new_slot[key]

    def entity_linking(self):
        if self.slot["role"]:
            self.slot["role"] = self.entity_resolution(self.slot["role"], self.roles)

        if self.slot["courseLevel"]:
            level = self.slot["courseLevel"].lower()
            if level in ["undergrad", "undergraduate", "bachelor", "bachelor's", "college", "college level", "college student", "university student", "university level", "u-grad", "ug", "baccalaureate"]:
                self.slot["courseLevel"] = "undergraduate"
            elif level in ["graduate", "grad", "postgraduate", "post-grad", "post grad", "master", "master's", "masters", "ms", "msc", "phd", "doctoral", "doctorate", "research student", "graduate school", "grad school"]:
                self.slot["courseLevel"] = "graduate"
            else:
                self.slot["courseLevel"] = None

        if self.slot["major"]:
            major = self.slot["major"].lower()
            if major in ["cs", "computer science"]:
                self.slot["major"] = "Computer Science"
            elif major in ["ds", "data science", "applied data science"]:
                self.slot["major"] = "Data Science"
            else:
                self.slot["major"] = None

        if self.slot["courseNum"]:
            cleaned = [self.entity_resolution(course.lower(), self.courseNums) for course in self.slot["courseNum"]]
            self.slot["courseNum"] = [c for c in cleaned if c]

        if self.slot["skills"]:
            cleaned = [self.entity_resolution(skill, self.skills) for skill in self.slot["skills"]]
            self.slot["skills"] = [s for s in cleaned if s]

    def check_missing_slots(self):
        missing = []
        if not self.slot["role"]:
            missing.append("your desired job role")
        if not self.slot["major"]:
            missing.append("your major")
        if not self.slot["courseLevel"]:
            missing.append("your academic level (e.g., undergrad or graduate)")
        return missing

    def entity_resolution(self, x, y_list):
        def string_similarity_1(s1, s2):
            return rltk.jaro_winkler_similarity(s1, s2)

        def string_similarity_2(s1_set, s2_set):
            return rltk.jaccard_index_similarity(s1_set, s2_set)

        def string_similarity_3(s1_set, s2_set):
            vector_1 = [word2vec_model[word] for word in s1_set if word in word2vec_model]
            vector_2 = [word2vec_model[word] for word in s2_set if word in word2vec_model]
            v1 = np.mean(vector_1, axis=0) if vector_1 else np.zeros(word2vec_model.vector_size)
            v2 = np.mean(vector_2, axis=0) if vector_2 else np.zeros(word2vec_model.vector_size)
            numerator = np.dot(v1, v2)
            denominator = np.linalg.norm(v1) * np.linalg.norm(v2)
            return numerator / denominator if denominator != 0 else 0.0

        def rule_based_method(s1, s2):
            s1_set = set(tokenizer.tokenize(s1))
            s2_set = set(tokenizer.tokenize(s2))
            return 0.4 * string_similarity_1(s1, s2) + 0.2 * string_similarity_2(s1_set, s2_set) + 0.4 * string_similarity_3(s1_set, s2_set)

        best_score, best_match = 0, None
        for y in y_list:
            score = rule_based_method(x.lower(), y.lower())
            if score > best_score:
                best_score = score
                best_match = y
        return best_match if best_score >= 0.5 else None

    def get_course_by_role(self, role, major, courseLevel):
        query_result, _, _ = self.driver.execute_query("""
            MATCH (r:Role {roleName: $role})-[rel1:ROLE_REQUIRES_SKILL]->(s:Skill)
            MATCH (s)<-[rel2:TEACHES_SKILL]-(c:Course {courseLevel: $courseLevel})
            MATCH (m {majorName: $major})<-[:PART_OF_MAJOR]-(c)
            OPTIONAL MATCH (c)-[:HAS_PREREQUISITE]->(c2)
            WHERE rel1.importance >= 0.1
            WITH c.courseNum AS courseNum, 
                c.courseName AS courseName, 
                c.webCourseDescription as courseDescription,
                collect(DISTINCT c2.courseNum) AS prerequisites,
                collect(DISTINCT s.skillName) AS skillNames
            RETURN courseNum, courseName, courseDescription, prerequisites, size(skillNames) AS skillCount, skillNames
            ORDER BY skillCount DESC
            LIMIT 8
        """, role=role, major=major, courseLevel=courseLevel)

        courses = {}
        all_skills_needed = set()
        for record in query_result:
            courseNum = record["courseNum"]
            courseName = record["courseName"]
            courseDescription = record["courseDescription"]
            prerequisites = record["prerequisites"]
            skills = record["skillNames"]
            all_skills_needed.update(skills)
            courses[courseNum] = {
                "courseName": courseName,
                "courseDescription": courseDescription,
                "prerequisites": prerequisites,
            }

        return courses, list(all_skills_needed)

    def response_generation(self, result_with_skills):
        result, skills = result_with_skills
        if self.intent["role2course"]:
            formatted_skills = ", ".join(sorted(skills))
            response = f"**Becoming a {self.slot['role']} will need skills:** {formatted_skills}\n\n"
            response += f"To help you prepare for the role of {self.slot['role']}, we recommend the following courses:\n\n"

            for course_code, details in result.items():
                name = details["courseName"]
                description = details["courseDescription"].split("NOTE")[0].strip()
                prerequisites = details["prerequisites"]
                response += f"📖 **{course_code}: {name}**\n"
                response += f"{description}\n"
                if prerequisites:
                    prereq_str = ", ".join(prerequisites)
                    response += f"📌 Prerequisites: {prereq_str}\n"
                response += "\n"

            response += "Let me know if you'd like to explore any course in more detail, or get course planning suggestions!"

        return response

    def greet(self):
        return (
            "👋 Hi, I'm your Course2Job Assistant!\n\n"
            "Tell me your desired job role, your current major, and your academic level, and I’ll recommend the most relevant courses to help you reach your goal. 🚀\n\n"
            "For example, you can say:\n"
            "> I'm a graduate student in Computer Science and I want to be a Machine Learning Engineer."
        )

    def reset(self):
        self.slot = {"role": None, "courseLevel": None, "major": None, "courseNum": [], "skills": []}
        self.intent = {"role2course": True, "course2job": False, "skill2job": False}

    def start(self, user_input):
        self.entity_extraction(user_input)
        self.intent_recognition(user_input)
        self.entity_linking()
        missing = self.check_missing_slots()
        if missing:
            return "To proceed, could you please provide " + ", ".join(missing) + "?"
        result = self.get_course_by_role(self.slot["role"], self.slot["major"], self.slot["courseLevel"])
        return self.response_generation(result)

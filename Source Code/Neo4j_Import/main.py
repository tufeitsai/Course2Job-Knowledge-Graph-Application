
from neo4j import GraphDatabase
import json
import pandas as pd
from tqdm import tqdm

# ----------- Neo4j Aura Cloud Connection -----------
uri = "neo4j+s://9ea9d411.databases.neo4j.io"
username = "neo4j"
password = "lW2dXVTTyJE_xI30dyV-AxsoeD7HMn-VP23wTw0JFfI"
driver = GraphDatabase.driver(uri, auth=(username, password))


# ------------------- INSERT NODES -------------------

def insert_nodes():
    with open('course_raw.json', 'r') as f:
        data = json.load(f)

    with driver.session() as session:
        for courseNum, row in tqdm(data.items(), desc="📚 Inserting Courses"):
            session.run("""
                MERGE (c:Course {
                    courseNum: $courseNum,
                    courseName: $courseName,
                    courseLevel: $courseLevel,
                    term: $term,
                    section: $section,
                    session: $session,
                    type: $type,
                    units: $units,
                    time: $time,
                    days: $days,
                    courseLocation: $courseLocation,
                    d_clearance: $d_clearance,
                    webCourseDescription: $webCourseDescription,
                    syllabusCourseDescription: $syllabusCourseDescription,
                    syllabusTableDescription: $syllabusTableDescription,
                    syllabusLearningObjective: $syllabusLearningObjective
                })
            """, courseNum=courseNum, courseName=row.get("courseName"), courseLevel=row.get("courseLevel"),
                 term=row.get("Semester"), section=row.get("Section"), session=row.get("Session"), type=row.get("Type"),
                 units=row.get("Units"), time=row.get("Time"), days=row.get("Days"), courseLocation=row.get("Location"),
                 d_clearance=row.get("D-Clearance"), webCourseDescription=row.get("WebCourseDescription"),
                 syllabusCourseDescription=row.get("SyllabusCourseDescription"),
                 syllabusTableDescription=row.get("SyllabusTableDescription"),
                 syllabusLearningObjective=row.get("SyllabusLearningObjective"))

        for courseNum, row in tqdm(data.items(), desc=" Inserting Majors"):
            session.run("MERGE (m:Major { majorName: $majorName })", majorName=row.get("Major"))

    instructors = {ins for _, row in data.items() for ins in row.get("Instructor", [])}
    with driver.session() as session:
        for instructor in tqdm(instructors, desc=" Inserting Instructors"):
            session.run("MERGE (i:Instructor { instructorName: $instructorName })", instructorName=instructor)

    with open('Final_cleaned_jobs_data.json', 'r') as f:
        jobs = json.load(f)

    with driver.session() as session:
        for job in tqdm(jobs, desc=" Inserting Jobs"):
            session.run("""
                MERGE (j:Job {
                    index: $index,
                    jobTitle: $jobTitle,
                    jobLocation: $location,
                    employmentType: $workType,
                    estimatedSalary: $salary,
                    benefits: $benefits,
                    url: $url,
                    jobDescription: $description
                })
            """, index=job["index"], jobTitle=job.get("Job Title"), location=job.get("Location"),
                 workType=job.get("Work Type"), salary=job.get("Salary"), benefits=job.get("Benefits"),
                 url=job.get("URL"), description=job.get("Full Job Description"))

        for job in tqdm(jobs, desc="🏢 Inserting Employers"):
            session.run("MERGE (e:Employer { employerName: $employer })", employer=job["Company"])

    skills = set()
    with open("final_job_posting.json", "r") as f:
        job_skills = json.load(f)
    for j in job_skills:
        skills.update(j.get("Technologies", []))
    for row in data.values():
        skills.update(row.get("Skills", []))

    with driver.session() as session:
        for skill in tqdm(skills, desc=" Inserting Skills"):
            session.run("MERGE (s:Skill { skillName: $name })", name=skill)

    with open("role_to_skills.json", "r") as f:
        roles = json.load(f)
    with driver.session() as session:
        for role in tqdm(roles.keys(), desc=" Inserting Roles"):
            session.run("MERGE (r:Role { roleName: $name })", name=role)


# ------------------- INSERT RELATIONSHIPS -------------------

def insert_edges():
    with open('course_raw.json', 'r') as f:
        courses = json.load(f)

    courseList = set(courses.keys())

    with driver.session() as session:
        for courseNum, row in tqdm(courses.items(), desc=" Linking Courses"):
            for preq in row.get("CoursePreq", []):
                for c in preq.split('/'):
                    if c in courseList:
                        session.run("""
                            MATCH (a:Course {courseNum: $a}), (b:Course {courseNum: $b})
                            MERGE (a)-[:HAS_PREREQUISITE]->(b)
                        """, a=courseNum, b=c)

            for ins in row.get("Instructor", []):
                session.run("""
                    MATCH (c:Course {courseNum: $num}), (i:Instructor {instructorName: $name})
                    MERGE (c)-[:TAUGHT_BY]->(i)
                """, num=courseNum, name=ins)

            for sk in row.get("Skills", []):
                session.run("""
                    MATCH (c:Course {courseNum: $num}), (s:Skill {skillName: $name})
                    MERGE (c)-[:TEACHES_SKILL]->(s)
                """, num=courseNum, name=sk)

            session.run("""
                MATCH (c:Course {courseNum: $num}), (m:Major {majorName: $major})
                MERGE (c)-[:PART_OF_MAJOR]->(m)
            """, num=courseNum, major=row.get("Major"))

    with open('Final_cleaned_jobs_data.json', 'r') as f:
        jobs = json.load(f)

    with driver.session() as session:
        for job in tqdm(jobs, desc="🔗 Linking Jobs and Employers"):
            if job.get("Company"):
                session.run("""
                    MATCH (j:Job {index: $index}), (e:Employer {employerName: $company})
                    MERGE (j)-[:POSTED_BY]->(e)
                """, index=job["index"], company=job["Company"])

    with open("final_job_posting.json", "r") as f:
        job_skills = json.load(f)
    with driver.session() as session:
        for js in tqdm(job_skills, desc="🔗 Linking Jobs and Skills"):
            for tech in js.get("Technologies", []):
                session.run("""
                    MATCH (j:Job {index: $index}), (s:Skill {skillName: $skill})
                    MERGE (j)-[:JOB_REQUIRES_SKILL]->(s)
                """, index=int(js["index"]), skill=tech)

    with open("role_to_skills.json", "r") as f:
        role_skills = json.load(f)
    with driver.session() as session:
        for role, skills in tqdm(role_skills.items(), desc="🔗 Linking Roles and Skills"):
            for skill, weight in skills.items():
                session.run("""
                    MATCH (r:Role {roleName: $role}), (s:Skill {skillName: $skill})
                    MERGE (r)-[rel:ROLE_REQUIRES_SKILL]->(s)
                    SET rel.importance = $importance
                """, role=role, skill=skill, importance=round(weight, 2))


# ------------------- RUN ALL -------------------

insert_nodes()
insert_edges()

print(" All nodes and relationships inserted into your Neo4j AuraDB!")

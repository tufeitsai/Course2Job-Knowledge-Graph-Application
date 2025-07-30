import streamlit as st
import fitz  # PyMuPDF
import json
import requests
from neo4j import GraphDatabase

# -------------------- NEO4J CONFIG --------------------
NEO4J_URI = "neo4j+s://9ea9d411.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "lW2dXVTTyJE_xI30dyV-AxsoeD7HMn-VP23wTw0JFfI"
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# -------------------- GROQ CONFIG --------------------
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-8b-8192"

# -------------------- PDF EXTRACT --------------------
def extract_text_from_pdf(uploaded_file):
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        text = "\n".join(page.get_text() for page in doc)
    return text

# -------------------- GROQ EXTRACTION --------------------
def extract_keywords_with_groq(text):
    prompt = f"""
From the following resume text, extract only technical and professional skill keywords.
Return them in a comma-separated format, no duplicates, no explanation, no bullet points, no grouping.

Resume:
{text}
"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 250
    }
    response = requests.post(GROQ_API_URL, headers=headers, data=json.dumps(body))
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"]

# -------------------- Load Skill Mapping --------------------
@st.cache_data(show_spinner=False)
def load_skill_mapping():
    with open("three_sources_skills_clusters_1_cleaned.json", "r") as f:
        return json.load(f)

# -------------------- Skill Mapper --------------------
def map_to_course_skills(unmatched_skills, mapping):
    representative_skills = set()
    lower_unmatched = [s.lower() for s in unmatched_skills]
    for entry in mapping.values():
        rep = entry["representative"]
        if any(s in [m.lower() for m in entry["members"]] for s in lower_unmatched):
            representative_skills.add(rep)
    return list(representative_skills)

# -------------------- NEO4J QUERIES --------------------
def match_jobs_from_skills_neo4j(skills):
    with driver.session() as session:
        result = session.run("""
        MATCH (j:Job)-[:HAS_ORIGINAL_TECH]->(s:OriginalSkill)
        WHERE toLower(s.name) IN $skills
        WITH j, COLLECT(DISTINCT s.name) AS matched_skills, COUNT(DISTINCT s) AS overlap
        RETURN j, matched_skills, overlap
        ORDER BY overlap DESC
        LIMIT 50
        """, skills=[s.lower() for s in skills])

        matches = []
        for record in result:
            job_node = record["j"]
            matches.append({
                "overlap": record["overlap"],
                "job": job_node,
                "matched_skills": record["matched_skills"]
            })
        return matches

@st.cache_data(show_spinner=False)
def fetch_all_skills():
    with driver.session() as session:
        result = session.run("MATCH (s:OriginalSkill) RETURN DISTINCT s.name AS name ORDER BY name")
        return [record["name"] for record in result]

def get_courses_by_skills(mapped_skills):
    with driver.session() as session:
        result = session.run("""
        MATCH (c:Course)-[:TEACHES_SKILL]->(s:Skill)
        WHERE toLower(s.skillName) IN $skills
        RETURN DISTINCT c.courseNum AS courseNum, c.courseName AS courseName,
               COLLECT(DISTINCT s.skillName) AS skills
        ORDER BY courseNum
        LIMIT 10
        """, skills=[s.lower() for s in mapped_skills])
        return [f"{r['courseNum']} - {r['courseName']} ({', '.join(r['skills'])})" for r in result]

# -------------------- STREAMLIT UI --------------------
st.set_page_config(page_title="Resume Matcher with Courses", layout="wide")
st.title("\U0001F4C4 Resume/Skills to Job Explorer")

option = st.radio("Choose input method:", ["\U0001F4C4 Upload Resume", "⌨️ Manually Type Skills"])

if "matches" not in st.session_state:
    st.session_state.matches = []
if "page" not in st.session_state:
    st.session_state.page = 0
if "extracted_skills" not in st.session_state:
    st.session_state.extracted_skills = ""

skill_mapping = load_skill_mapping()

if option == "\U0001F4C4 Upload Resume":
    uploaded_file = st.file_uploader("Upload your resume (PDF only):", type="pdf")
    if uploaded_file and st.button("Extract Skills and Match Jobs"):
        resume_text = extract_text_from_pdf(uploaded_file)
        with st.spinner("Calling Groq LLM to extract keywords..."):
            try:
                extracted = extract_keywords_with_groq(resume_text)
                skills = [s.strip() for s in extracted.split(",") if s.strip()]
                st.session_state.extracted_skills = ", ".join(skills)
                st.session_state.matches = match_jobs_from_skills_neo4j(skills)
                st.session_state.page = 0
            except Exception as e:
                st.error(f"❌ Error: {e}")

elif option == "⌨️ Manually Type Skills":
    all_skills = fetch_all_skills()
    selected_skills = st.multiselect("Type or select your skills:", options=all_skills)
    if selected_skills and st.button("Match Jobs"):
        st.session_state.extracted_skills = ", ".join(selected_skills)
        st.session_state.matches = match_jobs_from_skills_neo4j(selected_skills)
        st.session_state.page = 0

if st.session_state.extracted_skills:
    st.subheader("✅ Extracted Skills:")
    st.code(st.session_state.extracted_skills)

if st.session_state.matches:
    st.subheader("📋 Matched Jobs")
    per_page = 10
    page = st.session_state.page
    total = len(st.session_state.matches)
    total_pages = (total - 1) // per_page + 1

    for match in st.session_state.matches[page * per_page:(page + 1) * per_page]:
        job = match["job"]
        matched = match["matched_skills"]
        all_skills = [s.lower() for s in matched]

        with driver.session() as session:
            job_result = session.run("""
            MATCH (j:Job {index: $index})-[:HAS_ORIGINAL_TECH]->(s:OriginalSkill)
            RETURN DISTINCT toLower(s.name) AS skill
            """, index=job["index"])
            job_skills = [r["skill"] for r in job_result]

        unmatched = list(set(job_skills) - set(all_skills))
        mapped_skills = map_to_course_skills(unmatched, skill_mapping)
        extra_courses = get_courses_by_skills(mapped_skills)

        with st.expander(f"{job.get('jobTitle', 'No Title')} — Matches: {match['overlap']}"):
            # st.write(f"**Company:** {job.get('Company')}")
            st.write(f"**Location:** {job.get('jobLocation')}")
            st.write(f"**Work Type:** {job.get('employmentType')}")
            st.write(f"**Matched Skills:** {', '.join(matched)}")
            if extra_courses:
                st.write("**Potential Courses That Teach Skills Needed for This Position:**")
                for course in extra_courses:
                    st.markdown(f"- {course}")
            st.write(f"**Full Description:** {job.get('jobDescription')}")
            if job.get("url"):
                st.markdown(f"[🔗 Job Link]({job['url']})")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if page > 0 and st.button("⬅️ Previous"):
            st.session_state.page -= 1
    with col3:
        if (page + 1) * per_page < total and st.button("Next ➡️"):
            st.session_state.page += 1
    with col2:
        st.markdown(f"<center>Page {page + 1} of {total_pages}</center>", unsafe_allow_html=True)

driver.close()
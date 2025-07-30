import streamlit as st
from neo4j import GraphDatabase
import time

# ----------- Neo4j AuraDB Connection -----------
NEO4J_URI = "neo4j+s://9ea9d411.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "lW2dXVTTyJE_xI30dyV-AxsoeD7HMn-VP23wTw0JFfI"
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# ----------- Graph Stats -----------
@st.cache_data(show_spinner=False)
def get_graph_stats():
    with driver.session() as session:
        result = session.run("""
            MATCH (c:Course)
            WITH count(c) AS courseCount
            MATCH (s:Skill)
            WITH courseCount, count(s) AS skillCount
            MATCH (j:Job)
            RETURN courseCount, skillCount, count(j) AS jobCount
        """)
        record = result.single()
        return record["courseCount"], record["skillCount"], record["jobCount"]

# Get the numbers BEFORE displaying them
course_target, skill_target, job_target = get_graph_stats()


# ----------- Page Setup -----------
st.set_page_config(page_title="USC Career Matcher", layout="centered")

# ----------- Disable Chrome Auto Dark Mode -----------
st.markdown("""
    <style>
        :root {
            color-scheme: light;
        }

        body {
            background-color: white !important;
            color: #333 !important;
        }

        html, body, .block-container {
            background-color: white !important;
            color: #333 !important;
        }

        div[data-testid="stAppViewContainer"] {
            background-color: white !important;
        }

        /* Ensure injected HTML also uses light mode */
        * {
            background-color: inherit !important;
            color: inherit !important;
        }
    </style>
""", unsafe_allow_html=True)



# ----------- Custom CSS -----------
st.markdown("""
    <style>
        .big-button {
            display: block;
            text-align: center;
            background-color: #f5f5f5;
            border-radius: 15px;
            padding: 2rem 1rem;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            text-decoration: none;
            font-size: 1.2rem;
            font-weight: 500;
            color: black;
            transition: 0.3s ease;
        }
        .big-button:hover {
            background-color: #e0f7ff;
            transform: translateY(-3px);
        }
        .emoji {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# ----------- Title and Team Info -----------
st.markdown("<h1 style='text-align:center;'> ✌️USC Mission Adimission</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center;'> DSCI-558 Knowledge Graph Final Project</h4>", unsafe_allow_html=True)
st.markdown("<h6 style='text-align:center;'> Team Members: Xintong Jiang, Shuijing Zhang, Tufei Cai</h6>", unsafe_allow_html=True)
st.markdown("## ")

# ----------- Divider -----------
st.markdown("""
<hr style='border: 1px solid #eee; margin: 2rem auto; width: 90%;'>
""", unsafe_allow_html=True)


# ----------- Project Summary and Description -----------
st.markdown(f"""
<div style='
    background-color: #ffffff;
    padding: 2rem;
    border-radius: 12px;
    text-align: center;
    font-size: 18px;
    line-height: 1.8;
    max-width: 850px;
    margin: auto;
    color: #333;
'>
    <p style="font-size: 20px;"><strong>🚀 Empowering USC Students with Smarter Career Planning</strong></p>
    <p>This project uses a knowledge graph to connect USC courses, technical skills, and job roles — helping CS and DS students make informed academic and career decisions.</p>
    <br>
    <p style="font-size: 20px;"><strong>📊 Our knowledge graph contains:</strong></p>
    <p>📚 Hundreds of USC courses</p>
    <p>💡 Thousands of technical skills</p>
    <p>💼 A wide range of real-world job opportunities</p>
</div>
""", unsafe_allow_html=True)

st.markdown("## ")


# ----------- Animated Graph Counters -----------
course_target, skill_target, job_target = get_graph_stats()
col1, col2, col3 = st.columns(3)

with col1:
    counter = st.empty()
    for i in range(0, course_target + 1, max(1, course_target // 50)):
        counter.markdown(f"<h3 style='text-align:center;'>📚<br>{i}<br><span style='font-size:16px;'>Courses</span></h3>", unsafe_allow_html=True)
        time.sleep(0.01)

with col2:
    counter = st.empty()
    for i in range(0, skill_target + 1, max(1, skill_target // 50)):
        counter.markdown(f"<h3 style='text-align:center;'>💡<br>{i}<br><span style='font-size:16px;'>Skills</span></h3>", unsafe_allow_html=True)
        time.sleep(0.01)

with col3:
    counter = st.empty()
    for i in range(0, job_target + 1, max(1, job_target // 50)):
        counter.markdown(f"<h3 style='text-align:center;'>💼<br>{i}<br><span style='font-size:16px;'>Jobs</span></h3>", unsafe_allow_html=True)
        time.sleep(0.01)

# ----------- Divider -----------
st.markdown("""
<hr style='border: 1px solid #eee; margin: 2rem auto; width: 90%;'>
""", unsafe_allow_html=True)

# ----------- User Guidance Section -----------
st.markdown("""
<div style='
    background-color: #ffffff;
    padding: 2rem;
    border-radius: 12px;
    text-align: center;
    font-size: 18px;
    line-height: 1.6;
    max-width: 850px;
    margin: auto;
    color: #333;
'>
    <p>📘 <strong>If you're a new student</strong>, start with <strong>Role ➡️ Courses</strong> to explore which courses you should take for your dream career.</p>
    <p>🎓 <strong>If you've taken some classes</strong>, try <strong>Courses ➡️ Jobs</strong> to discover job roles aligned with your coursework.</p>
    <p>🚀 <strong>If you have strong project experience or a resume</strong>, use <strong>Skills ➡️ Jobs</strong> for the most accurate and personalized job recommendations.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("## ")



# ----------- Function Buttons -----------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <a href="/role_to_courses" target="_self" style="text-decoration: none;">
        <div class="big-button">
            <div class="emoji">📄</div>
            <div>Role ➡️ Courses</div>
            <div style="font-size: 0.9rem; color: #666;">Tell Us Your Desired Roles</div>
        </div>
    </a>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <a href="/courses_to_jobs" target="_self" style="text-decoration: none;">
        <div class="big-button">
            <div class="emoji">📚</div>
            <div>Courses ➡️ Jobs</div>
            <div style="font-size: 0.9rem; color: #666;">Enter the courses you took</div>
        </div>
    </a>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <a href="/skills_to_jobs" target="_self" style="text-decoration: none;">
        <div class="big-button">
            <div class="emoji">💻</div>
            <div>Skills ➡️ Jobs</div>
            <div style="font-size: 0.9rem; color: #666;">Update resume / Enter Skills</div>
        </div>
    </a>
    """, unsafe_allow_html=True)

driver.close()
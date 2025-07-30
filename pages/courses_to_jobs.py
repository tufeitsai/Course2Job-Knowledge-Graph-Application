import streamlit as st
from neo4j import GraphDatabase

# ----------- Neo4j AuraDB Connection -----------
NEO4J_URI = "neo4j+s://9ea9d411.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "lW2dXVTTyJE_xI30dyV-AxsoeD7HMn-VP23wTw0JFfI"
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# ----------- Fetch All Courses for Autocomplete -----------
@st.cache_data(show_spinner=False)
def fetch_all_courses():
    with driver.session() as session:
        result = session.run("MATCH (c:Course) RETURN DISTINCT c.courseNum AS name ORDER BY name")
        return [record["name"] for record in result]

# ----------- New Logic: Match Jobs Based on Courses -----------
def course2job(course_list):
    with driver.session() as session:
        result1 = session.run("""
            MATCH (c:Course)-[:TEACHES_SKILL]->(s:Skill)<-[:JOB_REQUIRES_SKILL]-(j:Job)
            WHERE c.courseNum IN $course_list
            WITH s.skillName AS skillName, count(*) AS freq
            ORDER BY freq DESC
            LIMIT 20
            RETURN skillName
        """, course_list=course_list)

        top_skills = [record["skillName"] for record in result1]

        result2 = session.run("""
            UNWIND $top_skills AS skillName
            MATCH (s:Skill {skillName: skillName})<-[:JOB_REQUIRES_SKILL]-(j:Job)
            MATCH (j)-[:POSTED_BY]->(e:Employer)
            WITH j, e, collect(DISTINCT skillName) AS matchedSkills, count(DISTINCT skillName) AS skillCount
            ORDER BY skillCount DESC
            LIMIT 5
            RETURN j.jobTitle AS jobTitle, e.employerName AS employerName,
                   matchedSkills, skillCount, j.jobLocation AS jobLocation,
                   j.employmentType AS employmentType, j.jobDescription AS jobDescription, j.url AS url
        """, top_skills=top_skills)

        matches = []
        for record in result2:
            matches.append({
                "jobTitle": record["jobTitle"],
                "employerName": record["employerName"],
                "matchedSkills": record["matchedSkills"],
                "skillCount": record["skillCount"],
                "jobLocation": record.get("jobLocation"),
                "employmentType": record.get("employmentType"),
                "jobDescription": record.get("jobDescription"),
                "url": record.get("url")
            })
        return matches, top_skills

# ----------- Streamlit Page Setup -----------
st.set_page_config(page_title="Courses ➡️ Jobs", layout="wide")
st.title("📚 Courses to Jobs Explorer")

all_courses = fetch_all_courses()
selected_courses = st.multiselect("Select the USC courses you have completed:", options=all_courses)

# ----------- Match Jobs Button -----------
if selected_courses and st.button("🔍 Find Jobs Based on Courses"):
    matches, top_skills = course2job(selected_courses)
    st.session_state["course_matches"] = matches
    st.session_state["top_skills"] = top_skills
    st.session_state["page"] = 0

# ----------- Show Skills Extracted -----------
if "top_skills" in st.session_state:
    st.subheader("✅ Top Skills Taught by Selected Courses:")
    st.code(", ".join(st.session_state["top_skills"]), language="")

# ----------- Paginate Job Results -----------
if "course_matches" in st.session_state and st.session_state["course_matches"]:
    st.subheader("📋 Matched Jobs")
    per_page = 5
    page = st.session_state.get("page", 0)
    matches = st.session_state["course_matches"]
    total_pages = (len(matches) - 1) // per_page + 1

    paginated = matches[page * per_page:(page + 1) * per_page]
    for match in paginated:
        with st.expander(f"{match['jobTitle']} at {match['employerName']} — Matches: {match['skillCount']} skills"):
            st.write(f"**Location:** {match.get('jobLocation')}")
            st.write(f"**Work Type:** {match.get('employmentType')}")
            st.write(f"**Matched Skills:** {', '.join(match['matchedSkills'])}")
            st.write(f"**Full Description:** {match.get('jobDescription')}")
            if match.get("url"):
                st.markdown(f"[🔗 Job Link]({match['url']})")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if page > 0 and st.button("⬅️ Previous"):
            st.session_state["page"] -= 1
    with col3:
        if (page + 1) * per_page < len(matches) and st.button("Next ➡️"):
            st.session_state["page"] += 1
    with col2:
        st.markdown(f"<center>Page {page + 1} of {total_pages}</center>", unsafe_allow_html=True)

driver.close()

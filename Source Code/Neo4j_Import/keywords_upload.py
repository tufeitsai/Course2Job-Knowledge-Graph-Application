from neo4j import GraphDatabase
import json
from tqdm import tqdm

# Cloud Neo4j config
NEO4J_URI = "neo4j+s://9ea9d411.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "lW2dXVTTyJE_xI30dyV-AxsoeD7HMn-VP23wTw0JFfI"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def safe_list(x):
    return x if isinstance(x, list) else []

def is_valid(val):
    return val is not None and isinstance(val, str) and val.strip() != ""

def create_job_keywords(tx, job_index, technologies, experiences, skills, domains):
    query_parts = []
    params = {"job_index": job_index}

    for i, tech in enumerate(technologies):
        query_parts.append(f"""
            MERGE (t{i}:OriginalSkill {{name: $tech{i}}})
            WITH t{i}
            MATCH (j:Job {{index: $job_index}})
            MERGE (j)-[:HAS_ORIGINAL_TECH]->(t{i})
        """)
        params[f"tech{i}"] = tech

    for i, exp in enumerate(experiences):
        query_parts.append(f"""
            MERGE (e{i}:Experience {{level: $exp{i}}})
            WITH e{i}
            MATCH (j:Job {{index: $job_index}})
            MERGE (j)-[:HAS_EXPERIENCE]->(e{i})
        """)
        params[f"exp{i}"] = exp

    for i, skill in enumerate(skills):
        query_parts.append(f"""
            MERGE (s{i}:SoftSkill {{name: $skill{i}}})
            WITH s{i}
            MATCH (j:Job {{index: $job_index}})
            MERGE (j)-[:HAS_SOFT_SKILL]->(s{i})
        """)
        params[f"skill{i}"] = skill

    for i, domain in enumerate(domains):
        query_parts.append(f"""
            MERGE (d{i}:OriginalDomain {{name: $domain{i}}})
            WITH d{i}
            MATCH (j:Job {{index: $job_index}})
            MERGE (j)-[:HAS_ORIGINAL_DOMAIN]->(d{i})
        """)
        params[f"domain{i}"] = domain

    if query_parts:
        tx.run("\n".join(query_parts), **params)

def import_mapped_data(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)

    with driver.session() as session:
        for entry in tqdm(data, desc=" Importing Keywords"):
            job_index = entry.get("index")
            if job_index is None:
                continue

            techs = [t.strip() for t in safe_list(entry.get("Technologies")) if is_valid(t)]
            exps = [e.strip() for e in safe_list(entry.get("Required Experience")) if is_valid(e) and not isinstance(e, dict)]
            skills = [s.strip() for s in safe_list(entry.get("Required Skills")) if is_valid(s)]
            domains = [d.strip() for d in safe_list(entry.get("Job Domains")) if is_valid(d)]

            session.execute_write(create_job_keywords, int(job_index), techs, exps, skills, domains)

    print("🎉 All keywords processed and linked!")

# Run the import
import_mapped_data("Clusted_technologies_keywords.json")
driver.close()

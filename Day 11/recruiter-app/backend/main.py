from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from parser import extract_text, extract_email, extract_skills, extract_name, extract_jd_info
from matcher import calculate_match
from memory import memory
from llm import evaluate_interview, generate_offer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- STEP 1 ----------------
@app.post("/upload-jd")
async def upload_jd(file: UploadFile = File(...)):
    text = extract_text(file)

    memory["jd"] = extract_jd_info(text)
    memory["step"] = 2

    return {
        "message": "JD processed. Upload resumes.",
        "jd": memory["jd"]
    }

# ---------------- STEP 2 ----------------
@app.post("/upload-resumes")
async def upload_resumes(files: list[UploadFile] = File(...)):
    
    memory["candidates"] = []  # ✅ reset

    results = []

    for file in files:
        text = extract_text(file)

        name = extract_name(text)
        email = extract_email(text)
        skills = extract_skills(text)

        match = calculate_match(skills, memory["jd"])

        candidate = {
            "name": name,
            "email": email,
            "skills": skills,
            "match": match
        }

        memory["candidates"].append(candidate)
        results.append(candidate)

    memory["step"] = 3
    return results

# ---------------- STEP 3 ----------------
@app.post("/filter")
def filter_candidates(threshold: int):
    filtered = [c for c in memory["candidates"] if c["match"] >= threshold]
    memory["filtered_candidates"] = filtered
    memory["step"] = 4
    return filtered

from pydantic import BaseModel

class Approval(BaseModel):
    flag: bool

@app.post("/approve")
def approve(data: Approval):
    if data.flag:
        memory["step"] = 5
        return {"message": "Provide interview Q&A"}
    else:
        memory["step"] = 1
        return {"message": "Restarting..."}

# ---------------- STEP 4 ----------------
@app.post("/approve")
def approve(flag: bool):
    if flag:
        memory["step"] = 5
        return {"message": "Provide interview Q&A"}
    else:
        memory["step"] = 1
        return {"message": "Restarting..."}

# ---------------- STEP 5 ----------------
from pydantic import BaseModel

class InterviewInput(BaseModel):
    text: str

@app.post("/evaluate")
def evaluate(data: InterviewInput):
    result = evaluate_interview(data.text)
    return {"evaluation": result}

# ---------------- STEP 6 ----------------
@app.post("/select")
def select(names: list[str]):
    selected = []

    for c in memory["filtered_candidates"]:
        if c["name"] in names:
            email = generate_offer(c["name"], memory["jd"]["job_title"])
            selected.append({
                "name": c["name"],
                "email": c["email"],
                "offer": email
            })

    memory["step"] = 1
    return selected

    
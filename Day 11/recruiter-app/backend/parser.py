import fitz
import re

def extract_text(file):
    file_bytes = file.file.read()
    pdf = fitz.open(stream=file_bytes, filetype="pdf")

    text = ""
    for page in pdf:
        text += page.get_text()

    return text


def extract_email(text):
    match = re.search(r'\S+@\S+', text)
    return match.group() if match else "Not found"


def extract_name(text):
    return text.strip().split("\n")[0]


def extract_skills(text):
    text = text.lower()

    skills_db = [
        "react","javascript","html5","css3",
        "node.js","python","git","mongodb"
    ]

    return list(set([s for s in skills_db if s in text]))


# ✅ ADD THIS HERE
def extract_jd_info(text):
    text = text.lower()

    skills_map = [
        "react","javascript","html5","css3",
        "node.js","python","git"
    ]

    required = []

    for skill in skills_map:
        if skill in text:
            required.append(skill)

    return {
        "job_title": "Full Stack Developer",
        "required_skills": list(set(required)),
        "optional_skills": []
    }
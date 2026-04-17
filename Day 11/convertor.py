import csv
import json
import re

INPUT_FILE = "./Day 11/Complaint_Dataset.csv"
OUTPUT_FILE = "./Day 11/policies.json"

def generate_keywords(trouble, category, solution, alternate_solution):
    """Extract meaningful keywords from all text fields for BM25 matching."""
    combined = f"{trouble} {category} {solution} {alternate_solution}".lower()

    # Remove punctuation
    combined = re.sub(r"[^\w\s]", " ", combined)

    # Stop words to remove
    stop_words = {
        "a", "an", "the", "is", "it", "in", "on", "at", "to", "for",
        "of", "and", "or", "with", "we", "our", "your", "can", "will",
        "be", "by", "as", "if", "up", "do", "not", "no", "so", "has",
        "was", "are", "this", "that", "have", "from", "within", "please",
        "offer", "provide", "initiate", "request", "process", "arrange",
        "issue", "assist", "within"
    }

    tokens = combined.split()
    keywords = []
    seen = set()
    for token in tokens:
        token = token.strip()
        if token and token not in stop_words and len(token) > 2 and token not in seen:
            keywords.append(token)
            seen.add(token)

    return keywords

def build_content(trouble, solution, alternate_solution, company_response, category):
    """Build a detailed content string combining all fields for LLM context."""
    return (
        f"Issue: {trouble}. "
        f"Category: {category}. "
        f"Primary resolution: {solution}. "
        f"Alternate resolution: {alternate_solution}. "
        f"Standard response: {company_response}"
    )

def convert():
    policies = []

    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, start=1):
            trouble           = row["Trouble"].strip()
            category          = row["Category"].strip()
            solution          = row["Solution"].strip()
            alternate_solution= row["Alternate Solution"].strip()
            company_response  = row["Company Response"].strip()

            if not trouble:
                continue

            policy = {
                "id":                 idx,
                "title":              trouble,
                "category":           category,
                "keywords":           generate_keywords(trouble, category, solution, alternate_solution),
                "solution":           solution,
                "alternate_solution": alternate_solution,
                "company_response":   company_response,
                "content":            build_content(trouble, solution, alternate_solution, company_response, category)
            }

            policies.append(policy)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(policies, f, indent=2, ensure_ascii=False)

    print(f"Converted {len(policies)} rows → {OUTPUT_FILE}")

    # Print category breakdown
    from collections import Counter
    cats = Counter(p["category"] for p in policies)
    print("\nCategory breakdown:")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat:<15} {count} entries")

if __name__ == "__main__":
    convert()
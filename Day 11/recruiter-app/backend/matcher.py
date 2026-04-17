def calculate_match(skills, jd):
    required = jd["required_skills"]
    optional = jd["optional_skills"]

    matched_required = len(set(skills) & set(required))
    matched_optional = len(set(skills) & set(optional))

    total_required = len(required)
    total_optional = len(optional)

    score = ((matched_required * 2) + matched_optional) / ((total_required * 2) + total_optional)
    return round(score * 100, 2)
# app/nlp/keywords.py
from sklearn.feature_extraction.text import TfidfVectorizer

def extract_keywords(reviews, top_n=5):
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(reviews)

    scores = X.sum(axis=0).A1
    words = vectorizer.get_feature_names_out()

    word_scores = list(zip(words, scores))
    sorted_words = sorted(word_scores, key=lambda x: x[1], reverse=True)

    return [w for w, _ in sorted_words[:top_n]]
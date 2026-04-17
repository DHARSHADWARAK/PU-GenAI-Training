# app/nlp/preprocess.py
import re
from nltk.corpus import stopwords

stop_words = set(stopwords.words('english'))

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)

    words = text.split()
    words = [w for w in words if w not in stop_words]

    return " ".join(words)
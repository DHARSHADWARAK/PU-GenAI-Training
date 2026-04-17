# app/nlp/sentiment.py
from transformers import pipeline

sentiment_model = pipeline("sentiment-analysis")

def get_sentiment(text, rating=None):
    result = sentiment_model(text[:512])[0]

    label = result['label']
    score = result['score']

    # base prediction
    sentiment = "positive" if label == "POSITIVE" else "negative"

    # 🔥 correction using rating
    # if rating is not None:
    #     if rating >= 4:
    #         sentiment = "positive"
    #     elif rating <= 2:
    #         sentiment = "negative"

    # 🔥 add neutral
    if score < 0.6:
        sentiment = "neutral"

    return sentiment, score
import os
from app.data.loader import load_data
from app.nlp.sentiment import get_sentiment
from app.nlp.keywords import extract_keywords

# 🔹 Absolute path (no path bugs ever again)
DATA_PATH = "../dataset/amazon_reviews.csv"


def process_products():
    df = load_data(DATA_PATH)

    products = {}

    # 🔹 Process each review
    for _, row in df.iterrows():
        name = row['name']
        review = row['reviews.text']
        rating = row['reviews.rating']

        sentiment, score = get_sentiment(review, rating)

        # 🔹 Initialize product
        if name not in products:
            products[name] = {
                "reviews": [],
                "positive": 0,
                "negative": 0,
                "neutral": 0
            }

        # 🔹 Add review
        products[name]["reviews"].append({
            "text": review,
            "sentiment": sentiment,
            "score": score
        })

        # 🔹 Increment sentiment count
        products[name][sentiment] += 1

    # 🔹 Post-processing per product
    formatted_products = {}

    for name, data in products.items():
        texts = [r["text"] for r in data["reviews"]]

        # 🔹 Extract keywords
        keywords = extract_keywords(texts)

        # 🔹 Determine overall sentiment
        if data["positive"] > data["negative"]:
            overall = "positive"
        elif data["negative"] > data["positive"]:
            overall = "negative"
        else:
            overall = "neutral"

        # 🔥 FINAL CLEAN STRUCTURE
        formatted_products[name] = {
            "product_name": name,
            "total_reviews": len(data["reviews"]),

            "sentiment_summary": {
                "positive": data["positive"],
                "negative": data["negative"],
                "neutral": data["neutral"],
                "overall": overall
            },

            "top_keywords": keywords,

            "reviews": data["reviews"]
        }

    return formatted_products


# 🔥 CACHE (VERY IMPORTANT)
PRODUCT_DATA = process_products()
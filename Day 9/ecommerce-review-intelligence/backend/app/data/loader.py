# app/data/loader.py
import pandas as pd

def load_data(path):
    df = pd.read_csv(path)

    df = df[['name', 'reviews.text', 'reviews.rating']]
    df = df.dropna()

    return df
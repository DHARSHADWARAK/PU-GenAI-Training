import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchProduct } from "../api/api";

export default function ProductDetail() {
  const { name } = useParams();
  const decodedName = decodeURIComponent(name);

  const [product, setProduct] = useState(null);

  useEffect(() => {
    fetchProduct(decodedName).then(data => setProduct(data));
  }, [decodedName]);

  if (!product) return <p>Loading...</p>;

  const summary = product.sentiment_summary;
  const total = product.total_reviews;

  return (
    <div style={{ padding: "30px", fontFamily: "Arial" }}>
      
      {/* 🔹 Title */}
      <h1 style={{ textAlign: "center", marginBottom: "30px" }}>
        {product.product_name}
      </h1>

      {/* 🔹 Layout */}
      <div style={{ display: "flex", gap: "30px" }}>
        
        {/* LEFT SIDE - REVIEWS */}
        <div style={{ flex: 2 }}>
          <h2>Reviews</h2>

          {product.reviews.map((r, i) => (
            <div
              key={i}
              style={{
                background: "#fff",
                padding: "15px",
                marginBottom: "15px",
                borderRadius: "10px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
              }}
            >
              <p style={{ lineHeight: "1.6" }}>{r.text}</p>

              <p style={{ marginTop: "10px" }}>
                <b>Sentiment:</b> {r.sentiment} ({r.score.toFixed(2)})
              </p>
            </div>
          ))}
        </div>

        {/* RIGHT SIDE */}
        <div style={{ flex: 1 }}>
          
          {/* 🔹 SENTIMENT CARD */}
          <div
            style={{
              background: "#fff",
              padding: "20px",
              borderRadius: "10px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
              marginBottom: "20px"
            }}
          >
            <h3>Sentiment</h3>

            {/* Positive */}
            <p>👍 Positive: {summary.positive}</p>
            <div style={{ background: "#eee", height: "8px" }}>
              <div
                style={{
                  width: `${(summary.positive / total) * 100}%`,
                  height: "8px",
                  background: "green"
                }}
              />
            </div>

            {/* Negative */}
            <p>👎 Negative: {summary.negative}</p>
            <div style={{ background: "#eee", height: "8px" }}>
              <div
                style={{
                  width: `${(summary.negative / total) * 100}%`,
                  height: "8px",
                  background: "red"
                }}
              />
            </div>

            {/* Neutral */}
            <p>😐 Neutral: {summary.neutral}</p>
            <div style={{ background: "#eee", height: "8px" }}>
              <div
                style={{
                  width: `${(summary.neutral / total) * 100}%`,
                  height: "8px",
                  background: "gray"
                }}
              />
            </div>

            <p style={{ marginTop: "10px" }}>
              <b>Overall:</b> {summary.overall}
            </p>
          </div>

          {/* 🔹 KEYWORDS CARD */}
          <div
            style={{
              background: "#fff",
              padding: "20px",
              borderRadius: "10px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
            }}
          >
            <h3>Keywords</h3>

            <div>
              {product.top_keywords.map((k, i) => (
                <span
                  key={i}
                  style={{
                    display: "inline-block",
                    padding: "6px 10px",
                    margin: "5px",
                    background: "#007bff",
                    color: "white",
                    borderRadius: "20px",
                    fontSize: "12px"
                  }}
                >
                  {k}
                </span>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
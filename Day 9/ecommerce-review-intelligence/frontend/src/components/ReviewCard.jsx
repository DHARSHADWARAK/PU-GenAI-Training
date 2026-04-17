export default function ReviewCard({ review }) {
{product.reviews.map((r, i) => {
  const getStyles = () => {
    if (r.sentiment === "positive") {
      return {
        background: "#e6f4ea",
        borderLeft: "5px solid #2e7d32"
      };
    }
    if (r.sentiment === "negative") {
      return {
        background: "#fdecea",
        borderLeft: "5px solid #d32f2f"
      };
    }
    return {
      background: "#fff8e1",
      borderLeft: "5px solid #f9a825"
    };
  };

  const styles = getStyles();

  return (
    <div
      key={i}
      style={{
        ...styles,
        padding: "15px",
        marginBottom: "15px",
        borderRadius: "8px",
        boxShadow: "0 2px 6px rgba(0,0,0,0.08)"
      }}
    >
      {/* 🔥 Sentiment label */}
      <div
        style={{
          fontSize: "12px",
          fontWeight: "bold",
          marginBottom: "8px",
          textTransform: "uppercase",
          color:
            r.sentiment === "positive"
              ? "#2e7d32"
              : r.sentiment === "negative"
              ? "#d32f2f"
              : "#f9a825"
        }}
      >
        {r.sentiment}
      </div>

      {/* 🔹 Review text */}
      <p style={{ lineHeight: "1.6" }}>{r.text}</p>

      {/* 🔹 Score */}
      <p style={{ marginTop: "10px", fontSize: "12px" }}>
        Confidence: {r.score.toFixed(2)}
      </p>
    </div>
  );
})}
}
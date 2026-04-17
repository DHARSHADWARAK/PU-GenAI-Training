import { useNavigate } from "react-router-dom";

export default function ProductCard({ product }) {
  const navigate = useNavigate();
  const summary = product.sentiment_summary;

  const boxStyle = (color) => ({
    padding: "6px 12px",
    borderRadius: "6px",
    color: "white",
    background: color,
    display: "inline-block",
    margin: "5px",
    fontSize: "14px"
  });

  return (
    <div
      onClick={() =>
        navigate(`/product/${encodeURIComponent(product.product_name)}`)
      }
      style={{
        border: "1px solid #ddd",
        padding: "15px",
        margin: "15px",
        borderRadius: "10px",
        boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
        cursor: "pointer", // 🔥 important
        transition: "0.2s"
      }}
    >
      <h2>{product.product_name}</h2>

      <p>Total Reviews: {product.total_reviews}</p>

      <div>
        <span style={boxStyle("green")}>
          Positive: {summary.positive}
        </span>

        <span style={boxStyle("red")}>
          Negative: {summary.negative}
        </span>

        <span style={boxStyle("gray")}>
          Neutral: {summary.neutral}
        </span>
      </div>

      <p style={{ marginTop: "10px" }}>
        <b>Overall:</b>{" "}
        <span
          style={{
            color:
              summary.overall === "positive"
                ? "green"
                : summary.overall === "negative"
                ? "red"
                : "gray"
          }}
        >
          {summary.overall}
        </span>
      </p>
    </div>
  );
}
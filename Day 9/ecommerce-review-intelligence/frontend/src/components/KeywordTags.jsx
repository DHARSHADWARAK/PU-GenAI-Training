export default function KeywordTags({ keywords }) {
  return (
    <div>
      {keywords.map((k, i) => (
        <span
          key={i}
          style={{
            margin: "5px",
            padding: "5px",
            background: "#eee",
            display: "inline-block"
          }}
        >
          {k}
        </span>
      ))}
    </div>
  );
}
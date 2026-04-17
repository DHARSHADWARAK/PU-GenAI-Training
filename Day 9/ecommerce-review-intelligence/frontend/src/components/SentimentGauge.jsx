import { PieChart, Pie, Cell } from "recharts";

export default function SentimentGauge({ positive, negative, neutral }) {
  const total = positive + negative + neutral;

  const score = (positive / total) * 100;

  const data = [
    { name: "Negative", value: negative, color: "#ff4d4d" },
    { name: "Neutral", value: neutral, color: "#999" },
    { name: "Positive", value: positive, color: "#4caf50" }
  ];

  return (
    <div style={{ textAlign: "center" }}>
      <PieChart width={250} height={150}>
        <Pie
          data={data}
          startAngle={180}
          endAngle={0}
          innerRadius={50}
          outerRadius={80}
          paddingAngle={2}
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={index} fill={entry.color} />
          ))}
        </Pie>
      </PieChart>

      {/* 🔥 Score */}
      <h2 style={{ marginTop: "-10px" }}>
        {score.toFixed(1)}%
      </h2>

      <p>Positive Score</p>
    </div>
  );
}
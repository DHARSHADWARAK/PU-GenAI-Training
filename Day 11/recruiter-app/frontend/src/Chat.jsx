import React, { useState } from "react";
import { uploadJD, uploadResumes } from "./api";

export default function Chat() {
  const [messages, setMessages] = useState([
    { role: "bot", text: "Hello! Please upload Job Description (JD)." }
  ]);

  const [step, setStep] = useState(1);
  const [input, setInput] = useState("");

  // STEP 1
  const handleJD = async (file) => {
    const res = await uploadJD(file);

    setMessages(prev => [
      ...prev,
      { role: "user", text: "Uploaded JD" },
      { role: "bot", text: res.message }
    ]);

    setStep(2);
  };

  // STEP 2
  const handleResumes = async (files) => {
    const res = await uploadResumes(files);

    setMessages(prev => [
      ...prev,
      { role: "user", text: "Uploaded resumes" },
      {
        role: "bot",
        text: res.map(c => `${c.name} - ${c.match}%`).join("\n")
      },
      { role: "bot", text: "Enter threshold (e.g., 70)" }
    ]);

    setStep(3);
  };

  // STEP 3
  const handleThreshold = async () => {
    const res = await fetch(
      `http://localhost:8000/filter?threshold=${input}`,
      { method: "POST" }
    ).then(r => r.json());

    setMessages(prev => [
      ...prev,
      { role: "user", text: input },
      {
        role: "bot",
        text: res.map(c => `${c.name} - ${c.match}%`).join("\n")
      },
      { role: "bot", text: "Approve candidates? (Yes/No)" }
    ]);

    setInput("");
    setStep(4);
  };

  // STEP 4
  const handleApprove = async (flag) => {
    const res = await fetch("http://localhost:8000/approve", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ flag })
    }).then(r => r.json());

    setMessages(prev => [
      ...prev,
      { role: "user", text: flag ? "Yes" : "No" },
      { role: "bot", text: res.message }
    ]);

    if (flag) setStep(5);
    else setStep(1);
  };

  // STEP 5
const handleInterview = async () => {
  const res = await fetch("http://localhost:8000/evaluate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      text: input   // ✅ MUST be wrapped like this
    })
  }).then(r => r.json());

  setMessages(prev => [
    ...prev,
    { role: "user", text: input },
    { role: "bot", text: res.evaluation || JSON.stringify(res) },
    { role: "bot", text: "Enter selected candidate names (comma separated)" }
  ]);

  setInput("");
  setStep(6);
};
  // STEP 6
  const handleSelection = async () => {
    const names = input.split(",").map(n => n.trim());

    const res = await fetch("http://localhost:8000/select", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(names)
    }).then(r => r.json());

    setMessages(prev => [
      ...prev,
      { role: "user", text: input },
      {
        role: "bot",
        text: res.map(c => `${c.name} selected\n${c.offer}`).join("\n\n")
      },
      { role: "bot", text: "Process complete. Starting again..." }
    ]);

    setInput("");
    setStep(1);
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Recruiter Bot</h2>

      {/* CHAT */}
      <div>
        {messages.map((m, i) => (
          <div key={i}>
            <b>{m.role}:</b>
            <pre>{m.text}</pre>
          </div>
        ))}
      </div>

      <br />

      {/* STEP INPUTS */}

      {step === 1 && (
        <input type="file" onChange={(e) => handleJD(e.target.files[0])} />
      )}

      {step === 2 && (
        <input type="file" multiple onChange={(e) => handleResumes([...e.target.files])} />
      )}

      {step === 3 && (
        <div>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter threshold"
          />
          <button onClick={handleThreshold}>Submit</button>
        </div>
      )}

      {step === 4 && (
        <div>
          <button onClick={() => handleApprove(true)}>Yes</button>
          <button onClick={() => handleApprove(false)}>No</button>
        </div>
      )}

      {step === 5 && (
        <div>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Paste interview Q&A"
          />
          <button onClick={handleInterview}>Submit</button>
        </div>
      )}

      {step === 6 && (
        <div>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter names (comma separated)"
          />
          <button onClick={handleSelection}>Submit</button>
        </div>
      )}
    </div>
  );
}
import React from "react";

const MODES = [
  {
    value: "strict",
    label: "Strict policy",
    description: "Uses the low-creativity policy prompt from Scenario A.",
  },
  {
    value: "friendly",
    label: "Friendly tone",
    description: "Uses the more empathetic customer-facing prompt from Scenario B.",
  },
];

function ModeSelector({ value, onChange, disabled }) {
  const selectedMode = MODES.find((mode) => mode.value === value) || MODES[0];

  return (
    <label className="field-group">
      <span className="field-label">Mode</span>
      <select
        className="mode-select"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
      >
        {MODES.map((mode) => (
          <option key={mode.value} value={mode.value}>
            {mode.label}
          </option>
        ))}
      </select>
      <span className="field-help">{selectedMode.description}</span>
    </label>
  );
}

export default ModeSelector;

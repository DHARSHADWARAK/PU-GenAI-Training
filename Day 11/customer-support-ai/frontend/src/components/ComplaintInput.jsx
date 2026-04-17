import React from "react";

function ComplaintInput({ value, onChange, disabled }) {
  return (
    <label className="field-group">
      <span className="field-label">Customer complaint</span>
      <textarea
        className="complaint-input"
        rows="6"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Describe the customer issue here..."
        disabled={disabled}
      />
    </label>
  );
}

export default ComplaintInput;

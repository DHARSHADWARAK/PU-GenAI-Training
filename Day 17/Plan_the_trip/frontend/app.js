const API_BASE_URL = "http://127.0.0.1:8000";

const agents = [
  "Input",
  "Memory",
  "Weather",
  "Transport",
  "Hotel",
  "Places",
  "Budget",
  "Itinerary",
  "Review",
  "PDF",
];

const form = document.querySelector("#tripForm");
const submitButton = document.querySelector("#submitButton");
const apiStatus = document.querySelector("#apiStatus");
const agentStrip = document.querySelector("#agentStrip");
const resultTitle = document.querySelector("#resultTitle");
const pdfLink = document.querySelector("#pdfLink");

function initializeAgents() {
  agentStrip.innerHTML = agents
    .map((agent) => `<span class="agent-chip" data-agent="${agent}">${agent}</span>`)
    .join("");
}

function markAgentsDone() {
  document.querySelectorAll(".agent-chip").forEach((chip) => chip.classList.add("done"));
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? "Planning trip..." : "Generate trip plan";
  if (isLoading) {
    document.querySelectorAll(".agent-chip").forEach((chip) => chip.classList.remove("done"));
    resultTitle.textContent = "Agents are planning your trip";
  }
}

function formToPayload(formData) {
  const preferences = String(formData.get("preferences") || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  return {
    source: formData.get("source"),
    destination: formData.get("destination"),
    start_date: formData.get("start_date"),
    end_date: formData.get("end_date"),
    budget: Number(formData.get("budget")),
    currency: formData.get("currency"),
    travellers: Number(formData.get("travellers")),
    preferences,
    pace: formData.get("pace"),
    user_id: formData.get("user_id"),
  };
}

function money(currency, value) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return "N/A";
  return `${currency || ""} ${Number(value).toLocaleString()}`.trim();
}

function setList(elementId, items, formatter = (item) => item) {
  const element = document.querySelector(`#${elementId}`);
  element.innerHTML = "";
  if (!items || !items.length) {
    element.innerHTML = "<li>No details returned.</li>";
    return;
  }
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = formatter(item);
    element.appendChild(li);
  });
}

function renderPlan(plan) {
  const prefs = plan.trip_preferences || {};
  const currency = prefs.currency || "INR";
  const weather = plan.weather_data || {};
  const transport = plan.transport_data || {};
  const hotel = (plan.hotel_data || {}).selected || {};
  const budget = plan.budget_summary || {};
  const itinerary = plan.itinerary || {};
  const review = plan.review_status || {};

  document.querySelector("#routeSource").textContent = prefs.source || "Source";
  document.querySelector("#routeDestination").textContent = prefs.destination || "Destination";
  resultTitle.textContent = itinerary.title || `${prefs.destination || "Trip"} plan`;

  document.querySelector("#weatherSummary").textContent =
    `${weather.summary || "Weather unavailable"}${weather.temperature_c ? `, ${weather.temperature_c} C` : ""}. Source: ${weather.source || "unknown"}.`;
  document.querySelector("#transportSummary").textContent =
    `${transport.summary || "Transport unavailable"} Estimated cost: ${money(currency, transport.estimated_cost)}.`;
  document.querySelector("#hotelSummary").textContent =
    `${hotel.name || "Hotel unavailable"} at ${money(currency, hotel.price_per_night)} per night. Rating: ${hotel.rating || "N/A"}.`;
  document.querySelector("#budgetSummary").textContent =
    `${budget.status || "unknown"}. Estimated total: ${money(currency, budget.estimated_total)}. Remaining: ${money(currency, budget.remaining)}.`;

  const itineraryList = document.querySelector("#itineraryList");
  itineraryList.innerHTML = "";
  (itinerary.days || []).forEach((day) => {
    const item = document.createElement("article");
    item.className = "day-item";
    item.innerHTML = `
      <h4>Day ${day.day || ""} ${day.date ? `- ${day.date}` : ""}</h4>
      <p><strong>Morning:</strong> ${day.morning || ""}</p>
      <p><strong>Afternoon:</strong> ${day.afternoon || ""}</p>
      <p><strong>Evening:</strong> ${day.evening || ""}</p>
    `;
    itineraryList.appendChild(item);
  });
  if (!itineraryList.children.length) {
    itineraryList.innerHTML = '<p class="empty-state">No itinerary generated.</p>';
  }

  setList("placesList", (plan.places_data || {}).places || [], (place) => `${place.name || "Place"}${place.category ? ` - ${place.category}` : ""}`);
  setList("reviewList", review.issues && review.issues.length ? review.issues : ["Approved by final review agent"], (item) => item);

  if (plan.pdf_link) {
    pdfLink.href = plan.pdf_link;
    pdfLink.textContent = "Open PDF report";
    pdfLink.classList.remove("disabled");
    pdfLink.classList.add("ready");
  } else {
    pdfLink.href = "#";
    pdfLink.textContent = "PDF unavailable";
    pdfLink.classList.add("disabled");
    pdfLink.classList.remove("ready");
  }

  markAgentsDone();
}

async function checkApi() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) throw new Error("Health check failed");
    apiStatus.textContent = "API online";
    apiStatus.className = "status-pill ok";
  } catch {
    apiStatus.textContent = "API offline";
    apiStatus.className = "status-pill error";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setLoading(true);
  try {
    const payload = formToPayload(new FormData(form));
    const response = await fetch(`${API_BASE_URL}/plan-trip`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Trip planning failed");
    }
    renderPlan(data);
  } catch (error) {
    resultTitle.textContent = "Trip planning failed";
    document.querySelector("#reviewList").innerHTML = `<li>${error.message}</li>`;
  } finally {
    setLoading(false);
  }
});

initializeAgents();
checkApi();

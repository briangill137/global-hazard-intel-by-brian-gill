const events = [
  {
    title: "Saharan Dust Transport",
    severity: "High",
    region: "North Africa -> Southern Europe",
    summary: "Aerosol density and transport winds indicate a cross-border dust event."
  },
  {
    title: "Western Wildfire Smoke",
    severity: "High",
    region: "California -> Nevada",
    summary: "Thermal anomalies and PM2.5 spikes indicate smoke plume expansion."
  },
  {
    title: "Industrial Chemical Alert",
    severity: "Medium",
    region: "Gulf Coast",
    summary: "Localized gas anomaly suggests elevated industrial release risk."
  }
];

function renderEvents() {
  const container = document.getElementById("events");
  container.innerHTML = "";

  events.forEach((event) => {
    const card = document.createElement("article");
    card.className = "event";
    card.innerHTML = `
      <strong>${event.title}</strong>
      <span class="badge ${event.severity.toLowerCase()}">${event.severity}</span>
      <p>${event.region}</p>
      <p>${event.summary}</p>
    `;
    container.appendChild(card);
  });
}

document.getElementById("refresh").addEventListener("click", renderEvents);
renderEvents();

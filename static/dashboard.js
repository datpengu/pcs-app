const fields = ["inside", "entered", "exited"];
const status = document.querySelector("#status");
const history = document.querySelector("#history");

async function refreshStats() {
  try {
    const response = await fetch("/api/stats", { cache: "no-store" });
    const stats = await response.json();
    fields.forEach((field) => document.querySelector(`#${field}`).textContent = stats[field]);
    status.textContent = stats.status === "running" ? "Camera online" : stats.status.replace("_", " ");
    status.dataset.state = stats.status;
  } catch { status.textContent = "API unavailable"; status.dataset.state = "error"; }
}

async function refreshHistory() {
  const response = await fetch("/api/history", { cache: "no-store" });
  const { days } = await response.json();
  history.replaceChildren(...days.map((day) => {
    const item = document.createElement("li");
    item.textContent = `${day.date}: ${day.entered} entered, ${day.exited} exited`;
    return item;
  }));
  if (!days.length) history.innerHTML = "<li>No crossings recorded yet.</li>";
}

refreshStats(); refreshHistory();
setInterval(refreshStats, 1000);
setInterval(refreshHistory, 30000);

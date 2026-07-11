"use strict";

const DATABASES = {
  jobs: "jobs.json",
  contacts: "contacts.json",
  coachNetwork: "coach_network.json",
  countries: "countries.json",
  licences: "pro_licence_watch.json"
};

const state = { jobs: [], contacts: [], coachNetwork: [], countries: [], licences: [] };
const text = (value) => {
  if (Array.isArray(value)) return value.join(", ");
  return value === undefined || value === null || value === "" ? "To verify" : String(value);
};
const safeUrl = (value) => /^https?:\/\//i.test(text(value)) ? text(value) : "";
const escapeHtml = (value) => text(value).replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
}[char]));
const badgeClass = (value) => {
  const normalized = text(value).toLowerCase();
  if (normalized.includes("very high") || normalized === "high" || normalized === "open") return "hot";
  if (normalized.includes("verified") && !normalized.includes("to verify")) return "good";
  return "neutral";
};
const row = (label, value, link = false) => {
  const url = link && safeUrl(value);
  const rendered = url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener">Open source</a>` : escapeHtml(value);
  return `<div class="detail-row"><dt>${escapeHtml(label)}</dt><dd>${rendered}</dd></div>`;
};
const details = (rows) => `<details><summary>View Details</summary><dl>${rows.join("")}</dl></details>`;
const card = ({ label, title, meta = "", badges = [], body = "", rows = [] }) => `
  <article class="card">
    <div class="card-top"><span class="label">${escapeHtml(label)}</span>${badges.map((item) => `<span class="badge ${badgeClass(item)}">${escapeHtml(item)}</span>`).join("")}</div>
    <h3>${escapeHtml(title)}</h3>
    ${meta ? `<p class="meta">${escapeHtml(meta)}</p>` : ""}
    ${body ? `<p>${escapeHtml(body)}</p>` : ""}
    ${rows.length ? details(rows) : ""}
  </article>`;

function renderDashboard() {
  const asiaCountries = state.countries.filter((item) => item.continent === "Asia" && item.confederation === "AFC");
  const headCoachWatch = asiaCountries.filter((item) =>
    ["High", "Medium"].includes(item.afcAHeadCoachPossibility)
  );
  const coachUpdates = state.coachNetwork.filter((item) =>
    item.person !== "To verify" && item.accuracyLevel !== "To verify"
  );
  const contactsToVerify = state.contacts.filter((item) =>
    item.accuracyLevel === "To verify" || item.email === "To verify"
  );
  const stats = [
    ["Asia Countries Tracked", asiaCountries.length, "AFC markets"],
    ["AFC A Head Coach Watch", headCoachWatch.length, "High and medium possibility"],
    ["Pro Licence Watch", state.licences.length, "AFC and nearby OFC"],
    ["Coach Network Updates", coachUpdates.length, "Non-placeholder records"],
    ["Contacts To Verify", contactsToVerify.length, "Research queue"]
  ];
  document.querySelector("#dashboardGrid").innerHTML = stats.map(([name, value, note]) =>
    `<article class="stat-card"><span>${escapeHtml(name)}</span><strong>${value}</strong><small>${escapeHtml(note)}</small></article>`
  ).join("");
  const actions = state.jobs.filter((item) => text(item.status).toLowerCase() === "open").slice(0, 2).map(jobCard);
  actions.push(card({ label: "Licence", title: "Review application windows", meta: "Pro Licence Watch", body: "Confirm foreign applicant rules and AFC A Licence recognition with priority associations." }));
  document.querySelector("#actionGrid").innerHTML = actions.join("");
}

function jobCard(item) {
  return card({
    label: item.roleType, title: item.position,
    meta: `${item.country} · ${item.organization}`,
    badges: [item.priority, item.status],
    body: item.shortSummary,
    rows: [
      row("Deadline", item.deadline), row("Team", item.teamType), row("Licence", item.licenceRequirement),
      row("Application", item.applicationMethod), row("Contact", `${item.contactPerson} · ${item.contactEmail}`),
      row("Fit score", item.fitScore), row("Fit reason", item.fitReason),
      row("Recommended action", item.recommendedAction), row("Details", item.details),
      row("Source", item.sourceUrl, true), row("Last checked", item.lastChecked), row("Notes", item.notes)
    ]
  });
}

function renderJobs() {
  document.querySelector("#jobsCount").textContent = `${state.jobs.length} records`;
  document.querySelector("#jobsGrid").innerHTML = state.jobs.map(jobCard).join("") || emptyState("No jobs recorded.");
}

function renderContacts() {
  document.querySelector("#contactsCount").textContent = `${state.contacts.length} records`;
  document.querySelector("#contactsGrid").innerHTML = state.contacts.map((item) => card({
    label: item.type, title: item.organization, meta: `${item.country} · ${item.role}`,
    badges: [item.priority, badgeClass(item.accuracyLevel) === "good" ? "Verified" : "To verify"],
    body: item.person,
    rows: [
      row("Email", item.email), row("Phone", item.phone), row("Website", item.website, true),
      row("Application page", item.applicationPage, true), row("Facebook", item.facebook, true),
      row("Instagram", item.instagram, true), row("LinkedIn", item.linkedin, true),
      row("Source", item.source), row("Source URL", item.sourceUrl, true),
      row("Last checked", item.lastChecked), row("Accuracy", item.accuracyLevel), row("Notes", item.notes)
    ]
  })).join("") || emptyState("No contacts recorded.");
}

function renderCoachNetwork() {
  document.querySelector("#coachCount").textContent = `${state.coachNetwork.length} records`;
  document.querySelector("#coachGrid").innerHTML = state.coachNetwork.map((item) => card({
    label: item.connectionType, title: item.person, meta: `${item.country} · ${item.teamOrganization}`,
    badges: [item.currentStatus],
    body: `${item.nationality} · ${item.role}`,
    rows: [
      row("Team type", item.teamType), row("Dates", `${item.startDate} – ${item.endDate}`),
      row("Source", item.source), row("Source URL", item.sourceUrl, true),
      row("Last checked", item.lastChecked), row("Accuracy", item.accuracyLevel), row("Notes", item.notes)
    ]
  })).join("") || emptyState("No network records.");
}

function countryCard(item) {
  return card({
    label: item.continent, title: `${item.flag === "To verify" ? "" : item.flag + " "}${item.country}`,
    meta: `${item.confederation} · ${item.association}`,
    badges: [item.priority, item.status],
    body: `Opportunity score ${item.opportunityScore}`,
    rows: [
      row("Main league", item.mainLeague), row("National team", item.nationalTeam),
      row("Target roles", item.targetRoles), row("Licence note", item.licenceNote),
      row("Last updated", item.lastUpdated), row("Accuracy", item.accuracyLevel), row("Notes", item.notes)
    ]
  });
}

function renderCountries(filter = "All") {
  const list = filter === "All" ? state.countries : state.countries.filter((item) => item.continent === filter);
  document.querySelector("#countriesCount").textContent = `${list.length} records`;
  document.querySelector("#countriesGrid").innerHTML = list.map(countryCard).join("");
  const filters = ["All", ...new Set(state.countries.map((item) => item.continent))];
  document.querySelector("#countryFilters").innerHTML = filters.map((name) =>
    `<button class="${name === filter ? "active" : ""}" data-country-filter="${escapeHtml(name)}">${escapeHtml(name)}</button>`
  ).join("");
}

function renderLicences() {
  document.querySelector("#licenceCount").textContent = `${state.licences.length} records`;
  document.querySelector("#licenceGrid").innerHTML = state.licences.map((item) => card({
    label: item.confederation, title: `${item.country} · ${item.courseName}`,
    meta: item.association, badges: [item.priority, item.status],
    body: `Next window: ${item.nextApplicationWindow}`,
    rows: [
      row("Foreign applicant", item.foreignApplicant), row("AFC A recognition", item.afcALicenceRecognition),
      row("Language", item.language), row("Cost", item.cost), row("Duration", item.duration),
      row("Required documents", item.requiredDocuments), row("Coach education contact", item.coachEducationContact),
      row("Official link", item.officialLink, true), row("Source", item.sourceUrl, true),
      row("Last checked", item.lastChecked), row("Accuracy", item.accuracyLevel), row("Notes", item.notes)
    ]
  })).join("") || emptyState("No licence records.");
}

function emptyState(message) {
  return `<p class="empty">${escapeHtml(message)}</p>`;
}

function setupNavigation() {
  document.querySelector(".main-nav").addEventListener("click", (event) => {
    const button = event.target.closest("[data-page]");
    if (!button) return;
    document.querySelectorAll(".main-nav button").forEach((item) => item.classList.toggle("active", item === button));
    document.querySelectorAll(".page").forEach((page) => page.classList.toggle("active", page.id === button.dataset.page));
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  document.querySelector("#countryFilters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-country-filter]");
    if (button) renderCountries(button.dataset.countryFilter);
  });
}

async function loadDatabases() {
  try {
    const entries = await Promise.all(Object.entries(DATABASES).map(async ([key, url]) => {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`${url}: ${response.status}`);
      const payload = await response.json();
      if (!Array.isArray(payload)) throw new Error(`${url}: expected an array`);
      return [key, payload];
    }));
    entries.forEach(([key, payload]) => { state[key] = payload; });
    renderDashboard(); renderJobs(); renderContacts(); renderCoachNetwork(); renderCountries(); renderLicences();
  } catch (error) {
    const notice = document.querySelector("#databaseMessage");
    notice.hidden = false;
    notice.textContent = "For JSON database mode, please run with Live Server or GitHub Pages.";
    console.error("Database loading failed:", error);
  }
}

document.querySelector("#todayDate").textContent = new Intl.DateTimeFormat("en", { dateStyle: "long" }).format(new Date());
setupNavigation();
loadDatabases();

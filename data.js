"use strict";

const DATABASES = {
  jobs: "jobs.json",
  contacts: "contacts.json",
  pipelineContacts: "data/contacts.json",
  coachNetwork: "coach_network.json",
  countries: "countries.json",
  licences: "pro_licence_watch.json",
  leagueIntelligence: "league_intelligence.json",
  updates: "updates.json",
  updateSchedule: "update_schedule.json"
};

const state = { jobs: [], contacts: [], pipelineContacts: [], coachNetwork: [], countries: [], licences: [], leagueIntelligence: [], updates: [], updateSchedule: null };
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
  const currentCoaches = state.coachNetwork.filter((item) => text(item.currentStatus).toLowerCase() === "current" && !text(item.accuracyLevel).toLowerCase().includes("to verify"));
  const marketCount = (field) => state.countries.filter((item) => ["high", "medium", "open"].includes(text(item[field]).toLowerCase())).length;
  const professionalLeagues = state.leagueIntelligence.filter((item) => !["to verify", "not public"].includes(text(item.professionalDivisions).toLowerCase())).length;
  const stats = [
    ["Countries Covered", state.countries.length, "Priority markets"],
    ["Professional Leagues", professionalLeagues, "Source-qualified records"],
    ["National Teams", state.countries.length, "Country markets tracked"],
    ["Current Korean Coaches", currentCoaches.filter((item) => item.nationality === "Korean").length, "Verified current records"],
    ["Current Japanese Coaches", currentCoaches.filter((item) => item.nationality === "Japanese").length, "Verified current records"],
    ["Current Asian Coaches", currentCoaches.filter((item) => ["Korean", "Japanese", "Asian"].includes(item.nationality)).length, "Verified current records"],
    ["Head Coach Markets", marketCount("afcAHeadCoachPossibility"), "High or medium watch"],
    ["Assistant Coach Markets", marketCount("assistantCoachPossibility"), "High or medium watch"],
    ["Fitness Coach Markets", marketCount("fitnessCoachPossibility"), "High or medium watch"],
    ["4-Day Update Cycle", state.updateSchedule ? `Every ${escapeHtml(state.updateSchedule.updateCycleDays)} days` : "To verify", state.updateSchedule ? `Last: ${scheduleLastDate()} · Next: ${scheduleNextDate()} · Push: Manual` : "Schedule unavailable"]
  ];
  document.querySelector("#dashboardGrid").innerHTML = stats.map(([name, value, note]) =>
    `<article class="stat-card"><span>${escapeHtml(name)}</span><strong>${value}</strong><small>${escapeHtml(note)}</small></article>`
  ).join("");
  const actions = state.jobs.filter((item) => text(item.status).toLowerCase() === "open").slice(0, 2).map(jobCard);
  actions.push(card({ label: "Licence", title: "Review application windows", meta: "Pro Licence Watch", body: "Confirm foreign applicant rules and AFC A Licence recognition with priority associations." }));
  document.querySelector("#actionGrid").innerHTML = actions.join("");
}

function scheduleLastDate() {
  return state.updateSchedule && validDate(state.updateSchedule.lastSiteUpdate) ? state.updateSchedule.lastSiteUpdate : "To verify";
}
function scheduleNextDate() {
  const last = scheduleLastDate();
  if (!validDate(last)) return "To verify";
  const date = new Date(`${last}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + Number(state.updateSchedule.updateCycleDays || 4));
  return date.toISOString().slice(0, 10);
}
function renderUpdateSchedule() {
  const target = document.querySelector("#schedulePanel");
  const workflow = document.querySelector("#updateWorkflow");
  if (!state.updateSchedule) {
    target.innerHTML = "";
    workflow.innerHTML = "";
    return;
  }
  const next = scheduleNextDate();
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const researchDue = validDate(next) && dateValue(next) <= today.getTime();
  const filesUpdated = validDate(scheduleLastDate());
  const badges = [["Research Due", researchDue ? "hot" : "neutral"], ["Files Updated", filesUpdated ? "good" : "neutral"], ["Push Required", "neutral"], ["Site Live", "neutral"]];
  target.innerHTML = `<div class="schedule-heading"><div><span class="label">${escapeHtml(state.updateSchedule.cycleName)}</span><h3>Update Cycle: Every ${escapeHtml(state.updateSchedule.updateCycleDays)} Days</h3></div><div class="schedule-badges">${badges.map(([label, className]) => `<span class="badge ${className}">${escapeHtml(label)}</span>`).join("")}</div></div><dl class="schedule-grid">${row("Last Site Update", scheduleLastDate())}${row("Next Planned Update", next)}${row("Current Status", state.updateSchedule.updateStatus)}${row("Managed Databases", state.updateSchedule.managedFiles)}</dl><p class="schedule-note">Research is collected every four days. The live website changes after the updated JSON files are committed and pushed to GitHub.</p><p class="schedule-note urgent-monitoring">Official vacancies are monitored more frequently. Verified urgent vacancies may be added before the regular four-day database update.</p>`;
  const steps = ["Review verified research", "Update JSON databases", "Check Live Server", "Commit changes", "Push to GitHub", "Confirm GitHub Pages"];
  workflow.innerHTML = `<h3>Update Workflow</h3><ol>${steps.map((step) => `<li>${escapeHtml(step)}</li>`).join("")}</ol>`;
}

const leagueGroups = [
  ["League Structure", ["association", "confederation", "leagueSystem", "topDivision", "professionalDivisions", "semiProfessionalDivisions", "totalKnownDivisions", "topDivisionTeams", "leagueFormat"]],
  ["Competitions and Match Numbers", ["leagueMatchesPerClub", "regularSeasonMatches", "playoffMatches", "mainCupCompetitions", "superCup", "otherCompetitions", "seasonCalendar", "transferWindows"]],
  ["Licence and Coaching Opportunity", ["foreignPlayerRules", "foreignCoachRules", "headCoachMinimumLicence", "afcAHeadCoachPossibility", "assistantCoachPossibility", "fitnessCoachPossibility", "marketProfessionalLevel", "foreignCoachHiringFrequency", "englishWorkingEnvironment", "visaDifficulty"]],
  ["Current and Previous National Team Coaches", ["nationalTeamCurrentCoach", "nationalTeamCurrentCoachNationality", "nationalTeamCurrentCoachStartDate", "nationalTeamPreviousCoach", "nationalTeamPreviousCoachNationality"]],
  ["Coach Career Comparison", ["currentCoachCareerSummary", "previousCoachCareerSummary", "currentChampion", "currentChampionHeadCoach", "currentChampionCoachNationality", "previousChampionHeadCoach"]],
  ["Korean / Japanese / Asian Coach History", ["recentKoreanCoaches", "recentJapaneseCoaches", "recentOtherAsianCoaches"]],
  ["League and Club Budgets", ["leagueOperatingBudget", "leagueBudgetCurrency", "leagueBudgetStatus", "leagueBudgetSource", "clubBudgetRange", "clubBudgetCurrency", "clubBudgetStatus", "clubBudgetSource"]],
  ["National Team Budget", ["nationalAssociationBudget", "nationalAssociationBudgetCurrency", "nationalAssociationBudgetStatus", "nationalAssociationBudgetSource", "nationalTeamOperatingBudget", "nationalTeamBudgetCurrency", "nationalTeamBudgetStatus", "nationalTeamBudgetSource"]],
  ["Coach Salary Information", ["currentNationalTeamCoachSalary", "previousNationalTeamCoachSalary", "coachSalaryCurrency", "coachSalaryStatus", "coachSalarySource"]]
];
const titleCase = (key) => key.replace(/([A-Z])/g, " $1").replace(/^./, (char) => char.toUpperCase()).replace("Afc", "AFC");
const leagueRow = (key, value) => row(titleCase(key), value);
function leagueSources(item) {
  const links = (item.officialSourceUrls || []).map((url, index) => row(`Official source ${index + 1}`, url, true));
  return [row("Association website", item.officialAssociationWebsite, true), row("League website", item.officialLeagueWebsite, true), ...links, row("Last checked", item.lastChecked), row("Accuracy", item.accuracyLevel), row("Notes", item.notes)].join("");
}
function leagueCard(item) {
  const summary = [
    row("Top Division", item.topDivision), row("Known League Divisions", item.totalKnownDivisions), row("League Matches", item.leagueMatchesPerClub),
    row("Main Cup", item.mainCupCompetitions), row("AFC A Head Coach", item.afcAHeadCoachPossibility), row("Head Coach Fit", item.headCoachFitScore),
    row("Assistant Fit", item.assistantCoachFitScore), row("Fitness Fit", item.fitnessCoachFitScore), row("Last Checked", item.lastChecked)
  ].join("");
  const groups = leagueGroups.map(([heading, keys]) => `<h4>${escapeHtml(heading)}</h4>${keys.map((key) => leagueRow(key, item[key])).join("")}`).join("");
  const fitRows = Object.entries(item.fitFactors || {}).map(([key, value]) => leagueRow(key, value)).join("");
  const fit = `${leagueRow("headCoachFitScore", item.headCoachFitScore)}${leagueRow("assistantCoachFitScore", item.assistantCoachFitScore)}${leagueRow("fitnessCoachFitScore", item.fitnessCoachFitScore)}${leagueRow("overallOpportunityScore", item.overallOpportunityScore)}${fitRows}<p class="fit-note">This score is an internal comparison tool, not a prediction of employment.</p>`;
  return `<article class="card league-card"><div class="card-top"><span class="label">${escapeHtml(item.continent)}</span><span class="badge ${badgeClass(item.accuracyLevel)}">${escapeHtml(item.accuracyLevel)}</span></div><h3>${item.flag === "To verify" ? "" : escapeHtml(item.flag) + " "}${escapeHtml(item.marketName || item.country)}</h3><dl class="league-summary">${summary}</dl><details><summary>View Details</summary><dl>${groups}<h4>Official Sources</h4>${leagueSources(item)}<h4>Julio Fit Analysis</h4>${fit}</dl></details></article>`;
}
const leagueFilterNames = ["All", "Asia", "Oceania", "Canada", "Africa Watch", "Europe Watch", "AFC A Head Coach", "Assistant Coach", "Fitness Coach", "Verified", "To Verify"];
function leagueMatchesFilter(item, filter) {
  if (filter === "All") return true;
  if (["Asia", "Oceania", "Canada", "Africa Watch", "Europe Watch"].includes(filter)) return item.continent === filter;
  if (filter === "Verified") return /verified|official|audited/i.test(item.accuracyLevel);
  if (filter === "To Verify") return /to verify|research required/i.test(item.accuracyLevel);
  const field = { "AFC A Head Coach": "afcAHeadCoachPossibility", "Assistant Coach": "assistantCoachPossibility", "Fitness Coach": "fitnessCoachPossibility" }[filter];
  return /high|medium|open|suitable/i.test(text(item[field]));
}
function renderLeagueStats() {
  const data = state.leagueIntelligence;
  const countMarkets = (field) => data.filter((item) => /high|medium|open|suitable/i.test(text(item[field]))).length;
  const verifiedStatuses = new Set(["Official", "Audited Report"]);
  const uniqueCountries = new Set(data.map((item) => item.country)).size;
  const stats = [["Countries Covered", uniqueCountries], ["AFC A Head Coach Markets", countMarkets("afcAHeadCoachPossibility")], ["Assistant Coach Markets", countMarkets("assistantCoachPossibility")], ["Fitness Coach Markets", countMarkets("fitnessCoachPossibility")], ["Budgets Verified", data.filter((item) => verifiedStatuses.has(item.leagueBudgetStatus) || verifiedStatuses.has(item.nationalAssociationBudgetStatus) || verifiedStatuses.has(item.nationalTeamBudgetStatus) || verifiedStatuses.has(item.clubBudgetStatus)).length], ["Salaries Verified", data.filter((item) => verifiedStatuses.has(item.coachSalaryStatus)).length], ["Research Required", data.filter((item) => /research required|to verify/i.test(item.accuracyLevel)).length]];
  document.querySelector("#leagueStats").innerHTML = stats.map(([label, value]) => `<article class="stat-card"><span>${escapeHtml(label)}</span><strong>${value}</strong></article>`).join("");
}
function renderLeagueIntelligence(filter = "All", query = "") {
  const normalized = query.trim().toLowerCase();
  const list = state.leagueIntelligence.filter((item) => leagueMatchesFilter(item, filter) && (!normalized || [item.country, item.marketName, item.topDivision, item.association, item.nationalTeamCurrentCoach, item.nationalTeamPreviousCoach, item.currentChampionHeadCoach].join(" ").toLowerCase().includes(normalized)));
  document.querySelector("#leagueCount").textContent = `${list.length} markets`;
  document.querySelector("#leagueGrid").innerHTML = list.map(leagueCard).join("") || emptyState("No markets match this search and filter.");
  document.querySelector("#leagueFilters").innerHTML = leagueFilterNames.map((name) => `<button class="${name === filter ? "active" : ""}" data-league-filter="${escapeHtml(name)}">${escapeHtml(name)}</button>`).join("");
}

const updateFilterNames = ["All", "New", "Changed", "Verified", "Jobs", "Contacts", "Coach Network", "League Intelligence", "Pro Licence", "Deadline Soon", "Research Required"];
const validDate = (value) => /^\d{4}-\d{2}-\d{2}$/.test(text(value));
const dateValue = (value) => validDate(value) ? new Date(`${value}T00:00:00`).getTime() : 0;
function updateMatchesFilter(item, filter) {
  if (filter === "All") return true;
  if (filter === "New") return ["New", "New Vacancy"].includes(item.updateType);
  if (filter === "Changed") return ["Changed", "Vacancy Changed", "Vacancy Closed"].includes(item.updateType);
  if (filter === "Verified") return ["Verified", "Vacancy Verified"].includes(item.updateType);
  if (["Deadline Soon", "Research Required"].includes(filter)) return item.updateType === filter;
  const category = { Jobs: "Job", Contacts: "Contact" }[filter] || filter;
  return item.category === category;
}
function updateMatchesPeriod(item, period) {
  if (period === "All History") return true;
  if (!validDate(item.date)) return false;
  const days = period === "Last 7 Days" ? 7 : 30;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const difference = today.getTime() - dateValue(item.date);
  return difference >= 0 && difference <= days * 86400000;
}
function updateHighlight(item) {
  if (item.updateType === "Deadline Soon") return "deadline-highlight";
  if (["New", "New Vacancy", "Vacancy Verified"].includes(item.updateType) && item.category === "Job" && /verified|official/i.test(item.accuracyLevel)) return "verified-highlight";
  if (item.updateType === "Corrected" && ["Coach Network", "National Team", "Professional Club"].includes(item.category)) return "corrected-highlight";
  if (item.updateType === "Contact Added" && /verified|official/i.test(item.accuracyLevel)) return "contact-highlight";
  return "";
}
function updateCard(item) {
  const source = safeUrl(item.sourceUrl) ? row("Source URL", item.sourceUrl, true) : row("Source URL", item.sourceUrl);
  return `<article class="card update-card ${updateHighlight(item)}"><div class="card-top"><span class="label">${escapeHtml(item.date)}</span><span class="badge ${badgeClass(item.updateType)}">${escapeHtml(item.updateType)}</span></div><h3>${escapeHtml(item.title)}</h3><p class="meta">${escapeHtml(item.country)} · ${escapeHtml(item.organization)}</p><p>${escapeHtml(item.shortSummary)}</p><div class="update-card-meta"><span>${escapeHtml(item.priority)}</span><span>${escapeHtml(item.accuracyLevel)}</span><span>${escapeHtml(item.relatedPage)}</span></div><details><summary>View Details</summary><dl>${row("Source", item.sourceName)}${source}${row("Related Role", item.relatedRole)}${row("Status", item.status)}${row("Recommended Action", item.recommendedAction)}${row("Last Checked", item.lastChecked)}${row("Notes", item.notes)}</dl></details></article>`;
}
function renderUpdateStats() {
  const today = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Seoul", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
  const now = new Date(); now.setHours(0, 0, 0, 0);
  const thisWeek = state.updates.filter((item) => validDate(item.date) && now.getTime() - dateValue(item.date) >= 0 && now.getTime() - dateValue(item.date) <= 7 * 86400000 && ["Changed", "Corrected", "Vacancy Changed", "Vacancy Closed"].includes(item.updateType)).length;
  const stats = [["New Today", state.updates.filter((item) => item.date === today && ["New", "New Vacancy"].includes(item.updateType)).length], ["Changed This Week", thisWeek], ["Deadline Soon", state.updates.filter((item) => item.updateType === "Deadline Soon").length], ["Contacts Added", state.updates.filter((item) => item.updateType === "Contact Added").length], ["Coaches Appointed", state.updates.filter((item) => item.updateType === "Coach Appointed").length], ["Research Required", state.updates.filter((item) => item.updateType === "Research Required").length]];
  document.querySelector("#updatesStats").innerHTML = stats.map(([label, value]) => `<article class="stat-card"><span>${escapeHtml(label)}</span><strong>${value}</strong></article>`).join("");
}
function renderUpdates(filter = "All", query = "", period = "All History") {
  const normalized = query.trim().toLowerCase();
  const list = state.updates.filter((item) => updateMatchesFilter(item, filter) && updateMatchesPeriod(item, period) && (!normalized || [item.country, item.organization, item.title, item.relatedRole, item.shortSummary].join(" ").toLowerCase().includes(normalized))).sort((a, b) => dateValue(b.date) - dateValue(a.date) || text(b.time).localeCompare(text(a.time)));
  document.querySelector("#updatesCount").textContent = `${list.length} updates`;
  document.querySelector("#updatesGrid").innerHTML = list.map(updateCard).join("") || emptyState("No updates match this search and filter.");
  document.querySelector("#updatesFilters").innerHTML = updateFilterNames.map((name) => `<button class="${name === filter ? "active" : ""}" data-update-filter="${escapeHtml(name)}">${escapeHtml(name)}</button>`).join("");
}

const jobFilterNames = ["All", "Open", "Closing Soon", "Head Coach", "Assistant Coach", "Fitness Coach", "National Team", "Professional Club", "AFC", "OFC", "Africa", "Canada", "Central America", "Verified", "To Verify", "Closed"];
const verifiedJobPlatforms = new Set(["Official Website", "Instagram", "Facebook", "TikTok", "LinkedIn", "X", "FIFA", "AFC", "OFC", "CAF", "UEFA", "CONCACAF", "FutbolJobs", "Jobs4Football", "LinkedIn Jobs"]);
const socialJobPlatforms = new Set(["Instagram", "Facebook", "TikTok", "LinkedIn", "X"]);
const recruitmentPlatforms = new Set(["FutbolJobs", "Jobs4Football", "LinkedIn Jobs"]);
function calculateJobDeadline(item) {
  if (!validDate(item.deadline)) {
    item.daysUntilDeadline = "To verify";
    return;
  }
  const today = new Date(); today.setHours(0, 0, 0, 0);
  item.daysUntilDeadline = Math.round((dateValue(item.deadline) - today.getTime()) / 86400000);
  if (item.daysUntilDeadline < 0) item.status = "Closed";
  else if (item.daysUntilDeadline <= 7) item.status = "Closing Soon";
}
function hasVerifiedJobSource(item) {
  if (!verifiedJobPlatforms.has(item.sourcePlatform) || !safeUrl(item.sourceUrl) || /to verify|screenshot|uncertain/i.test(text(item.accuracyLevel))) return false;
  if (socialJobPlatforms.has(item.sourcePlatform)) return !/to verify/i.test(text(item.officialSocialAccount));
  if (recruitmentPlatforms.has(item.sourcePlatform)) return Boolean(safeUrl(item.applicationLink));
  return item.sourcePlatform === "Official Website" || Boolean(safeUrl(item.applicationLink));
}
function prepareJobs() {
  state.jobs.forEach((item) => {
    calculateJobDeadline(item);
    if (item.status === "Open" && (!validDate(item.deadline) || !hasVerifiedJobSource(item))) item.status = "To Verify";
  });
}
function sourceBadge(item) {
  const jobBoards = ["FutbolJobs", "Jobs4Football", "LinkedIn Jobs"];
  return jobBoards.includes(item.sourcePlatform) ? "Job Board" : item.sourcePlatform;
}
function jobAction(label, value, primary = false) {
  const url = safeUrl(value);
  return url ? `<a class="job-action ${primary ? "primary" : ""}" href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(label)}</a>` : `<span class="job-action disabled" aria-disabled="true">${escapeHtml(label)} unavailable</span>`;
}
function jobCard(item) {
  const summary = [row("Role", item.roleType), row("Country", item.country), row("Organization", item.organization), row("Team type", item.teamType), row("Deadline", item.deadline), row("Days remaining", item.daysUntilDeadline), row("Licence requirement", item.licenceRequirement), row("AFC A fit", item.afcALicenceFit), row("Fit score", item.fitScore), row("Status", item.status), row("Accuracy", item.accuracyLevel), row("Source platform", sourceBadge(item))].join("");
  const expanded = [row("Full description", item.details), row("Application method", item.applicationMethod), row("Contact person", item.contactPerson), row("Public email", item.contactEmail), row("Public phone", item.contactPhone), row("Official source", item.sourceUrl, true), row("Official SNS", item.officialSocialAccount), row("Licence analysis", `${item.licenceRequirement} · ${item.afcALicenceFit}`), row("Julio fit reason", item.fitReason), row("Recommended action", item.recommendedAction), row("Last checked", item.lastChecked), row("Notes", item.notes)].join("");
  return `<article class="card job-card"><div class="card-top"><span class="label">${escapeHtml(item.roleType)}</span><span class="source-badge">${escapeHtml(sourceBadge(item))}</span><span class="badge ${badgeClass(item.status)}">${escapeHtml(item.status)}</span></div><h3>${escapeHtml(item.position)}</h3><dl class="job-summary">${summary}</dl><details><summary>View Details</summary><dl>${expanded}</dl></details><div class="job-actions">${jobAction("Open Official Source", item.sourceUrl)}${jobAction("Open Application", item.applicationLink, true)}</div></article>`;
}
function jobMatchesFilter(item, filter) {
  if (filter === "All") return true;
  if (["Open", "Closing Soon", "To Verify", "Closed"].includes(filter)) return item.status === filter;
  if (["Head Coach", "Assistant Coach", "Fitness Coach"].includes(filter)) return item.roleType === filter;
  if (["National Team", "Professional Club"].includes(filter)) return item.teamType === filter;
  if (filter === "Verified") return hasVerifiedJobSource(item);
  if (filter === "AFC") return item.continent === "Asia" || item.sourcePlatform === "AFC";
  if (filter === "OFC") return item.continent === "Oceania" || item.sourcePlatform === "OFC";
  if (filter === "Africa") return item.continent === "Africa";
  return item.continent === filter;
}
function renderJobStats() {
  const stats = [["Verified Open", state.jobs.filter((item) => item.status === "Open" && hasVerifiedJobSource(item)).length], ["Closing Within 7 Days", state.jobs.filter((item) => item.status === "Closing Soon").length], ["Head Coach", state.jobs.filter((item) => item.roleType === "Head Coach" && ["Open", "Closing Soon"].includes(item.status)).length], ["Assistant Coach", state.jobs.filter((item) => item.roleType === "Assistant Coach" && ["Open", "Closing Soon"].includes(item.status)).length], ["Fitness Coach", state.jobs.filter((item) => item.roleType === "Fitness Coach" && ["Open", "Closing Soon"].includes(item.status)).length], ["To Verify", state.jobs.filter((item) => item.status === "To Verify").length]];
  document.querySelector("#jobsStats").innerHTML = stats.map(([label, value]) => `<article class="stat-card"><span>${escapeHtml(label)}</span><strong>${value}</strong></article>`).join("");
}
function renderJobs(filter = "All", query = "") {
  const normalized = query.trim().toLowerCase();
  const list = state.jobs.filter((item) => jobMatchesFilter(item, filter) && (!normalized || [item.roleType, item.position, item.country, item.organization, item.teamType, item.sourcePlatform].join(" ").toLowerCase().includes(normalized)));
  document.querySelector("#jobsCount").textContent = `${list.length} records`;
  document.querySelector("#jobsGrid").innerHTML = list.map(jobCard).join("") || emptyState("No vacancies match this search and filter.");
  document.querySelector("#jobsFilters").innerHTML = jobFilterNames.map((name) => `<button class="${name === filter ? "active" : ""}" data-job-filter="${escapeHtml(name)}">${escapeHtml(name)}</button>`).join("");
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
  document.querySelector("#jobsFilters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-job-filter]");
    if (button) renderJobs(button.dataset.jobFilter, document.querySelector("#jobsSearch").value);
  });
  document.querySelector("#jobsSearch").addEventListener("input", (event) => {
    const active = document.querySelector("#jobsFilters .active");
    renderJobs(active ? active.dataset.jobFilter : "All", event.target.value);
  });
  document.querySelector("#leagueFilters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-league-filter]");
    if (button) renderLeagueIntelligence(button.dataset.leagueFilter, document.querySelector("#leagueSearch").value);
  });
  document.querySelector("#leagueSearch").addEventListener("input", (event) => {
    const active = document.querySelector("#leagueFilters .active");
    renderLeagueIntelligence(active ? active.dataset.leagueFilter : "All", event.target.value);
  });
  document.querySelector("#updatesFilters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-update-filter]");
    if (button) renderUpdates(button.dataset.updateFilter, document.querySelector("#updatesSearch").value, document.querySelector("#updatesPeriod").value);
  });
  document.querySelector("#updatesSearch").addEventListener("input", (event) => {
    const active = document.querySelector("#updatesFilters .active");
    renderUpdates(active ? active.dataset.updateFilter : "All", event.target.value, document.querySelector("#updatesPeriod").value);
  });
  document.querySelector("#updatesPeriod").addEventListener("change", (event) => {
    const active = document.querySelector("#updatesFilters .active");
    renderUpdates(active ? active.dataset.updateFilter : "All", document.querySelector("#updatesSearch").value, event.target.value);
  });
}

async function loadDatabases() {
  const entries = await Promise.allSettled(Object.entries(DATABASES).map(async ([key, url]) => {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`${url}: ${response.status}`);
      const payload = await response.json();
      if (key === "updateSchedule") {
        if (!payload || Array.isArray(payload) || typeof payload !== "object") throw new Error(`${url}: expected an object`);
      } else if (!Array.isArray(payload)) throw new Error(`${url}: expected an array`);
      return [key, payload];
  }));
  entries.forEach((result, index) => {
    if (result.status === "fulfilled") state[result.value[0]] = result.value[1];
    else console.error("Database loading failed:", Object.values(DATABASES)[index], result.reason);
  });
  const resultByKey = Object.fromEntries(Object.keys(DATABASES).map((key, index) => [key, entries[index]]));
  const generalFailed = ["jobs", "contacts", "coachNetwork", "countries", "licences"].some((key) => resultByKey[key].status === "rejected");
  const leagueFailed = resultByKey.leagueIntelligence.status === "rejected";
  const updatesFailed = resultByKey.updates.status === "rejected";
  const scheduleFailed = resultByKey.updateSchedule.status === "rejected";
  const existingContactKeys = new Set(state.contacts.map((item) => `${text(item.organization).toLowerCase()}|${text(item.email).toLowerCase()}`));
  state.pipelineContacts.forEach((item) => {
    const key = `${text(item.organisation).toLowerCase()}|${text(item.email).toLowerCase()}`;
    if (existingContactKeys.has(key)) return;
    state.contacts.push({
      id: item.id,
      continent: item.region,
      country: item.country,
      organization: item.organisation,
      type: item.organisationType,
      role: "Official contact",
      person: "Not publicly listed",
      email: item.email,
      phone: "Not Public",
      website: item.website,
      facebook: "To verify",
      instagram: "To verify",
      linkedin: "To verify",
      applicationPage: item.contactPage,
      priority: "High",
      source: "Official organisation page",
      sourceUrl: item.sourceUrl,
      lastChecked: text(item.detectedAt).slice(0, 10),
      accuracyLevel: "To verify",
      notes: "Automatically detected public role-based email. Verify the recipient before sending a CV."
    });
    existingContactKeys.add(key);
  });
  if (generalFailed) {
    const notice = document.querySelector("#databaseMessage");
    notice.hidden = false;
    notice.textContent = "For JSON database mode, please run with Live Server or GitHub Pages.";
  }
  if (leagueFailed) {
    const notice = document.querySelector("#leagueMessage");
    notice.hidden = false;
    notice.textContent = "League Intelligence data could not be loaded. Run the project with Live Server or GitHub Pages.";
  }
  if (updatesFailed) {
    const notice = document.querySelector("#updatesMessage");
    notice.hidden = false;
    notice.textContent = "Update Center data could not be loaded. Run the project with Live Server or GitHub Pages.";
  }
  if (scheduleFailed) {
    const notice = document.querySelector("#scheduleMessage");
    notice.hidden = false;
    notice.textContent = "Update schedule could not be loaded. Run the project with Live Server or GitHub Pages.";
  }
  prepareJobs(); renderUpdateSchedule(); renderDashboard(); renderJobStats(); renderJobs(); renderContacts(); renderCoachNetwork(); renderCountries(); renderLicences(); renderLeagueStats(); renderLeagueIntelligence(); renderUpdateStats(); renderUpdates();
}

document.querySelector("#todayDate").textContent = new Intl.DateTimeFormat("en", { dateStyle: "long" }).format(new Date());
setupNavigation();
loadDatabases();

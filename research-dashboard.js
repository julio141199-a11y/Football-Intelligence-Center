"use strict";

(function () {
  const escapeValue = (value) => String(value ?? "To verify").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[char]));

  const formatDateTime = (value) => {
    if (!value) return "Not run yet";
    const date = new Date(value);
    return Number.isNaN(date.getTime())
      ? String(value)
      : new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(date);
  };

  async function loadJson(url, fallback) {
    try {
      const response = await fetch(`${url}?v=${Date.now()}`, { cache: "no-store" });
      if (!response.ok) throw new Error(`${url}: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error("Research dashboard load failed:", error);
      return fallback;
    }
  }

  function cleanLegacyDashboardCards() {
    document.querySelectorAll("#dashboardGrid .stat-card").forEach((card) => {
      const label = card.querySelector("span")?.textContent?.trim() || "";
      if (label === "Fitness Coach Markets") card.remove();
      if (label === "4-Day Update Cycle") {
        const strong = card.querySelector("strong");
        const small = card.querySelector("small");
        card.querySelector("span").textContent = "Daily Update Cycle";
        if (strong) strong.textContent = "Every day";
        if (small) small.textContent = "Maintenance 08:00 · Research 08:15 KST";
      }
    });

    document.querySelectorAll("#schedulePanel .schedule-note").forEach((node) => {
      if (/four days|four-day/i.test(node.textContent)) {
        node.textContent = "Research and maintenance run daily. The public website changes after valid JSON or website files are committed to GitHub.";
      }
    });

    const scheduleHeading = document.querySelector("#schedulePanel h3");
    if (scheduleHeading && /Every\s+\d+\s+Days/i.test(scheduleHeading.textContent)) {
      scheduleHeading.textContent = "Update Cycle: Daily";
    }
  }

  function renderResearchStatus(state, inbox) {
    const target = document.querySelector("#researchStatusPanel");
    if (!target) return;

    const leads = Array.isArray(inbox) ? inbox : [];
    const pending = leads.filter((item) => item.status === "To Verify").length;
    const promoted = leads.filter((item) => item.status === "Promoted").length;
    const rejected = leads.filter((item) => item.status === "Rejected").length;
    const sourceStates = state && typeof state.sourceStates === "object" ? Object.values(state.sourceStates) : [];
    const successfulSources = sourceStates.filter((item) => item.lastResult === "success").length;
    const errorSources = sourceStates.filter((item) => item.lastResult === "error").length;
    const statusClass = state?.lastSuccessfulRun ? "good" : "neutral";

    target.innerHTML = `
      <div class="schedule-heading">
        <div>
          <span class="label">Free Research Automation</span>
          <h3>FIC Research Watch</h3>
        </div>
        <div class="schedule-badges">
          <span class="badge ${statusClass}">${state?.lastSuccessfulRun ? "Last run successful" : "Waiting for first data run"}</span>
          <span class="badge ${pending ? "hot" : "neutral"}">${pending} pending review</span>
        </div>
      </div>
      <dl class="schedule-grid">
        <div class="detail-row"><dt>Last run</dt><dd>${escapeValue(formatDateTime(state?.lastRun))}</dd></div>
        <div class="detail-row"><dt>Last successful run</dt><dd>${escapeValue(formatDateTime(state?.lastSuccessfulRun))}</dd></div>
        <div class="detail-row"><dt>Sources successful</dt><dd>${successfulSources}</dd></div>
        <div class="detail-row"><dt>Source errors</dt><dd>${errorSources}</dd></div>
        <div class="detail-row"><dt>Pending leads</dt><dd>${pending}</dd></div>
        <div class="detail-row"><dt>Promoted / Rejected</dt><dd>${promoted} / ${rejected}</dd></div>
      </dl>
      <p class="schedule-note">Research leads are shown here for transparency. Only verified vacancies added to jobs.json appear in the Jobs page.</p>
    `;
  }

  async function initialiseResearchStatus() {
    const [researchState, researchInbox] = await Promise.all([
      loadJson("data/research_state.json", {}),
      loadJson("data/research_inbox.json", [])
    ]);
    renderResearchStatus(researchState, researchInbox);
    cleanLegacyDashboardCards();

    const observer = new MutationObserver(cleanLegacyDashboardCards);
    const dashboard = document.querySelector("#dashboardGrid");
    const schedule = document.querySelector("#schedulePanel");
    if (dashboard) observer.observe(dashboard, { childList: true, subtree: true });
    if (schedule) observer.observe(schedule, { childList: true, subtree: true });
    setTimeout(() => observer.disconnect(), 5000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialiseResearchStatus);
  } else {
    initialiseResearchStatus();
  }
})();

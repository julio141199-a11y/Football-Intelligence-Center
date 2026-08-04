"use strict";

(function () {
  const esc = (value) => String(value ?? "To verify").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[char]));

  const fetchJson = async (url, fallback) => {
    try {
      const response = await fetch(`${url}?v=${Date.now()}`, { cache: "no-store" });
      if (!response.ok) throw new Error(`${url}: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error("Phase 5 UI data load failed:", error);
      return fallback;
    }
  };

  const statusText = (value) => String(value || "").toLowerCase();
  const dateText = (value) => {
    if (!value || value === "To verify" || value === "Not Public") return "To verify";
    const date = new Date(`${value}T00:00:00`);
    return Number.isNaN(date.getTime())
      ? value
      : new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(date);
  };

  const jobPriority = (job) => {
    const fit = Number(job.fitScore || 0);
    const days = Number(job.daysUntilDeadline);
    const status = statusText(job.status);
    let score = fit;
    if (status.includes("closing soon")) score += 30;
    if (status.includes("verified open") || ["open", "new", "updated"].includes(status)) score += 20;
    if (Number.isFinite(days) && days >= 0 && days <= 7) score += 20;
    const targetText = `${job.position || ""} ${job.teamType || ""}`.toLowerCase();
    if (job.roleType === "Assistant Coach" && targetText.includes("national")) score += 25;
    if (job.roleType === "Head Coach" && /u-?20|under-?20/.test(targetText)) score += 25;
    if (job.roleType === "Head Coach" && targetText.includes("professional")) score += 10;
    return score;
  };

  function renderMetrics(jobs, updates, inbox) {
    const open = jobs.filter((job) => {
      const s = statusText(job.status);
      return s.includes("verified open") || ["open", "new", "updated"].includes(s) || s.includes("closing soon");
    });
    const closing = open.filter((job) => statusText(job.status).includes("closing soon") || (Number(job.daysUntilDeadline) >= 0 && Number(job.daysUntilDeadline) <= 3));
    const newUpdates = updates.filter((item) => {
      const value = item.date || item.updatedAt || item.lastUpdated || item.createdAt;
      if (!value) return false;
      const date = new Date(value);
      return !Number.isNaN(date.getTime()) && Date.now() - date.getTime() <= 7 * 86400000;
    });
    const pending = inbox.filter((item) => item.status === "To Verify");

    const metrics = [
      ["Verified Open", open.length, "urgent"],
      ["Closing Soon", closing.length, closing.length ? "urgent" : ""],
      ["New This Week", newUpdates.length, ""],
      ["Research Leads", pending.length, ""]
    ];

    document.querySelector("#prioritySummary").innerHTML = metrics.map(([label, value, className]) => `
      <article class="priority-metric ${className}">
        <span>${esc(label)}</span>
        <strong>${value}</strong>
      </article>
    `).join("");

    const hero = document.querySelector("#heroSummary");
    if (open.length) {
      hero.textContent = `${open.length} verified opportunity${open.length === 1 ? "" : "ies"} currently require review.`;
    } else if (pending.length) {
      hero.textContent = `No verified open vacancy yet. ${pending.length} research lead${pending.length === 1 ? "" : "s"} await verification.`;
    } else {
      hero.textContent = "No verified open vacancy or pending research lead at the moment.";
    }
  }

  function renderPriorityJobs(jobs) {
    const target = document.querySelector("#priorityJobsGrid");
    const active = jobs
      .filter((job) => {
        const s = statusText(job.status);
        return s.includes("verified open") || ["open", "new", "updated"].includes(s) || s.includes("closing soon");
      })
      .sort((a, b) => jobPriority(b) - jobPriority(a))
      .slice(0, 3);

    if (!active.length) {
      target.innerHTML = `
        <article class="card">
          <span class="label">No verified opening</span>
          <h3>Research Watch is active</h3>
          <p>Potential leads remain outside the Jobs page until official verification is complete.</p>
        </article>`;
      return;
    }

    target.innerHTML = active.map((job) => `
      <article class="card priority-job">
        <div class="card-top">
          <span class="label">${esc(job.roleType)}</span>
          <span class="badge ${statusText(job.status).includes("closing") ? "hot" : "good"}">${esc(job.status)}</span>
        </div>
        <h3>${esc(job.position || `${job.organization} ${job.roleType}`)}</h3>
        <p class="meta">${esc(job.country)} · ${esc(job.organization)}</p>
        <p>${esc(job.shortSummary || job.recommendedAction || "Review the official source and application requirements.")}</p>
        <p class="job-deadline">Deadline: ${esc(dateText(job.deadline))}</p>
      </article>
    `).join("");
  }

  function renderMarketPulse(updates) {
    const target = document.querySelector("#marketPulseGrid");
    const sorted = [...updates].sort((a, b) => {
      const aDate = new Date(a.date || a.updatedAt || a.lastUpdated || 0).getTime();
      const bDate = new Date(b.date || b.updatedAt || b.lastUpdated || 0).getTime();
      return bDate - aDate;
    }).slice(0, 4);

    if (!sorted.length) {
      target.innerHTML = `<article class="pulse-item"><h4>No recent verified movement</h4><p>New verified changes will appear here.</p></article>`;
      return;
    }

    target.innerHTML = sorted.map((item) => `
      <article class="pulse-item">
        <span class="label">${esc(item.type || item.category || "Update")}</span>
        <h4>${esc(item.title || item.organization || item.country || "Database update")}</h4>
        <p>${esc(item.summary || item.details || item.notes || item.description || "Verified information updated.")}</p>
      </article>
    `).join("");
  }

  function renderBrief(researchState, inbox, schedule) {
    const target = document.querySelector("#dailyBriefPanel");
    const pending = inbox.filter((item) => item.status === "To Verify").length;
    const sourceStates = researchState && typeof researchState.sourceStates === "object"
      ? Object.values(researchState.sourceStates) : [];
    const success = sourceStates.filter((item) => item.lastResult === "success").length;
    const errors = sourceStates.filter((item) => item.lastResult === "error").length;
    const lastRun = researchState?.lastRun
      ? new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(researchState.lastRun))
      : "Not run yet";

    target.innerHTML = `
      <div class="brief-row"><span>Automation</span><strong>Daily at 08:00 and 18:00 KST</strong></div>
      <div class="brief-row"><span>Last research run</span><strong>${esc(lastRun)}</strong></div>
      <div class="brief-row"><span>Sources checked</span><strong>${success}</strong></div>
      <div class="brief-row"><span>Source errors</span><strong>${errors}</strong></div>
      <div class="brief-row"><span>Pending verification</span><strong>${pending}</strong></div>
      <div class="brief-row"><span>Data policy</span><strong>${schedule?.commitPolicy?.commitOnlyOnMeaningfulChange ? "Commit on meaningful change" : "Review required"}</strong></div>
    `;
  }

  function connectJumpButtons() {
    document.querySelectorAll("[data-jump-page]").forEach((button) => {
      button.addEventListener("click", () => {
        const targetPage = button.dataset.jumpPage;
        const navButton = document.querySelector(`.main-nav [data-page="${targetPage}"]`);
        if (navButton) navButton.click();
      });
    });
  }

  async function init() {
    const [jobs, updates, inbox, researchState, schedule, pipelineOpportunities, pipelineUpdates, vacancies] = await Promise.all([
      fetchJson("jobs.json", []),
      fetchJson("updates.json", []),
      fetchJson("data/research_inbox.json", []),
      fetchJson("data/research_state.json", {}),
      fetchJson("update_schedule.json", {}),
      fetchJson("data/opportunities.json", []),
      fetchJson("data/updates.json", []),
      fetchJson("data/vacancies.json", [])
    ]);

    const vacancyJobs = vacancies.map((item) => ({
      id: item.id, roleType: item.role, position: `${item.organization} ${item.role}`,
      organization: item.organization, country: item.country, teamType: item.team_level,
      status: ({ NEW: "New", UPDATED: "Updated", CLOSING_SOON: "Closing Soon", CLOSED: "Closed", EXPIRED: "Expired", UNVERIFIED: "To Verify" })[item.status] || "To Verify",
      deadline: item.deadline || "To verify", fitScore: item.fit_score,
      shortSummary: `${item.role} vacancy record from ${item.source_type || "official source"}.`,
      sourceUrl: item.official_source_url
    }));
    const mergedJobs = [...jobs, ...vacancyJobs].filter((item, index, all) =>
      index === all.findIndex((candidate) => candidate.id === item.id)
    );

    const pendingPipeline = pipelineOpportunities.map((item) => ({
      status: item.status,
      sourceUrl: item.sourceUrl
    }));
    const scopedUpdates = updates.filter((item) =>
      item.category !== "Coach Network" && item.relatedPage !== "Coach Network"
    );
    renderMetrics(mergedJobs, scopedUpdates, [...inbox, ...pendingPipeline]);
    renderPriorityJobs(mergedJobs);
    const pipelinePulse = pipelineUpdates.slice(0, 3).map((item) => ({
      date: item.runAt,
      type: "Pipeline",
      title: "Daily opportunity scan",
      summary: `${item.sourcesChecked || 0} sources checked · ${item.newCandidates || 0} new candidate(s) · ${item.newContacts || 0} new contact(s) · ${item.socialProfiles || 0} official social profile(s)`
    }));
    renderMarketPulse([...scopedUpdates, ...pipelinePulse]);
    renderBrief(researchState, [...inbox, ...pendingPipeline], schedule);
    connectJumpButtons();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

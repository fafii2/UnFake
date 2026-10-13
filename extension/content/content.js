/**
 * UnFake — Content Script
 *
 * Injected into every webpage. Handles:
 * 1. Receiving messages from the background service worker.
 * 2. Rendering the loading overlay.
 * 3. Rendering the results modal with verdict, explanation, and evidence.
 * 4. Dismissing the modal.
 */

(() => {
  // Prevent double-injection
  if (window.__unfakeInitialized) return;
  window.__unfakeInitialized = true;

  const MODAL_ID = "unfake-modal";
  const OVERLAY_ID = "unfake-overlay";

  // ── Message Listener ────────────────────────────────────────────

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "show_loading") {
      showLoading(message.claim);
    } else if (message.action === "show_result") {
      showResult(message.result);
    }
  });

  // ── Loading State ───────────────────────────────────────────────

  function showLoading(claim) {
    removeExisting();

    const overlay = createOverlay();
    const modal = createModal();

    modal.innerHTML = `
      <div class="unfake-modal-header">
        <div class="unfake-logo-row">
          <span class="unfake-logo-icon">🔍</span>
          <span class="unfake-logo-text">UnFake</span>
        </div>
        <button class="unfake-close-btn" id="unfake-close">&times;</button>
      </div>
      <div class="unfake-modal-body">
        <div class="unfake-loading">
          <div class="unfake-spinner"></div>
          <p class="unfake-loading-text">Verifying claim...</p>
          <p class="unfake-claim-preview">"${escapeHtml(truncate(claim, 150))}"</p>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);
    document.body.appendChild(modal);
    attachCloseHandler();
  }

  // ── Result Display ──────────────────────────────────────────────

  function showResult(result) {
    removeExisting();

    const overlay = createOverlay();
    const modal = createModal();

    const isError = result.error || result.status === "error";
    const verdict = isError ? "error" : (result.verdict || "unknown");
    const verdictLabel = getVerdictLabel(verdict);
    const verdictClass = getVerdictClass(verdict);

    let evidenceHtml = "";
    if (result.evidence && result.evidence.length > 0) {
      evidenceHtml = `
        <div class="unfake-evidence-section">
          <h3 class="unfake-evidence-title">Sources</h3>
          ${result.evidence.map((e) => `
            <div class="unfake-evidence-item">
              <div class="unfake-evidence-header">
                <a href="${escapeHtml(e.source_url)}" target="_blank" rel="noopener noreferrer"
                   class="unfake-evidence-link">
                  ${escapeHtml(e.title)}
                </a>
                <span class="unfake-evidence-badge unfake-badge-${e.relevance}">
                  ${e.relevance}
                </span>
              </div>
              <p class="unfake-evidence-snippet">${escapeHtml(e.snippet)}</p>
              <div class="unfake-evidence-meta">
                ${e.publisher ? `<span>${escapeHtml(e.publisher)}</span>` : ""}
                ${e.published_date ? `<span>· ${escapeHtml(e.published_date)}</span>` : ""}
                <span class="unfake-source-type">${e.source_type === "local_archive" ? "📁 Archive" : "🌐 Web"}</span>
              </div>
            </div>
          `).join("")}
        </div>
      `;
    }

    let triageHtml = "";
    if (result.triage) {
      triageHtml = `
        <div class="unfake-triage-info">
          <span class="unfake-triage-label">Triage:</span>
          ${escapeHtml(result.triage.reason)}
        </div>
      `;
    }

    modal.innerHTML = `
      <div class="unfake-modal-header">
        <div class="unfake-logo-row">
          <span class="unfake-logo-icon">🔍</span>
          <span class="unfake-logo-text">UnFake</span>
        </div>
        <button class="unfake-close-btn" id="unfake-close">&times;</button>
      </div>
      <div class="unfake-modal-body">
        <div class="unfake-verdict-section">
          <div class="unfake-verdict-badge ${verdictClass}">
            ${verdictLabel}
          </div>
        </div>
        <div class="unfake-explanation">
          <p>${escapeHtml(result.explanation || "No explanation available.")}</p>
        </div>
        ${triageHtml}
        <div class="unfake-original-claim">
          <h3 class="unfake-claim-title">Your claim</h3>
          <blockquote class="unfake-claim-text">
            "${escapeHtml(truncate(result.original_claim || "", 500))}"
          </blockquote>
        </div>
        ${evidenceHtml}
        <div class="unfake-footer-info">
          ${result.processing_time_ms != null
            ? `<span>Processed in ${result.processing_time_ms}ms</span>`
            : ""}
          <span class="unfake-disclaimer">
            This is an assistive tool. Verify important claims through multiple sources.
          </span>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);
    document.body.appendChild(modal);
    attachCloseHandler();

    // Animate in
    requestAnimationFrame(() => {
      overlay.classList.add("unfake-visible");
      modal.classList.add("unfake-visible");
    });
  }

  // ── Helpers ─────────────────────────────────────────────────────

  function createOverlay() {
    const overlay = document.createElement("div");
    overlay.id = OVERLAY_ID;
    overlay.className = "unfake-overlay";
    return overlay;
  }

  function createModal() {
    const modal = document.createElement("div");
    modal.id = MODAL_ID;
    modal.className = "unfake-modal";
    return modal;
  }

  function attachCloseHandler() {
    const closeBtn = document.getElementById("unfake-close");
    const overlay = document.getElementById(OVERLAY_ID);

    if (closeBtn) {
      closeBtn.addEventListener("click", removeExisting);
    }
    if (overlay) {
      overlay.addEventListener("click", removeExisting);
    }

    // ESC key
    document.addEventListener("keydown", function handler(e) {
      if (e.key === "Escape") {
        removeExisting();
        document.removeEventListener("keydown", handler);
      }
    });
  }

  function removeExisting() {
    const modal = document.getElementById(MODAL_ID);
    const overlay = document.getElementById(OVERLAY_ID);
    if (modal) modal.remove();
    if (overlay) overlay.remove();
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function truncate(text, maxLength) {
    if (!text) return "";
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "…";
  }

  function getVerdictLabel(verdict) {
    const labels = {
      supported: "✅ Supported",
      contradicted: "❌ Contradicted",
      mixed: "⚠️ Mixed Evidence",
      insufficient_evidence: "❓ Insufficient Evidence",
      error: "⚠️ Error",
      unknown: "❓ Unknown",
    };
    return labels[verdict] || labels.unknown;
  }

  function getVerdictClass(verdict) {
    const classes = {
      supported: "unfake-verdict-supported",
      contradicted: "unfake-verdict-contradicted",
      mixed: "unfake-verdict-mixed",
      insufficient_evidence: "unfake-verdict-insufficient",
      error: "unfake-verdict-error",
    };
    return classes[verdict] || "unfake-verdict-insufficient";
  }
})();

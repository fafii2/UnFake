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
    } else if (message.action === "start_crop") {
      if (window.UnFakeCrop) {
        window.UnFakeCrop.startCrop((cropArea) => {
          chrome.runtime.sendMessage({
            action: "crop_completed",
            cropArea: cropArea,
          });
        });
      }
    } else if (message.action === "show_ocr_loading") {
      showOcrLoading();
    } else if (message.action === "show_ocr_review") {
      showOcrReview(message.data);
    }
  });

  // ── Loading States ──────────────────────────────────────────────

  function showOcrLoading() {
    removeExisting();

    const overlay = createOverlay();
    const modal = createModal();

    modal.innerHTML = `
      <div class="unfake-modal-header">
        <div class="unfake-logo-row">
          <span class="unfake-logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0a192f" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="m9 12 2 2 4-4"/>
            </svg>
          </span>
          <span class="unfake-logo-text">UnFake</span>
        </div>
        <button class="unfake-close-btn" id="unfake-close" aria-label="Close">&times;</button>
      </div>
      <div class="unfake-modal-body">
        <div class="unfake-loading">
          <div class="unfake-spinner"></div>
          <p class="unfake-loading-text">Extracting text from image...</p>
          <p class="unfake-claim-preview">Running local OCR recognition (100% on-device)</p>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);
    document.body.appendChild(modal);
    attachCloseHandler();

    requestAnimationFrame(() => {
      overlay.classList.add("unfake-visible");
      modal.classList.add("unfake-visible");
    });
  }

  // ── OCR Review & Edit Modal ─────────────────────────────────────

  function showOcrReview(data) {
    removeExisting();

    const overlay = createOverlay();
    const modal = createModal();

    const text = data.text || "";
    const confidence = data.confidence || 0;
    const snippetUrl = data.snippetUrl || "";

    let confClass = "unfake-confidence-high";
    let confLabel = `🟢 ${confidence}% Confidence`;
    if (confidence < 60) {
      confClass = "unfake-confidence-low";
      confLabel = `🔴 ${confidence}% Confidence (Check for errors)`;
    } else if (confidence < 80) {
      confClass = "unfake-confidence-medium";
      confLabel = `🟡 ${confidence}% Confidence (Review recommended)`;
    }

    modal.innerHTML = `
      <div class="unfake-modal-header">
        <div class="unfake-logo-row">
          <span class="unfake-logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0a192f" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="m9 12 2 2 4-4"/>
            </svg>
          </span>
          <span class="unfake-logo-text">Review Extracted Text</span>
        </div>
        <button class="unfake-close-btn" id="unfake-close" aria-label="Close">&times;</button>
      </div>
      <div class="unfake-modal-body">
        ${snippetUrl ? `
          <div class="unfake-ocr-preview-container">
            <img src="${snippetUrl}" alt="Cropped image" class="unfake-ocr-thumbnail">
          </div>
        ` : ""}
        <div class="unfake-ocr-confidence-row">
          <span class="unfake-ocr-label">Recognized Text</span>
          <span class="unfake-confidence-badge ${confClass}">
            ${confLabel}
          </span>
        </div>
        <textarea id="unfake-ocr-input" class="unfake-ocr-textarea" rows="4">${escapeHtml(text)}</textarea>
        <p class="unfake-ocr-hint">Review or correct any misread words before verifying.</p>

        <div class="unfake-btn-row">
          <button id="unfake-verify-ocr-btn" class="unfake-btn-primary">Verify Claim</button>
          <button id="unfake-cancel-ocr-btn" class="unfake-btn-secondary">Cancel</button>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);
    document.body.appendChild(modal);
    attachCloseHandler();

    const verifyBtn = document.getElementById("unfake-verify-ocr-btn");
    const cancelBtn = document.getElementById("unfake-cancel-ocr-btn");
    const inputArea = document.getElementById("unfake-ocr-input");

    if (cancelBtn) {
      cancelBtn.addEventListener("click", removeExisting);
    }

    if (verifyBtn && inputArea) {
      verifyBtn.addEventListener("click", () => {
        const claimText = inputArea.value.trim();
        if (!claimText) return;

        showLoading(claimText);
        chrome.runtime.sendMessage({
          action: "verify_claim",
          claim: claimText,
          inputType: "image_ocr",
        });
      });
    }

    requestAnimationFrame(() => {
      overlay.classList.add("unfake-visible");
      modal.classList.add("unfake-visible");
      if (inputArea) inputArea.focus();
    });
  }

  function showLoading(claim) {
    removeExisting();

    const overlay = createOverlay();
    const modal = createModal();

    modal.innerHTML = `
      <div class="unfake-modal-header">
        <div class="unfake-logo-row">
          <span class="unfake-logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0a192f" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="m9 12 2 2 4-4"/>
            </svg>
          </span>
          <span class="unfake-logo-text">UnFake</span>
        </div>
        <button class="unfake-close-btn" id="unfake-close" aria-label="Close">&times;</button>
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
    const isTriageRejected = result.status === "triage_rejected";
    const verdict = isError
      ? "error"
      : (isTriageRejected ? "triage_rejected" : (result.verdict || "unknown"));
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

    let tipHtml = "";
    if (isTriageRejected) {
      tipHtml = `
        <div class="unfake-triage-tip">
          💡 <strong>Tip:</strong> UnFake verifies empirical claims (dates, numbers, laws, official events). Highlight text containing a specific factual assertion to check it.
        </div>
      `;
    }

    modal.innerHTML = `
      <div class="unfake-modal-header">
        <div class="unfake-logo-row">
          <span class="unfake-logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0a192f" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="m9 12 2 2 4-4"/>
            </svg>
          </span>
          <span class="unfake-logo-text">UnFake</span>
        </div>
        <button class="unfake-close-btn" id="unfake-close" aria-label="Close">&times;</button>
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
        ${tipHtml}
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
      triage_rejected: "ℹ️ Not a Factual Claim",
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
      triage_rejected: "unfake-verdict-triage-rejected",
      error: "unfake-verdict-error",
    };
    return classes[verdict] || "unfake-verdict-insufficient";
  }
})();

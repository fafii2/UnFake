/**
 * UnFake Popup Script
 *
 * Handles:
 * - Backend health check on open
 * - Manual claim submission from the popup textarea
 */

const API_BASE = "http://localhost:8000";

// ── DOM Elements ────────────────────────────────────────────────────

const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const manualClaim = document.getElementById("manualClaim");
const verifyBtn = document.getElementById("verifyBtn");

// ── Backend Health Check ────────────────────────────────────────────

async function checkBackendStatus() {
  try {
    const response = await fetch(`${API_BASE}/api/v1/health`, { method: "GET", signal: AbortSignal.timeout(3000) });
    if (response.ok) {
      const data = await response.json();
      statusDot.className = "status-dot online";
      statusText.textContent = `Backend online (v${data.version})`;
    } else {
      setOffline("Backend returned an error");
    }
  } catch (err) {
    setOffline("Backend unreachable");
  }
}

function setOffline(message) {
  statusDot.className = "status-dot offline";
  statusText.textContent = message;
}

// ── Manual Claim Input ──────────────────────────────────────────────

manualClaim.addEventListener("input", () => {
  const hasText = manualClaim.value.trim().length > 0;
  verifyBtn.disabled = !hasText;
});

verifyBtn.addEventListener("click", async () => {
  const claim = manualClaim.value.trim();
  if (!claim) return;

  verifyBtn.disabled = true;
  verifyBtn.textContent = "Verifying...";

  try {
    // Send the claim to the background service worker,
    // which forwards it to the backend API
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    const response = await chrome.runtime.sendMessage({
      action: "verify_claim",
      claim: claim,
      inputType: "text",
      tabId: tab?.id,
    });

    if (response && response.success) {
      verifyBtn.textContent = "✓ Result shown on page";
      // The result modal is rendered by the content script
    } else {
      verifyBtn.textContent = "Error — try again";
      document.getElementById('actionStatus').textContent = response?.error || 'Verification failed. Please try again.';
      console.error("Verification failed:", response?.error);
    }
  } catch (err) {
    verifyBtn.textContent = "Error — try again";
    document.getElementById('actionStatus').textContent = err.message;
    console.error("Failed to send message:", err);
  }

  // Re-enable after a delay
  setTimeout(() => {
    verifyBtn.textContent = "Verify Claim";
    verifyBtn.disabled = manualClaim.value.trim().length === 0;
  }, 3000);
});

const cropBtn = document.getElementById("cropBtn");
if (cropBtn) {
  cropBtn.addEventListener("click", async () => {
    try {
      const response = await chrome.runtime.sendMessage({ action: "trigger_crop_from_popup" });
      if (!response?.success) throw new Error(response?.error || 'Cannot crop this page.');
      window.close();
    } catch (err) {
      console.error("[UnFake] Failed to trigger crop:", err);
      document.getElementById('actionStatus').textContent = err.message;
    }
  });
}

// ── Initialize ──────────────────────────────────────────────────────

checkBackendStatus();
document.getElementById('exampleBtn').addEventListener('click', () => {
  manualClaim.value = 'The BSP stores 400,000 tons of Tallano gold owned by Ferdinand Marcos Sr.';
  verifyBtn.disabled = false;
  manualClaim.focus();
});

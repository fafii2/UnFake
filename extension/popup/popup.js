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
    const response = await fetch(`${API_BASE}/`, { method: "GET" });
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
    const response = await chrome.runtime.sendMessage({
      action: "verify_claim",
      claim: claim,
      inputType: "text",
    });

    if (response && response.success) {
      verifyBtn.textContent = "✓ Result shown on page";
      // The result modal is rendered by the content script
    } else {
      verifyBtn.textContent = "Error — try again";
      console.error("Verification failed:", response?.error);
    }
  } catch (err) {
    verifyBtn.textContent = "Error — try again";
    console.error("Failed to send message:", err);
  }

  // Re-enable after a delay
  setTimeout(() => {
    verifyBtn.textContent = "Verify Claim";
    verifyBtn.disabled = manualClaim.value.trim().length === 0;
  }, 3000);
});

// ── Initialize ──────────────────────────────────────────────────────

checkBackendStatus();

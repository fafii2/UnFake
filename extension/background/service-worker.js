/**
 * UnFake — Background Service Worker
 *
 * Responsibilities:
 * 1. Create the right-click context menu item.
 * 2. Receive messages from content scripts and the popup.
 * 3. Send verification requests to the backend API.
 * 4. Forward results back to the content script for display.
 */

const API_BASE = "http://localhost:8000";
const VERIFY_ENDPOINT = `${API_BASE}/api/v1/verify`;

// ── Context Menu Setup ──────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "unfake-verify",
    title: "Verify with UnFake",
    contexts: ["selection"],
  });
  console.log("[UnFake] Context menu created.");
});

// ── Context Menu Click Handler ──────────────────────────────────────

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== "unfake-verify") return;

  const selectedText = info.selectionText;
  if (!selectedText || !selectedText.trim()) {
    console.warn("[UnFake] No text selected.");
    return;
  }

  console.log("[UnFake] Verifying selected text:", selectedText.substring(0, 100));

  // Tell the content script to show loading state
  await sendToContentScript(tab.id, {
    action: "show_loading",
    claim: selectedText.trim(),
  });

  // Call the backend
  const result = await callVerifyAPI(selectedText.trim(), "text");

  // Send the result to the content script for display
  await sendToContentScript(tab.id, {
    action: "show_result",
    result: result,
  });
});

// ── Message Listener (from popup and content scripts) ───────────────

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "verify_claim") {
    // Handle async response
    handleVerifyClaim(message, sender)
      .then(sendResponse)
      .catch((err) => {
        console.error("[UnFake] Verification error:", err);
        sendResponse({ success: false, error: err.message });
      });

    // Return true to indicate async response
    return true;
  }
});

async function handleVerifyClaim(message, sender) {
  const { claim, inputType } = message;
  const result = await callVerifyAPI(claim, inputType || "text");

  // If the message came from the popup, also send result to the active tab
  if (!sender.tab) {
    const [activeTab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });
    if (activeTab) {
      await sendToContentScript(activeTab.id, {
        action: "show_result",
        result: result,
      });
    }
  }

  return { success: !result.error, result };
}

// ── API Communication ───────────────────────────────────────────────

async function callVerifyAPI(claim, inputType) {
  try {
    const response = await fetch(VERIFY_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        claim: claim,
        input_type: inputType,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      return {
        error: true,
        status: "error",
        explanation: errorData?.message || `Backend error (HTTP ${response.status})`,
        original_claim: claim,
      };
    }

    return await response.json();
  } catch (err) {
    console.error("[UnFake] API call failed:", err);
    return {
      error: true,
      status: "error",
      explanation: `Could not reach the UnFake backend. Is it running at ${API_BASE}?`,
      original_claim: claim,
    };
  }
}

// ── Helper: Send message to content script ──────────────────────────

async function sendToContentScript(tabId, message) {
  try {
    await chrome.tabs.sendMessage(tabId, message);
  } catch (err) {
    console.warn("[UnFake] Could not reach content script:", err.message);
  }
}

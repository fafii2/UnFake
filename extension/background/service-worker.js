/**
 * UnFake — Background Service Worker
 *
 * Responsibilities:
 * 1. Register right-click context menus (text verification & image cropping).
 * 2. Coordinate viewport screenshots via chrome.tabs.captureVisibleTab.
 * 3. Manage offscreen document for Tesseract.js client-side OCR.
 * 4. Coordinate verification requests with the FastAPI backend.
 */

const API_BASE = "http://localhost:8000";
const VERIFY_ENDPOINT = `${API_BASE}/api/v1/verify`;

// ── Context Menu Setup ──────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(() => {
  // 1. Text selection verification
  chrome.contextMenus.create({
    id: "unfake-verify",
    title: "Verify Text with UnFake",
    contexts: ["selection"],
  });

  // 2. Image / Screenshot cropping verification
  chrome.contextMenus.create({
    id: "unfake-crop",
    title: "Verify Image / Screen Region",
    contexts: ["page", "image", "frame"],
  });

  console.log("[UnFake] Context menus initialized.");
});

// ── Context Menu Click Handler ──────────────────────────────────────

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "unfake-verify") {
    const selectedText = info.selectionText;
    if (!selectedText || !selectedText.trim()) return;

    await sendToContentScript(tab.id, {
      action: "show_loading",
      claim: selectedText.trim(),
    });

    const result = await callVerifyAPI(selectedText.trim(), "text");
    await sendToContentScript(tab.id, {
      action: "show_result",
      result: result,
    });
  } else if (info.menuItemId === "unfake-crop") {
    // Trigger the in-page cropping canvas
    await sendToContentScript(tab.id, {
      action: "start_crop",
    });
  }
});

// ── Message Listener ───────────────────────────────────────────────

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "verify_claim") {
    handleVerifyClaim(message, sender)
      .then(sendResponse)
      .catch((err) => {
        console.error("[UnFake] Verification error:", err);
        sendResponse({ success: false, error: err.message });
      });
    return true;
  }

  if (message.action === "crop_completed") {
    handleCropCompleted(message.cropArea, sender.tab)
      .then(sendResponse)
      .catch((err) => {
        console.error("[UnFake] Crop & OCR error:", err);
        sendResponse({ success: false, error: err.message });
      });
    return true;
  }

  if (message.action === "trigger_crop_from_popup") {
    handleTriggerCropFromPopup()
      .then(sendResponse)
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true;
  }
});

// ── Image Cropping & OCR Pipeline ───────────────────────────────────

async function handleCropCompleted(cropArea, tab) {
  if (!tab || !tab.id) {
    const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
    tab = activeTab;
  }
  if (!tab || !tab.id) return { success: false, error: "No active tab found" };

  // 1. Show OCR progress loading state on page
  await sendToContentScript(tab.id, { action: "show_ocr_loading" });

  try {
    // 2. Capture high-resolution viewport screenshot
    const screenshotUrl = await chrome.tabs.captureVisibleTab(tab.windowId || null, {
      format: "png",
    });

    // 3. Ensure the offscreen OCR worker document exists
    await ensureOffscreenDocument();

    // 4. Send to offscreen document for canvas cropping & Tesseract recognition
    const ocrResponse = await chrome.runtime.sendMessage({
      action: "process_image_ocr",
      screenshotUrl: screenshotUrl,
      cropArea: cropArea,
    });

    if (!ocrResponse || !ocrResponse.success) {
      throw new Error(ocrResponse?.error || "OCR recognition failed.");
    }

    // 5. Send recognized text and snippet to content script for user review
    await sendToContentScript(tab.id, {
      action: "show_ocr_review",
      data: {
        text: ocrResponse.text,
        confidence: ocrResponse.confidence,
        snippetUrl: ocrResponse.snippetUrl,
      },
    });

    return { success: true };
  } catch (err) {
    console.error("[UnFake] Image OCR processing failed:", err);
    await sendToContentScript(tab.id, {
      action: "show_result",
      result: {
        error: true,
        status: "error",
        explanation: `Image OCR failed: ${err.message}`,
        original_claim: "Cropped image region",
      },
    });
    return { success: false, error: err.message };
  }
}

async function handleTriggerCropFromPopup() {
  const [activeTab] = await chrome.tabs.query({
    active: true,
    currentWindow: true,
  });
  if (activeTab && activeTab.id) {
    await sendToContentScript(activeTab.id, { action: "start_crop" });
  }
  return { success: true };
}

// ── Offscreen Document Manager ──────────────────────────────────────

let creatingOffscreen = null;

async function ensureOffscreenDocument() {
  const offscreenUrl = chrome.runtime.getURL("offscreen/offscreen.html");

  if (typeof chrome.runtime.getContexts === "function") {
    try {
      const existingContexts = await chrome.runtime.getContexts({
        contextTypes: ["OFFSCREEN_DOCUMENT"],
        documentUrls: [offscreenUrl],
      });
      if (existingContexts && existingContexts.length > 0) return;
    } catch (e) {
      // getContexts fallback
    }
  }

  if (creatingOffscreen) {
    await creatingOffscreen;
    return;
  }

  try {
    creatingOffscreen = chrome.offscreen.createDocument({
      url: "offscreen/offscreen.html",
      reasons: ["DOM_PARSER", "BLOBS"],
      justification: "Run local Tesseract.js OCR and canvas cropping",
    });
    await creatingOffscreen;
  } catch (err) {
    if (!err.message || !err.message.includes("Only a single offscreen")) {
      throw err;
    }
  } finally {
    creatingOffscreen = null;
  }
}

// ── Claim Verification Handler ──────────────────────────────────────

async function handleVerifyClaim(message, sender) {
  const { claim, inputType } = message;
  const result = await callVerifyAPI(claim, inputType || "text");

  // Determine target tab to display result
  let targetTabId = sender?.tab?.id;
  if (!targetTabId) {
    const [activeTab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });
    targetTabId = activeTab?.id;
  }

  if (targetTabId) {
    await sendToContentScript(targetTabId, {
      action: "show_result",
      result: result,
    });
  }

  return { success: !result.error, result };
}

// ── Backend API Communication ───────────────────────────────────────

async function callVerifyAPI(claim, inputType) {
  try {
    const response = await fetch(VERIFY_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        claim: claim,
        input_type: inputType || "text",
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      let detailMsg = errorData?.detail || errorData?.message;
      if (Array.isArray(detailMsg)) {
        detailMsg = detailMsg.map((d) => d.msg || JSON.stringify(d)).join("; ");
      } else if (typeof detailMsg === "object" && detailMsg !== null) {
        detailMsg = JSON.stringify(detailMsg);
      }
      return {
        error: true,
        status: "error",
        explanation: detailMsg || `Backend error (HTTP ${response.status})`,
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

// ── Helper: Send message to content script with auto-injection ──────

async function sendToContentScript(tabId, message) {
  try {
    await chrome.tabs.sendMessage(tabId, message);
  } catch (err) {
    console.warn("[UnFake] Direct message to content script failed, attempting script injection:", err.message);
    try {
      if (chrome.scripting) {
        await chrome.scripting.insertCSS({
          target: { tabId: tabId },
          files: ["content/content.css"],
        });
        await chrome.scripting.executeScript({
          target: { tabId: tabId },
          files: [
            "content/text-selection.js",
            "content/image-crop.js",
            "content/content.js",
          ],
        });
        // Retry message after dynamic injection
        await chrome.tabs.sendMessage(tabId, message);
      }
    } catch (injErr) {
      console.warn("[UnFake] Script injection not possible on tab:", injErr.message);
    }
  }
}

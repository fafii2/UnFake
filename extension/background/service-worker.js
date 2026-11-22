/**
 * UnFake — Background Service Worker
 *
 * Responsibilities:
 * 1. Register right-click context menus (text verification & image cropping).
 * 2. Coordinate viewport screenshots via chrome.tabs.captureVisibleTab.
 * 3. Manage offscreen document for Tesseract.js client-side OCR.
 * 4. Coordinate verification requests with the FastAPI backend.
 */

importScripts('../shared/rules.js', '../shared/claims.js');

const API_BASE = "http://127.0.0.1:8001";
const VERIFY_ENDPOINT = `${API_BASE}/api/v1/verifications`;
const pendingRequests = new Map();

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

    await handleVerifyClaim({claim: selectedText.trim(), inputType: 'text'}, {tab}).catch(err => {
      console.warn('[UnFake] Cannot verify on this page:', err.message);
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
  if (message.action === "upload_screenshot") {
    handleUploadedScreenshot(message, sender)
      .then(sendResponse)
      .catch(err => sendResponse({success: false, error: err.message}));
    return true;
  }
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

  try {
    const assertActive = async () => {
      const [active] = await chrome.tabs.query({active: true, windowId: tab.windowId});
      if (active?.id !== tab.id) throw new Error('Return to the selected tab and crop again.');
    };
    await assertActive();
    // Wait for the page to paint after removing all extension overlays.
    await sendToContentScript(tab.id, {action: 'prepare_capture'});
    await assertActive();
    const screenshotUrl = await chrome.tabs.captureVisibleTab(tab.windowId || null, {
      format: "png",
    });
    await sendToContentScript(tab.id, { action: 'show_ocr_loading' });

    await recognizeAndReview(tab.id, screenshotUrl, cropArea);

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

async function handleUploadedScreenshot(message, sender) {
  const tabId = sender?.tab?.id ?? message.tabId;
  if (tabId == null) throw new Error('Open a news or Facebook page first.');
  if (typeof message.imageUrl !== 'string' ||
      !/^data:image\/(png|jpeg|webp);base64,/.test(message.imageUrl) ||
      message.imageUrl.length > 7 * 1024 * 1024) {
    throw new Error('Choose a PNG, JPEG, or WebP screenshot under 5 MB.');
  }
  // Null means recognize the whole image. Dimensions are validated locally.
  await sendToContentScript(tabId, {action: 'show_ocr_loading'});
  try {
    await recognizeAndReview(tabId, message.imageUrl, null);
    return {success: true};
  } catch (err) {
    await sendToContentScript(tabId, {action: 'show_result', result: {
      error: true, status: 'error', explanation: `Image OCR failed: ${err.message}`,
      original_claim: 'Uploaded screenshot',
    }});
    return {success: false, error: err.message};
  }
}

async function recognizeAndReview(tabId, screenshotUrl, cropArea) {
  await ensureOffscreenDocument();
  const result = await chrome.runtime.sendMessage({
    action: 'process_image_ocr', screenshotUrl, cropArea,
  });
  if (!result?.success) throw new Error(result?.error || 'OCR recognition failed.');
  await sendToContentScript(tabId, {action: 'show_ocr_review', data: {
    text: result.text, confidence: result.confidence, snippetUrl: result.snippetUrl,
  }});
}

async function handleTriggerCropFromPopup() {
  const [activeTab] = await chrome.tabs.query({
    active: true,
    currentWindow: true,
  });
  if (activeTab && activeTab.id) {
    await sendToContentScript(activeTab.id, { action: "start_crop" });
  } else throw new Error('No active page found.');
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
      reasons: ["WORKERS", "BLOBS"],
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
  // Resolve the initiating tab before waiting on any network request.
  let targetTabId = sender?.tab?.id ?? message.tabId;
  if (targetTabId == null) {
    const [activeTab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });
    targetTabId = activeTab?.id;
  }

  if (targetTabId == null) throw new Error('Open a regular webpage to display verification results.');
  const requestId = crypto.randomUUID();
  pendingRequests.set(targetTabId, requestId);
  try {
    await sendToContentScript(targetTabId, {action: 'show_loading', claim, requestId});
    const result = await callVerifyAPI(claim, inputType || 'text');
    if (pendingRequests.get(targetTabId) !== requestId) return {success: false, error: 'A newer verification replaced this request.'};
    await sendToContentScript(targetTabId, {action: 'show_result', result, requestId});
    return {success: !result.error, result, error: result.error ? result.explanation : undefined};
  } finally {
    if (pendingRequests.get(targetTabId) === requestId) pendingRequests.delete(targetTabId);
  }
}

// ── Backend API Communication ───────────────────────────────────────

async function callVerifyAPI(claim, inputType) {
  const started = performance.now();
  const normalized = UnFakeClaims.normalize(claim);
  if (!normalized || typeof claim !== 'string' || claim.length > 5000) {
    return {error: true, status: 'error', explanation: 'Enter a claim containing 1 to 5,000 characters.', original_claim: claim};
  }
  const triage = UnFakeClaims.triage(normalized);
  if (!triage.is_verifiable) {
    return {status: 'triage_rejected', verdict: null, confidence: null, triage, evidence: [],
      explanation: `This text was not submitted for verification. ${triage.reason}`,
      original_claim: claim.trim(), processing_time_ms: Math.round(performance.now() - started),
      evaluation_method: 'client_triage', warnings: []};
  }
  try {
    const response = await fetch(VERIFY_ENDPOINT, {
      method: "POST",
      signal: AbortSignal.timeout(10000),
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

    let data = await response.json();
    const deadline = performance.now() + 85000;
    while (data.status === 'pending') {
      if (typeof data.id !== 'string' || !/^[a-f0-9]{32}$/.test(data.id)) throw new Error('Invalid verification response.');
      if (performance.now() > deadline) return {
        error: true, status: 'error', original_claim: claim,
        explanation: 'Verification timed out. The live services may be busy; please try again.',
      };
      await new Promise(resolve => setTimeout(resolve, 1000));
      const poll = await fetch(`${VERIFY_ENDPOINT}/${data.id}`, {signal: AbortSignal.timeout(10000)});
      if (!poll.ok) return {
        error: true, status: 'error', original_claim: claim,
        explanation: 'Verification was interrupted or the backend restarted. Please try again.',
      };
      data = await poll.json();
    }
    if (data.status === 'error') return {error: true, status: 'error', original_claim: claim,
      explanation: data.error || 'Verification failed. Please try again.'};
    return data.result || data;
  } catch (err) {
    console.error("[UnFake] API call failed:", err);
    return {
      error: true,
      status: "error",
      explanation: err.name === 'TimeoutError' || err.name === 'AbortError'
        ? 'Verification timed out. Please try again.'
        : `Could not reach the UnFake backend. Is it running at ${API_BASE}?`,
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
      } else throw new Error('Page access is unavailable.');
    } catch (injErr) {
      console.warn("[UnFake] Script injection not possible on tab:", injErr.message);
      throw new Error('UnFake cannot display results on this page. Open a regular HTTP or HTTPS webpage and try again.');
    }
  }
}

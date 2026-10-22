/**
 * UnFake — Offscreen Document OCR Engine
 *
 * Runs inside the extension's privileged origin (chrome-extension://),
 * completely bypassing host website CSP restrictions.
 *
 * Responsibilities:
 * 1. Crop screenshot data URL to the user's selected bounding box.
 * 2. Execute local Tesseract.js worker with offline eng traineddata.
 * 3. Return recognized text, confidence score, and cropped image snippet.
 */

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "process_image_ocr") {
    handleOcr(message.screenshotUrl, message.cropArea)
      .then(sendResponse)
      .catch((err) => {
        console.error("[UnFake OCR Error]", err);
        sendResponse({ success: false, error: err.message });
      });

    return true; // Keep message port open for async response
  }
});

async function handleOcr(screenshotUrl, cropArea) {
  // 1. Crop image on canvas taking viewport scaling into account
  const croppedDataUrl = await cropImage(screenshotUrl, cropArea);

  // 2. Resolve offline asset paths from extension bundle
  const workerPath = chrome.runtime.getURL("lib/worker.min.js");
  const corePath = chrome.runtime.getURL("lib/tesseract-core-lstm.wasm.js");
  const langPath = chrome.runtime.getURL("lib/tessdata");

  console.log("[UnFake OCR] Initializing Tesseract.js worker with workerBlobURL: false...");
  const worker = await Tesseract.createWorker("eng", 1, {
    workerPath: workerPath,
    corePath: corePath,
    langPath: langPath,
    workerBlobURL: false, // Required for Manifest V3 local worker loading
    gzip: true,
    logger: (m) => {
      if (m.status === "recognizing text") {
        console.log(`[UnFake OCR] Progress: ${Math.round((m.progress || 0) * 100)}%`);
      }
    },
  });

  console.log("[UnFake OCR] Recognizing text...");
  let result;
  try {
    result = await worker.recognize(croppedDataUrl);
  } finally {
    await worker.terminate();
  }

  const recognizedText = (result.data && result.data.text) ? result.data.text.trim() : "";
  const confidence = Math.round((result.data && result.data.confidence) || 0);

  console.log(`[UnFake OCR] Complete (${confidence}% recognition confidence).`);

  return {
    success: true,
    text: recognizedText,
    confidence: confidence,
    snippetUrl: croppedDataUrl,
  };
}

function cropImage(screenshotUrl, cropArea) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      try {
        const vpWidth = cropArea.viewportWidth || (cropArea.width > 0 ? (cropArea.x + cropArea.width) : 1);
        const vpHeight = cropArea.viewportHeight || (cropArea.height > 0 ? (cropArea.y + cropArea.height) : 1);

        const scaleX = img.naturalWidth / vpWidth;
        const scaleY = img.naturalHeight / vpHeight;

        const sx = Math.max(0, Math.round(cropArea.x * scaleX));
        const sy = Math.max(0, Math.round(cropArea.y * scaleY));
        const sWidth = Math.min(img.naturalWidth - sx, Math.round(cropArea.width * scaleX));
        const sHeight = Math.min(img.naturalHeight - sy, Math.round(cropArea.height * scaleY));

        if (sWidth <= 0 || sHeight <= 0) {
          return reject(new Error("Selected crop area is too small or invalid."));
        }

        const canvas = document.createElement("canvas");
        canvas.width = sWidth;
        canvas.height = sHeight;

        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, sx, sy, sWidth, sHeight, 0, 0, sWidth, sHeight);

        resolve(canvas.toDataURL("image/png"));
      } catch (err) {
        reject(err);
      }
    };
    img.onerror = () => reject(new Error("Failed to load viewport screenshot for cropping."));
    img.src = screenshotUrl;
  });
}

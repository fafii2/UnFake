/**
 * UnFake — Interactive Image & Screen Region Cropper
 *
 * Injects a responsive canvas overlay onto the active page,
 * allowing users to drag a selection rectangle over quote cards,
 * infographics, or altered screenshots.
 */

window.UnFakeCrop = window.UnFakeCrop || (() => {
  let activeOverlay = null;
  let activeCleanup = null;

  function startCrop(onComplete) {
    if (activeOverlay) cancelCrop();

    // 1. Create full-viewport container
    const container = document.createElement("div");
    container.id = "unfake-crop-container";
    container.className = "unfake-crop-container";

    const canvas = document.createElement("canvas");
    canvas.id = "unfake-crop-canvas";
    canvas.className = "unfake-crop-canvas";

    const hint = document.createElement("div");
    hint.id = "unfake-crop-hint";
    hint.className = "unfake-crop-hint";
    hint.innerHTML = `<span>Drag to select image or quote card • Press <strong>Esc</strong> to cancel</span>`;

    container.appendChild(canvas);
    container.appendChild(hint);
    document.body.appendChild(container);
    activeOverlay = container;

    // 2. Size canvas to match window viewport
    const width = window.innerWidth;
    const height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");

    // Initial dark wash
    drawOverlay(ctx, width, height, null);

    let isDragging = false;
    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let currentY = 0;

    function onMouseDown(e) {
      if (e.button !== 0) return; // Left click only
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      currentX = e.clientX;
      currentY = e.clientY;
      hint.style.opacity = "0.3";
    }

    function onMouseMove(e) {
      if (!isDragging) return;
      currentX = e.clientX;
      currentY = e.clientY;

      const rect = getNormalizedRect(startX, startY, currentX, currentY);
      drawOverlay(ctx, width, height, rect);
    }

    function onMouseUp(e) {
      if (!isDragging) return;
      isDragging = false;
      currentX = Math.max(0, Math.min(width, e.clientX));
      currentY = Math.max(0, Math.min(height, e.clientY));

      const rect = getNormalizedRect(startX, startY, currentX, currentY);
      cleanup();

      // Ignore accidental tiny clicks (< 20px)
      if (rect.width < 20 || rect.height < 20) {
        return;
      }

      if (typeof onComplete === "function") {
        onComplete({
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
          viewportWidth: window.innerWidth,
          viewportHeight: window.innerHeight,
          devicePixelRatio: window.devicePixelRatio || 1,
        });
      }
    }

    function onKeyDown(e) {
      if (e.key === "Escape") {
        cleanup();
      }
    }

    function cleanup() {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener('resize', cleanup);
      activeCleanup = null;
      if (activeOverlay) {
        activeOverlay.remove();
        activeOverlay = null;
      }
    }

    canvas.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener('resize', cleanup, {once: true});
    activeCleanup = cleanup;
  }

  function cancelCrop() {
    if (activeCleanup) { activeCleanup(); return; }
    if (activeOverlay) {
      activeOverlay.remove();
      activeOverlay = null;
    }
  }

  function getNormalizedRect(x1, y1, x2, y2) {
    const x = Math.min(x1, x2);
    const y = Math.min(y1, y2);
    const width = Math.abs(x2 - x1);
    const height = Math.abs(y2 - y1);
    return { x, y, width, height };
  }

  function drawOverlay(ctx, width, height, rect) {
    ctx.clearRect(0, 0, width, height);

    // 1. Dark semi-transparent mask
    ctx.fillStyle = "rgba(10, 25, 47, 0.55)";
    ctx.fillRect(0, 0, width, height);

    if (!rect || rect.width <= 0 || rect.height <= 0) return;

    // 2. Clear out the selected rectangle so it's bright & visible
    ctx.clearRect(rect.x, rect.y, rect.width, rect.height);

    // 3. Draw border
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.strokeRect(rect.x, rect.y, rect.width, rect.height);

    ctx.strokeStyle = "#1e3a8a";
    ctx.lineWidth = 1;
    ctx.strokeRect(rect.x - 1, rect.y - 1, rect.width + 2, rect.height + 2);

    // 4. Draw corner handles
    const handleSize = 8;
    ctx.fillStyle = "#1e3a8a";

    // Top-left, top-right, bottom-left, bottom-right
    ctx.fillRect(rect.x - 4, rect.y - 4, handleSize, handleSize);
    ctx.fillRect(rect.x + rect.width - 4, rect.y - 4, handleSize, handleSize);
    ctx.fillRect(rect.x - 4, rect.y + rect.height - 4, handleSize, handleSize);
    ctx.fillRect(rect.x + rect.width - 4, rect.y + rect.height - 4, handleSize, handleSize);

    // 5. Dimension tag
    const dimText = `${Math.round(rect.width)} × ${Math.round(rect.height)} px`;
    ctx.font = "bold 11px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
    const textWidth = ctx.measureText(dimText).width;

    const tagX = rect.x;
    const tagY = rect.y + rect.height + 6;

    ctx.fillStyle = "rgba(10, 25, 47, 0.85)";
    ctx.beginPath();
    ctx.roundRect(tagX, tagY, textWidth + 12, 20, 4);
    ctx.fill();

    ctx.fillStyle = "#ffffff";
    ctx.fillText(dimText, tagX + 6, tagY + 14);
  }

  return {
    startCrop,
    cancelCrop,
  };
})();

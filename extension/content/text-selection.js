/**
 * UnFake — Text Selection Utility
 *
 * Captures the user's text selection on the active page.
 * Used by the content script and triggered by the context menu.
 */

globalThis.UnFakeSelection = globalThis.UnFakeSelection || {
  /**
   * Get the currently selected text on the page.
   * @returns {string} The selected text, trimmed.
   */
  getSelectedText() {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
      return "";
    }
    return selection.toString().trim();
  },
};

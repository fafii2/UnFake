/** Client-side normalization and triage. Vocabulary is generated from Python rules. */
(() => {
  const rules = globalThis.UnFakeRules;
  const find = (name, text) => new RegExp(rules[name], 'i').exec(text);
  const strip = (text) => {
    text = text.trim();
    const pairs = [['"', '"'], ["'", "'"], ['[', ']'], ['(', ')']];
    return pairs.some(([a,b]) => text.length >= 2 && text.startsWith(a) && text.endsWith(b)) ? text.slice(1,-1).trim() : text;
  };
  function normalize(raw) {
    let text = String(raw || '').normalize('NFC');
    const noise = /^(?:(?:like|reply|share|see more|see less)|\d+\s*(?:h|hr|hrs|min|mins)\s*(?:ago)?|\[?\d{1,2}:\d{2}\s*(?:am|pm)?\]?)$/i;
    text = text.split(/\r?\n/).filter(line => !noise.test(line.trim())).join('\n');
    text = text.replace(/[“”„«»]/g, '"').replace(/[‘’`‚]/g, "'").replace(/\s+/g, ' ').trim();
    text = strip(text).replace(/^(?:[-*•]|\d+[.)])\s+(?=\S)/, '');
    text = text.replace(new RegExp(rules.BROADCAST_PREFIXES_REGEX, 'i'), '').trim();
    return strip(text).replace(/\?{2,}/g, '?').replace(/!{2,}/g, '!').replace(/\.{4,}/g, '...').trim();
  }
  function triage(text) {
    text = text.trim();
    const words = text.split(/\s+/).filter(Boolean);
    const result = (is_verifiable, category, reason) => ({is_verifiable, category, reason});
    const short = words.length === 3 && /\b(?:is|are|was|were|ay)\b/i.test(text);
    if (words.length < 4 && !short) return result(false, 'TOO_SHORT', 'Text is too short to form a verifiable factual assertion.');
    const entity = find('NAMED_ENTITIES_PATTERN', text);
    const metric = find('METRICS_PATTERN', text);
    const action = find('VERIFIABLE_PREDICATES_PATTERN', text);
    const time = find('TEMPORAL_PATTERN', text);
    if (find('CASUAL_SLANG_PATTERN', text) && !entity && !metric && !action) {
      return result(false, 'CASUAL_COMMENTARY', 'Text contains informal commentary or slang without factual anchors.');
    }
    if (text.endsWith('?') || ((find('QUESTION_STARTERS_PATTERN', text) || find('EMBEDDED_QUESTION_PATTERN', text)) && !action)) {
      return result(false, 'QUESTION', 'Text is phrased as a question rather than a factual assertion.');
    }
    const opinion = find('OPINION_MARKERS_PATTERN', text);
    const opinions = [...text.matchAll(new RegExp(rules.OPINION_MARKERS_PATTERN, 'ig'))];
    const qualified = opinion && /^(?:i\s+think|i\s+believe|sa\s+tingin\s+ko|naniniwala\s+ako)$/i.test(opinion[0]) && action && entity && (time || metric) && opinions.length === 1;
    if (opinion && !qualified) return result(false, 'OPINION', 'Text expresses a personal opinion or value judgment.');
    const anchors = [entity, metric, time, action].filter(Boolean).length;
    if ((find('ATTRIBUTION_MARKERS_PATTERN', text) || qualified) && anchors) {
      return result(true, 'UNCERTAIN_BORDERLINE', 'Claim contains an attributed, qualified or reported assertion.');
    }
    if (anchors || short) return result(true, 'FACTUAL_ASSERTION', 'Verifiable factual indicators were found.');
    if (words.length >= 5) return result(true, 'UNCERTAIN_BORDERLINE', 'Declarative statement; proceeding as a borderline claim.');
    return result(false, 'OPINION', 'Text does not contain sufficient verifiable factual indicators.');
  }
  globalThis.UnFakeClaims = {normalize, triage};
})();

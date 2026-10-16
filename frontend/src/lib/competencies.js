/**
 * KaushalTwin — Competency Normalization & Validation Utility
 * Adheres to zero-fabrication principle: does not invent fake records or synthetic scores.
 */

export function normalizeCompetency(c) {
  if (!c || typeof c !== 'object') return null;
  const name = c.competency_name || c.name || '';
  const nosId = c.nos_id || c.code || '';
  if (!name && !nosId) return null;

  // Validate score: must be a real number
  if (typeof c.score !== 'number' || isNaN(c.score)) {
    return null;
  }

  // Normalize score to 0 - 100
  let score = c.score;
  if (score > 0 && score <= 1) {
    score = Math.round(score * 100);
  } else {
    score = Math.round(score);
  }
  score = Math.max(0, Math.min(100, score));

  // Normalize benchmark (standard NSQF threshold is 70% if not specified)
  let benchmark = 70;
  if (typeof c.benchmark === 'number' && !isNaN(c.benchmark)) {
    benchmark = c.benchmark > 0 && c.benchmark <= 1 ? Math.round(c.benchmark * 100) : Math.round(c.benchmark);
    benchmark = Math.max(0, Math.min(100, benchmark));
  }

  const isProficient = score >= benchmark;
  const variance = score - benchmark;

  // Short label for axes without cutting off critical identifying prefix
  const shortName = name.length > 20 ? `${name.slice(0, 18)}...` : (name || nosId);

  return {
    ...c,
    nos_id: nosId,
    competency_name: name,
    displayName: nosId ? `${nosId} — ${name}` : name,
    shortName,
    score,
    benchmark,
    isProficient,
    variance,
    evidence_count: typeof c.evidence_count === 'number' ? c.evidence_count : 0,
    status: c.status || (isProficient ? 'AI Match Met' : 'Evidence Deficit'),
  };
}

/**
 * Cleanly wraps competency titles across up to 2 lines to prevent truncation.
 * Words are preserved where possible; single words exceeding line budget are cleanly truncated.
 */
export function wrapText(text, maxCharsPerLine = 26) {
  if (!text || typeof text !== 'string') return [];
  const trimmed = text.trim();
  if (!trimmed) return [];

  const words = trimmed.split(/\s+/);
  const lines = [];
  let currentLine = '';

  for (const word of words) {
    let safeWord = word;
    if (safeWord.length > maxCharsPerLine) {
      safeWord = safeWord.slice(0, maxCharsPerLine - 3) + '...';
    }

    if (!currentLine) {
      currentLine = safeWord;
    } else if ((currentLine + ' ' + safeWord).length <= maxCharsPerLine) {
      currentLine += ' ' + safeWord;
    } else {
      lines.push(currentLine);
      currentLine = safeWord;
    }
  }

  if (currentLine) {
    lines.push(currentLine);
  }

  // Cap at 2 lines for chart row aesthetic; if 3rd line exists, append ellipsis to line 2
  if (lines.length > 2) {
    const firstLine = lines[0];
    const remaining = lines.slice(1).join(' ');
    const secondLine =
      remaining.length > maxCharsPerLine
        ? remaining.slice(0, maxCharsPerLine - 3) + '...'
        : remaining;
    return [firstLine, secondLine];
  }

  return lines;
}

export default { normalizeCompetency, wrapText };


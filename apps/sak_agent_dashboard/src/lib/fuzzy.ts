/**
 * Subsequence matching for the command palette.
 *
 * A plain `includes()` fails the thing people actually type: "usd" for "Use
 * sample data", "ar" for "Auto-refresh". This matches the query's characters
 * in order anywhere in the haystack, scores how good the match was, and hands
 * back the matched positions so the row can show *why* it matched.
 *
 * Deliberately not a dependency: the corpus is a dozen commands, and the whole
 * algorithm is forty lines with no allocation per keystroke beyond one array.
 */

export interface FuzzyMatch {
  /** Higher is better. Only meaningful relative to other matches. */
  score: number;
  /** Indices into the haystack that the query matched, ascending. */
  positions: number[];
}

/** A word boundary is the start, or a character after a separator. */
function isBoundary(text: string, index: number): boolean {
  if (index === 0) return true;
  const previous = text[index - 1]!;
  return previous === " " || previous === "-" || previous === "_" || previous === "·";
}

/**
 * Match `query` against `text`, case-insensitively.
 *
 * Returns null when the query is not a subsequence of the text. An empty query
 * matches everything with a score of 0, which is what keeps an unfiltered
 * palette in its declared order.
 */
export function fuzzyMatch(query: string, text: string): FuzzyMatch | null {
  const needle = query.trim().toLowerCase();
  if (needle === "") return { score: 0, positions: [] };

  const haystack = text.toLowerCase();
  const positions: number[] = [];

  let score = 0;
  let cursor = 0;
  let previousIndex = -2;

  for (const character of needle) {
    if (character === " ") continue; // spaces separate terms; they match nothing
    const index = haystack.indexOf(character, cursor);
    if (index === -1) return null;

    // Consecutive characters and word-initial characters are what make a match
    // feel intentional rather than coincidental, so both are worth more than a
    // character found halfway through some later word.
    if (index === previousIndex + 1) score += 8;
    if (isBoundary(text, index)) score += 6;
    score += 1;
    // The further into the string the match starts, the weaker it is.
    if (positions.length === 0) score -= Math.min(index, 10) * 0.5;

    positions.push(index);
    previousIndex = index;
    cursor = index + 1;
  }

  // A query that covers most of a short label beats one buried in a long one.
  score += (positions.length / haystack.length) * 6;
  return { score, positions };
}

/**
 * Split `text` into runs, marking which characters the query matched.
 *
 * The palette renders these directly; keeping the split here means the
 * highlighting is testable without rendering anything.
 */
export function highlightSegments(
  text: string,
  positions: readonly number[],
): { text: string; matched: boolean }[] {
  if (positions.length === 0) return [{ text, matched: false }];

  const marked = new Set(positions);
  const segments: { text: string; matched: boolean }[] = [];

  for (let index = 0; index < text.length; index += 1) {
    const matched = marked.has(index);
    const last = segments[segments.length - 1];
    if (last && last.matched === matched) {
      last.text += text[index];
    } else {
      segments.push({ text: text[index]!, matched });
    }
  }

  return segments;
}

/**
 * Rank `items` against a query, best first.
 *
 * `fields` are tried in order and the best-scoring one wins, so a label match
 * outranks a description match without the caller weighting them itself. The
 * order of equally-scoring items is preserved (`Array.prototype.sort` is
 * stable), which is what keeps "Go to" above "Actions" on an empty query.
 */
export function rankBy<T>(
  items: readonly T[],
  query: string,
  fields: (item: T) => readonly string[],
): { item: T; match: FuzzyMatch; fieldIndex: number }[] {
  const ranked: { item: T; match: FuzzyMatch; fieldIndex: number }[] = [];

  for (const item of items) {
    let best: { match: FuzzyMatch; fieldIndex: number } | null = null;
    fields(item).forEach((field, fieldIndex) => {
      const match = fuzzyMatch(query, field);
      if (!match) return;
      // A later field is a weaker signal: a hit in the description is worth
      // less than the same hit in the label.
      const adjusted = { ...match, score: match.score - fieldIndex * 4 };
      if (!best || adjusted.score > best.match.score) {
        best = { match: adjusted, fieldIndex };
      }
    });
    if (best) ranked.push({ item, ...(best as { match: FuzzyMatch; fieldIndex: number }) });
  }

  return ranked.sort((a, b) => b.match.score - a.match.score);
}

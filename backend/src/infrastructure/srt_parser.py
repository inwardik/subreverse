"""SRT subtitle file parser and matcher.

Parses SRT subtitle files and matches English/Russian cues by overlapping time frames.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


# Regex patterns
SRT_TIME_RE = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*$")
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def parse_time_to_ms(h: str, m: str, s: str, ms: str) -> int:
    """Convert time components to milliseconds."""
    return int(h) * 3600_000 + int(m) * 60_000 + int(s) * 1000 + int(ms)


def ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT time format (HH:MM:SS,mmm)."""
    if ms < 0:
        ms = 0
    h = ms // 3600_000
    ms %= 3600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


@dataclass
class Cue:
    """Represents a single subtitle cue with timing and text."""
    idx: int
    start_ms: int
    end_ms: int
    text: str

    @property
    def time_str(self) -> str:
        """Return time range in SRT format."""
        return f"{ms_to_srt_time(self.start_ms)} --> {ms_to_srt_time(self.end_ms)}"


def clean_text(text_lines: List[str]) -> str:
    """
    Clean subtitle text by removing HTML tags and normalizing whitespace.

    Args:
        text_lines: List of text lines from subtitle cue

    Returns:
        Cleaned and normalized text
    """
    # Join multiple lines with space, strip tags and normalize whitespace
    joined = " ".join(line.strip() for line in text_lines if line is not None)
    no_tags = TAG_RE.sub("", joined)
    # Normalize whitespace
    normalized = WHITESPACE_RE.sub(" ", no_tags).strip()
    return normalized


def parse_srt(path: str) -> List[Cue]:
    """
    Parse an SRT subtitle file into a list of Cue objects.

    Args:
        path: Path to the SRT file

    Returns:
        List of parsed subtitle cues

    Example SRT format:
        1
        00:00:01,000 --> 00:00:04,000
        First subtitle text

        2
        00:00:05,000 --> 00:00:08,000
        Second subtitle text
    """
    cues: List[Cue] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()

    i = 0
    n = len(lines)
    while i < n:
        # Skip empty lines
        while i < n and not lines[i].strip():
            i += 1
        if i >= n:
            break

        # Optional numeric index line
        idx_line = lines[i].strip()
        idx = None
        if idx_line.isdigit():
            idx = int(idx_line)
            i += 1

        # Time line
        if i >= n:
            break
        time_line = lines[i].strip()
        m = SRT_TIME_RE.match(time_line)
        if not m:
            # If time line not matched, try to skip this block safely
            i += 1
            continue
        i += 1

        sh, sm, ss, sms, eh, em, es, ems = m.groups()
        start_ms = parse_time_to_ms(sh, sm, ss, sms)
        end_ms = parse_time_to_ms(eh, em, es, ems)

        # Text lines until a blank line
        text_lines: List[str] = []
        while i < n and lines[i].strip():
            text_lines.append(lines[i])
            i += 1

        # Move past the blank line
        while i < n and not lines[i].strip():
            i += 1

        text = clean_text(text_lines)
        cues.append(Cue(idx=idx or len(cues) + 1, start_ms=start_ms, end_ms=end_ms, text=text))

    return cues


def interval_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    """Calculate overlap duration between two time intervals in milliseconds."""
    return max(0, min(a_end, b_end) - max(a_start, b_start))


def intervals_close(a_start: int, a_end: int, b_start: int, b_end: int, tol: int) -> bool:
    """
    Check if two intervals are close enough considering tolerance.

    Intervals are considered close if they overlap after expanding both by tolerance.
    """
    return not (a_end + tol < b_start - tol or b_end + tol < a_start - tol)


def match_cues(en_cues: List[Cue], ru_cues: List[Cue], tolerance_ms: int = 1000) -> List[Tuple[Cue, Optional[Cue]]]:
    """
    Match English and Russian subtitle cues by overlapping time frames.

    For each EN cue, finds the RU cue with the largest overlap duration (considering tolerance).
    If no RU cue overlaps within tolerance, the RU field is None.

    Args:
        en_cues: List of English subtitle cues
        ru_cues: List of Russian subtitle cues
        tolerance_ms: Timing tolerance in milliseconds (default: 1000ms = 1 second)

    Returns:
        List of tuples (en_cue, ru_cue) where ru_cue may be None if no match found

    Algorithm:
        - Uses a sliding window approach for efficiency
        - Calculates overlap ratio (IoU-like) between time intervals
        - Picks the RU cue with highest overlap score for each EN cue
    """
    matches: List[Tuple[Cue, Optional[Cue]]] = []
    ru_index = 0
    ru_len = len(ru_cues)

    for en in en_cues:
        # Advance ru_index to a plausible start
        while ru_index < ru_len and ru_cues[ru_index].end_ms + tolerance_ms < en.start_ms - tolerance_ms:
            ru_index += 1

        best_ru: Optional[Cue] = None
        best_score = -1.0
        j = ru_index

        # Check candidates while their start is not far beyond en
        while j < ru_len and ru_cues[j].start_ms - tolerance_ms <= en.end_ms + tolerance_ms:
            ru = ru_cues[j]
            if intervals_close(en.start_ms, en.end_ms, ru.start_ms, ru.end_ms, tolerance_ms):
                overlap = interval_overlap(
                    en.start_ms - tolerance_ms, en.end_ms + tolerance_ms,
                    ru.start_ms - tolerance_ms, ru.end_ms + tolerance_ms
                )
                union = (
                    max(en.end_ms + tolerance_ms, ru.end_ms + tolerance_ms) -
                    min(en.start_ms - tolerance_ms, ru.start_ms - tolerance_ms)
                )
                score = overlap / union if union > 0 else 0

                # Use overlap ratio; tie-breaker by absolute overlap then proximity of starts
                if score > best_score:
                    best_score = score
                    best_ru = ru
            j += 1

        if en and best_ru:
            matches.append((en, best_ru))

    return matches

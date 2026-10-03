"""
LectureFlow Cut Planner
Detects spoken verbal cues, retakes, and dead air, then builds a Right-to-Left cut list.
"""

from typing import List, Dict, Any, Optional

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20
}

class CutSegment:
    def __init__(self, name: str, in_source: float, out_source: float, reason: str = "spoken_cue"):
        self.name = name
        self.in_source = in_source
        self.out_source = out_source
        self.duration = out_source - in_source
        self.reason = reason

    def to_dict(self, offset: float = 0.0) -> Dict[str, Any]:
        return {
            "name": self.name,
            "in_source": round(self.in_source, 3),
            "out_source": round(self.out_source, 3),
            "timeline_in": round(self.in_source + offset, 3),
            "timeline_out": round(self.out_source + offset, 3),
            "duration": round(self.duration, 3),
            "reason": self.reason
        }

class CutPlanner:
    def __init__(
        self,
        pre_padding: float = 0.5,
        post_padding: float = 0.5,
        retake_keywords: Optional[List[str]] = None
    ):
        self.pre_padding = pre_padding
        self.post_padding = post_padding
        self.retake_keywords = retake_keywords or ["cut", "retake", "sorry", "again"]

    def parse_transcript(self, words: List[Dict[str, Any]]) -> List[CutSegment]:
        clean_words = [w for w in words if w.get("text", "").strip()]
        cuts: List[CutSegment] = []

        # 1. Identify Spoken Slide Cues
        for i, w in enumerate(clean_words):
            token = w.get("text", "").lower().strip(".,!?\"'")
            if token == "slide" and i + 1 < len(clean_words):
                next_w = clean_words[i + 1]
                next_token = next_w.get("text", "").lower().strip(".,!?\"'")
                
                # Check if followed by a number or word-number
                num_val = None
                if next_token.isdigit():
                    num_val = int(next_token)
                elif next_token in NUMBER_WORDS:
                    num_val = NUMBER_WORDS[next_token]

                if num_val is not None:
                    prev_w = clean_words[i - 1] if i > 0 else None
                    subseq_w = clean_words[i + 2] if i + 2 < len(clean_words) else None

                    prev_end = prev_w.get("end", 0.0) if prev_w else 0.0
                    subseq_start = subseq_w.get("start", next_w.get("end", 0.0)) if subseq_w else next_w.get("end", 0.0)

                    # Calculate natural room tone cuts
                    t_in = min(w.get("start", 0.0), prev_end + self.pre_padding)
                    t_out = max(next_w.get("end", 0.0), subseq_start - self.post_padding)

                    if t_out > t_in:
                        cuts.append(CutSegment(
                            name=f"Slide {num_val}",
                            in_source=t_in,
                            out_source=t_out,
                            reason="spoken_cue"
                        ))

        # 2. Identify Retakes and Verbal Slips
        for i, w in enumerate(clean_words):
            token = w.get("text", "").lower().strip(".,!?\"'")
            if token in self.retake_keywords:
                # Find boundaries of the false start
                # Look backward for pause or sentence boundary
                bad_start = w.get("start", 0.0)
                for j in range(i - 1, max(0, i - 15), -1):
                    gap = clean_words[j + 1].get("start", 0.0) - clean_words[j].get("end", 0.0)
                    if gap > 1.5 or clean_words[j].get("text", "").endswith((".", "!", "?")):
                        bad_start = clean_words[j].get("end", 0.0) + self.pre_padding
                        break

                # Look forward for the restart of speech
                bad_end = w.get("end", 0.0)
                for k in range(i + 1, min(len(clean_words), i + 10)):
                    next_token = clean_words[k].get("text", "").lower().strip(".,!?\"'")
                    if next_token not in self.retake_keywords:
                        bad_end = clean_words[k].get("start", 0.0) - self.post_padding
                        break

                if bad_end > bad_start and (bad_end - bad_start) > 1.0:
                    # Ensure no duplicate overlap
                    if not any(abs(c.in_source - bad_start) < 2.0 for c in cuts):
                        cuts.append(CutSegment(
                            name=f"Retake @ {bad_start:.1f}s",
                            in_source=bad_start,
                            out_source=bad_end,
                            reason="retake"
                        ))

        # Sort cuts in chronological source order
        cuts.sort(key=lambda c: c.in_source)
        return cuts

    def build_right_to_left_plan(self, cuts: List[CutSegment], timeline_offset: float) -> List[Dict[str, Any]]:
        """
        Reverses the cut order to execute Right-to-Left.
        Because each downstream cut removes a slice, earlier upstream timestamps
        remain completely unaffected on the timeline.
        """
        reversed_cuts = list(reversed(cuts))
        return [c.to_dict(offset=timeline_offset) for c in reversed_cuts]

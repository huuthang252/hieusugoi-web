import re
import difflib

_BLANK_RE  = re.compile(r"[（(][\s　]{0,3}[）)]")
_CHOICE_RE = re.compile(r"[①②③④]|(?:^|\s)[1-4][.．\s]", re.MULTILINE)

_CIRCLE_NUM = {"①": 1, "②": 2, "③": 3, "④": 4}
_ANSWER_LINE_RE = re.compile(r"^Đáp án đúng[:：]\s*(.+)$", re.MULTILINE)
_NUM_PREFIX_RE  = re.compile(r"^([1-4])[.．）\s]\s*")


def is_fill_in_question(text: str) -> bool:
    if not text:
        return False
    return bool(_BLANK_RE.search(text)) and bool(_CHOICE_RE.search(text))


def parse_choices(text: str) -> dict:
    """Extract {1: 'xxx', 2: 'xxx', ...} from OCR text.
    Tries ①②③④ format first, then 1. / 1  numeric format.
    """
    choices: dict = {}

    for line in text.splitlines():
        line = line.strip()
        for circle, num in _CIRCLE_NUM.items():
            if line.startswith(circle):
                val = line[len(circle):].strip()
                if val:
                    choices[num] = val

    if len(choices) >= 2:
        return choices

    choices = {}
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^([1-4])[.．）\s]\s*(.+)$", line)
        if m:
            num = int(m.group(1))
            val = m.group(2).strip()
            if val:
                choices[num] = val

    return choices


def build_closed_choice_prompt(question_text: str, choices: dict) -> str:
    """Build a structured closed-choice prompt the AI must stay within."""
    choices_block = "\n".join(f"{n}. {v}" for n, v in sorted(choices.items()))
    return f"""Bạn là gia sư JLPT. Chọn đáp án đúng nhất cho chỗ trống trong câu sau.

Câu hỏi:
{question_text}

Choices (danh sách đáp án):
{choices_block}

Rules:
- You MUST choose exactly one answer from the Choices list above.
- DO NOT create new words or use words not in the list.
- Even if unsure, you must still pick one from the list.
- Output the EXACT text of the chosen answer as it appears in the list.

Output:
Đáp án đúng: <số> <nguyên văn từ choices>

Diễn giải:
<1-3 câu giải thích ngắn gọn>"""


def validate_answer(result: str, choices: dict) -> str:
    """Post-validate AI answer. Returns corrected result or fallback message."""
    if not choices:
        return result

    m = _ANSWER_LINE_RE.search(result)
    if not m:
        return result

    answer_raw   = m.group(1).strip()
    answer_line  = m.group(0).strip()

    # 1. Validate by number prefix (cheapest, most reliable)
    num_m = _NUM_PREFIX_RE.match(answer_raw)
    if num_m:
        num = int(num_m.group(1))
        if num in choices:
            return result  # AI picked a valid number — accept

    # 2. Validate by substring match against any choice text
    for num, text in choices.items():
        if text in answer_raw or answer_raw in text:
            return result  # Substring match — accept

    # 3. Fuzzy match
    choice_texts = list(choices.values())
    matches = difflib.get_close_matches(answer_raw, choice_texts, n=1, cutoff=0.4)
    if matches:
        best_text = matches[0]
        best_num  = next(k for k, v in choices.items() if v == best_text)
        return result.replace(
            answer_line,
            f"Đáp án đúng: {best_num} {best_text} [đã sửa tự động]",
            1,
        )

    # 4. Hard fallback
    choices_str = "  |  ".join(f"{k}. {v}" for k, v in sorted(choices.items()))
    return result.replace(
        answer_line,
        f"Đáp án đúng: Không xác định — Choices: {choices_str}",
        1,
    )

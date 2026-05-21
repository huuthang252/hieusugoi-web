"""
tools/generate_n4_pack.py
Generate N4 JLPT dataset packs (schema v2) as clean UTF-8 JSON files.

Usage:
    python tools/generate_n4_pack.py

Output:
    data/jlpt/N4/grammar/n4_grammar_pack_01.json    (5 items)
    data/jlpt/N4/vocabulary/n4_vocabulary_pack_01.json  (10 items)
    data/jlpt/N4/quiz/n4_quiz_pack_01.json           (5 items)

Schema version: 2 (superset of v1 — all v1 required fields remain required)
"""

from __future__ import annotations

import json
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────

VALID_POS = {"verb", "noun", "adjective", "adverb", "particle", "expression", "other"}
VALID_REGISTER = {"formal", "casual", "neutral", "written"}
VALID_LEVELS = {"N5", "N4", "N3", "N2", "N1"}

REQUIRED_GRAMMAR_FIELDS = {
    "id", "level", "pattern", "meaning_vi", "formation",
    "example_jp", "example_reading", "example_vi",
    "tags", "search_forms", "related_grammar",
}

REQUIRED_VOCAB_FIELDS = {
    "id", "level", "word", "reading", "kanji", "meaning_vi", "part_of_speech",
    "example_jp", "example_reading", "example_vi", "tags", "search_forms",
}

REQUIRED_QUIZ_FIELDS = {
    "id", "level", "type", "question", "choices", "answer",
    "explanation_vi", "grammar_refs", "vocab_refs", "tags",
}

DATA_DIR = Path(__file__).parent.parent / "data" / "jlpt"


# ── I/O helper ────────────────────────────────────────────────────────────────

def write_json(path: str | Path, data: list) -> None:
    """Write data to path as UTF-8 JSON (no BOM, ensure_ascii=False, indent=2)."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[WRITE] {out.relative_to(out.parent.parent.parent.parent)}")


# ── Internal validators ───────────────────────────────────────────────────────

def _validate_grammar(items: list, label: str) -> bool:
    errors: list[str] = []
    ids_seen: set[str] = set()

    for item in items:
        item_id = item.get("id", "<no id>")

        if item_id in ids_seen:
            errors.append(f"  [{item_id}] duplicate id")
        ids_seen.add(item_id)

        missing = REQUIRED_GRAMMAR_FIELDS - item.keys()
        if missing:
            errors.append(f"  [{item_id}] missing required fields: {sorted(missing)}")

        lvl = item.get("level", "")
        if lvl not in VALID_LEVELS:
            errors.append(f"  [{item_id}] invalid level: {lvl!r}")

        sf = item.get("search_forms")
        if not isinstance(sf, list) or len(sf) == 0:
            errors.append(f"  [{item_id}] search_forms must be a non-empty list")

        rg = item.get("related_grammar")
        if not isinstance(rg, list):
            errors.append(f"  [{item_id}] related_grammar must be a list")

        reg = item.get("register")
        if reg is not None and reg not in VALID_REGISTER:
            errors.append(f"  [{item_id}] invalid register: {reg!r} (valid: {VALID_REGISTER})")

        ds = item.get("difficulty_score")
        if ds is not None and not (1.0 <= float(ds) <= 5.0):
            errors.append(f"  [{item_id}] difficulty_score {ds} out of range 1.0-5.0")

    if errors:
        print(f"[VALIDATE] {label}: {len(errors)} error(s):")
        for e in errors:
            print(e)
        return False
    print(f"[VALIDATE] {label}: OK ({len(items)} items)")
    return True


def _validate_vocab(items: list, label: str) -> bool:
    errors: list[str] = []
    ids_seen: set[str] = set()

    for item in items:
        item_id = item.get("id", "<no id>")

        if item_id in ids_seen:
            errors.append(f"  [{item_id}] duplicate id")
        ids_seen.add(item_id)

        missing = REQUIRED_VOCAB_FIELDS - item.keys()
        if missing:
            errors.append(f"  [{item_id}] missing required fields: {sorted(missing)}")

        lvl = item.get("level", "")
        if lvl not in VALID_LEVELS:
            errors.append(f"  [{item_id}] invalid level: {lvl!r}")

        pos = item.get("part_of_speech", "")
        if pos not in VALID_POS:
            errors.append(f"  [{item_id}] invalid part_of_speech: {pos!r}")

        sf = item.get("search_forms")
        if not isinstance(sf, list) or len(sf) == 0:
            errors.append(f"  [{item_id}] search_forms must be a non-empty list")

        vg = item.get("verb_group")
        if vg is not None and vg not in (1, 2, 3):
            errors.append(f"  [{item_id}] verb_group must be 1, 2, or 3, got {vg!r}")

        trans = item.get("transitivity")
        if trans is not None and trans not in ("transitive", "intransitive"):
            errors.append(f"  [{item_id}] transitivity must be 'transitive' or 'intransitive'")

        colls = item.get("collocations")
        if colls is not None and not isinstance(colls, list):
            errors.append(f"  [{item_id}] collocations must be a list")

    if errors:
        print(f"[VALIDATE] {label}: {len(errors)} error(s):")
        for e in errors:
            print(e)
        return False
    print(f"[VALIDATE] {label}: OK ({len(items)} items)")
    return True


def _validate_quiz(items: list, label: str) -> bool:
    errors: list[str] = []
    ids_seen: set[str] = set()
    valid_item_types = {"vocabulary_choice", "fill_in", "context_choice"}

    for item in items:
        item_id = item.get("id", "<no id>")

        if item_id in ids_seen:
            errors.append(f"  [{item_id}] duplicate id")
        ids_seen.add(item_id)

        missing = REQUIRED_QUIZ_FIELDS - item.keys()
        if missing:
            errors.append(f"  [{item_id}] missing required fields: {sorted(missing)}")

        choices = item.get("choices")
        if not isinstance(choices, list) or len(choices) < 2:
            errors.append(f"  [{item_id}] choices must be a list with >=2 items")
        else:
            answer = item.get("answer")
            if not isinstance(answer, int) or not (0 <= answer < len(choices)):
                errors.append(
                    f"  [{item_id}] answer {answer!r} out of range [0, {len(choices)-1}]"
                )

        for ref_field in ("grammar_refs", "vocab_refs"):
            val = item.get(ref_field)
            if val is not None and not isinstance(val, list):
                errors.append(f"  [{item_id}] {ref_field} must be a list")

        it = item.get("item_type")
        if it is not None and it not in valid_item_types:
            errors.append(f"  [{item_id}] invalid item_type: {it!r}")

    if errors:
        print(f"[VALIDATE] {label}: {len(errors)} error(s):")
        for e in errors:
            print(e)
        return False
    print(f"[VALIDATE] {label}: OK ({len(items)} items)")
    return True


# ── N4 Grammar Pack 01 ────────────────────────────────────────────────────────
# 5 items: N4_G_001 ~ N4_G_005
# Architecture stress-test slice covering:
#   te-form compound (てみる), change-of-state (ようになる),
#   ability/formal (ことができる), obligation (なければならない),
#   completion/regret (てしまう)

N4_GRAMMAR_PACK_01: list[dict] = [
    {
        "id": "N4_G_001",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "pattern": "〜てみる",
        "meaning_vi": "thử làm gì (thử nghiệm, xem kết quả ra sao)",
        "formation": "Vて形 + みる",
        "example_jp": "この料理を一度食べてみてください。",
        "example_reading": "このりょうりをいちどたべてみてください。",
        "example_vi": "Hãy thử ăn món này một lần xem sao.",
        "tags": ["te_form", "attempt", "daily"],
        "search_forms": [
            "てみる", "てみます", "てみた", "てみました",
            "てみて", "てみない", "てみれば", "でみる", "でみた",
        ],
        "related_grammar": ["N4_G_002", "N5_G_106"],
        "register": "neutral",
        "difficulty_score": 2.0,
        "notes_vi": "Khác 〜てください (yêu cầu): 〜てみる mang nghĩa tự nguyện thử nghiệm.",
    },
    {
        "id": "N4_G_002",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "pattern": "〜ようになる",
        "meaning_vi": "trở nên có thể / dần dần trở thành (diễn đạt sự biến đổi trạng thái)",
        "formation": "V辞書形 / V否定形 (〜ない) + ようになる",
        "example_jp": "練習を続けて、日本語で話せるようになりました。",
        "example_reading": "れんしゅうをつづけて、にほんごではなせるようになりました。",
        "example_vi": "Nhờ tiếp tục luyện tập, tôi đã có thể nói được tiếng Nhật.",
        "tags": ["change_of_state", "potential", "result"],
        "search_forms": [
            "ようになる", "ようになります", "ようになった",
            "ようになりました", "ようになって", "ようになれ",
        ],
        "related_grammar": ["N4_G_001", "N4_G_003"],
        "register": "neutral",
        "difficulty_score": 2.5,
        "notes_vi": "Khác 〜ようにする (nỗ lực để đạt được): 〜ようになる là kết quả đã xảy ra, không do ý chí.",
        "alt_meaning_vi": "Dạng phủ định: 〜ないようになる = trở nên không còn làm gì nữa.",
    },
    {
        "id": "N4_G_003",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "pattern": "〜ことができる",
        "meaning_vi": "có thể làm gì (diễn đạt khả năng, trang trọng hơn potential form)",
        "formation": "V辞書形 + ことができる",
        "example_jp": "私は自転車を修理することができます。",
        "example_reading": "わたしはじてんしゃをしゅうりすることができます。",
        "example_vi": "Tôi có thể sửa xe đạp.",
        "tags": ["ability", "potential", "formal"],
        "search_forms": [
            "ことができる", "ことができます", "ことができない",
            "ことができません", "ことができた", "ことができました",
            "ことができれば",
        ],
        "related_grammar": ["N4_G_002", "N5_G_102"],
        "register": "formal",
        "difficulty_score": 2.1,
        "notes_vi": "Trang trọng hơn potential form (〜られる/〜える). Thường dùng trong văn viết hoặc lời thoại trang trọng.",
    },
    {
        "id": "N4_G_004",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "pattern": "〜なければならない",
        "meaning_vi": "phải làm gì (bắt buộc, nghĩa vụ)",
        "formation": "V否定形 (ない → なけ) + ればならない / ればなりません",
        "example_jp": "明日は早く起きなければなりません。",
        "example_reading": "あしたははやくおきなければなりません。",
        "example_vi": "Ngày mai tôi phải dậy sớm.",
        "tags": ["obligation", "must", "formal"],
        "search_forms": [
            "なければならない", "なければなりません",
            "なければいけない", "なければいけません",
            "なきゃならない", "なきゃいけない", "なきゃ",
        ],
        "related_grammar": ["N5_G_108", "N4_G_003"],
        "register": "neutral",
        "difficulty_score": 2.8,
        "notes_vi": "なきゃ là dạng rút gọn thường dùng trong hội thoại. なければいけない cũng phổ biến ngang nhau.",
        "alt_meaning_vi": "Phủ định của 〜なければならない: 〜なくてもいい (không cần phải làm).",
    },
    {
        "id": "N4_G_005",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "pattern": "〜てしまう",
        "meaning_vi": "đã làm xong / lỡ làm rồi (hoàn thành, thường có sắc thái tiếc nuối hoặc không chủ ý)",
        "formation": "Vて形 + しまう (dạng thân mật: 〜ちゃう / 〜じゃう)",
        "example_jp": "試験の日を忘れてしまいました。",
        "example_reading": "しけんのひをわすれてしまいました。",
        "example_vi": "Tôi đã lỡ quên mất ngày thi rồi.",
        "tags": ["completion", "regret", "unintentional", "te_form"],
        "search_forms": [
            "てしまう", "てしまいます", "てしまった", "てしまいました",
            "てしまって", "ちゃう", "ちゃった", "ちゃいました",
            "でしまう", "でしまった", "じゃう", "じゃった",
        ],
        "related_grammar": ["N5_G_104", "N4_G_001"],
        "register": "neutral",
        "difficulty_score": 2.3,
        "notes_vi": "Hai nghĩa chính: (1) hoàn thành dứt khoát, (2) vô tình/tiếc nuối. Context quyết định nghĩa.",
    },
]


# ── N4 Vocabulary Pack 01 ─────────────────────────────────────────────────────
# 10 items: N4_V_001 ~ N4_V_010
# Focus: high-frequency N4 verbs, adjectives, adverb

N4_VOCABULARY_PACK_01: list[dict] = [
    {
        "id": "N4_V_001",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "word": "決める",
        "reading": "きめる",
        "kanji": "決める",
        "meaning_vi": "quyết định",
        "part_of_speech": "verb",
        "example_jp": "旅行の日程を決めました。",
        "example_reading": "りょこうのにっていをきめました。",
        "example_vi": "Tôi đã quyết định lịch trình chuyến đi.",
        "tags": ["decision", "transitive", "daily"],
        "search_forms": [
            "決める", "決めます", "決めた", "決めました",
            "決めて", "決めない", "決めれば", "きめる", "きめた",
        ],
        "verb_group": 2,
        "transitivity": "transitive",
        "collocations": ["日程を決める", "計画を決める", "場所を決める", "方向を決める"],
        "difficulty_score": 2.0,
        "domain_tags": ["daily", "planning"],
        "antonym_id": "N4_V_002",
    },
    {
        "id": "N4_V_002",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "word": "変える",
        "reading": "かえる",
        "kanji": "変える",
        "meaning_vi": "thay đổi (cái gì đó), thay thế",
        "part_of_speech": "verb",
        "example_jp": "考えを変えることが大切です。",
        "example_reading": "かんがえをかえることがたいせつです。",
        "example_vi": "Việc thay đổi cách suy nghĩ là điều quan trọng.",
        "tags": ["change", "transitive", "daily"],
        "search_forms": [
            "変える", "変えます", "変えた", "変えました",
            "変えて", "変えない", "かえる", "かえた", "かえて",
        ],
        "verb_group": 2,
        "transitivity": "transitive",
        "collocations": ["考えを変える", "予定を変える", "方針を変える"],
        "difficulty_score": 2.1,
        "domain_tags": ["daily"],
        "notes_vi": "Phân biệt: 変える (타동사, thay đổi cái gì) vs 変わる (자동사, cái gì thay đổi).",
        "antonym_id": "N4_V_001",
    },
    {
        "id": "N4_V_003",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "word": "調べる",
        "reading": "しらべる",
        "kanji": "調べる",
        "meaning_vi": "tra cứu, điều tra, kiểm tra",
        "part_of_speech": "verb",
        "example_jp": "辞書で意味を調べてみました。",
        "example_reading": "じしょでいみをしらべてみました。",
        "example_vi": "Tôi đã thử tra nghĩa trong từ điển.",
        "tags": ["research", "transitive", "daily", "academic"],
        "search_forms": [
            "調べる", "調べます", "調べた", "調べました",
            "調べて", "調べない", "しらべる", "しらべた", "しらべて",
        ],
        "verb_group": 2,
        "transitivity": "transitive",
        "collocations": ["インターネットで調べる", "意味を調べる", "原因を調べる"],
        "difficulty_score": 2.0,
        "domain_tags": ["daily", "academic"],
    },
    {
        "id": "N4_V_004",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "word": "続ける",
        "reading": "つづける",
        "kanji": "続ける",
        "meaning_vi": "tiếp tục (làm gì)",
        "part_of_speech": "verb",
        "example_jp": "毎日練習を続けることが上達の近道です。",
        "example_reading": "まいにちれんしゅうをつづけることがじょうたつのちかみちです。",
        "example_vi": "Tiếp tục luyện tập mỗi ngày là con đường ngắn nhất để tiến bộ.",
        "tags": ["continuation", "transitive", "daily"],
        "search_forms": [
            "続ける", "続けます", "続けた", "続けました",
            "続けて", "続けない", "つづける", "つづけた", "つづけて",
        ],
        "verb_group": 2,
        "transitivity": "transitive",
        "collocations": ["練習を続ける", "勉強を続ける", "仕事を続ける", "努力を続ける"],
        "difficulty_score": 2.0,
        "domain_tags": ["daily", "academic"],
    },
    {
        "id": "N4_V_005",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "word": "伝える",
        "reading": "つたえる",
        "kanji": "伝える",
        "meaning_vi": "truyền đạt, thông báo, cho biết",
        "part_of_speech": "verb",
        "example_jp": "気持ちをうまく伝えることができませんでした。",
        "example_reading": "きもちをうまくつたえることができませんでした。",
        "example_vi": "Tôi đã không thể truyền đạt được cảm xúc một cách đúng đắn.",
        "tags": ["communication", "transitive", "daily"],
        "search_forms": [
            "伝える", "伝えます", "伝えた", "伝えました",
            "伝えて", "伝えない", "つたえる", "つたえた", "つたえて",
        ],
        "verb_group": 2,
        "transitivity": "transitive",
        "collocations": ["気持ちを伝える", "情報を伝える", "メッセージを伝える"],
        "difficulty_score": 2.3,
        "domain_tags": ["daily", "communication"],
    },
    {
        "id": "N4_V_006",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "word": "経験",
        "reading": "けいけん",
        "kanji": "経験",
        "meaning_vi": "kinh nghiệm, trải nghiệm",
        "part_of_speech": "noun",
        "example_jp": "海外生活の経験が仕事に役立っています。",
        "example_reading": "かいがいせいかつのけいけんがしごとにやくだっています。",
        "example_vi": "Kinh nghiệm sống ở nước ngoài đang hữu ích cho công việc.",
        "tags": ["experience", "noun", "daily"],
        "search_forms": [
            "経験", "経験する", "経験した", "経験して",
            "経験があ", "経験を", "けいけん",
        ],
        "collocations": ["経験がある", "経験を積む", "経験者", "貴重な経験"],
        "difficulty_score": 2.2,
        "domain_tags": ["daily", "career"],
        "notes_vi": "Cũng dùng như động từ: 経験する (trải nghiệm, trải qua).",
    },
    {
        "id": "N4_V_007",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "word": "予定",
        "reading": "よてい",
        "kanji": "予定",
        "meaning_vi": "kế hoạch, lịch trình, dự kiến",
        "part_of_speech": "noun",
        "example_jp": "週末の予定はもう決まりましたか？",
        "example_reading": "しゅうまつのよていはもうきまりましたか？",
        "example_vi": "Kế hoạch cuối tuần đã sắp xếp xong chưa?",
        "tags": ["planning", "schedule", "daily"],
        "search_forms": [
            "予定", "予定する", "予定した", "予定がある",
            "予定を", "予定通り", "よてい",
        ],
        "collocations": ["予定がある", "予定を立てる", "予定通り", "予定変更"],
        "difficulty_score": 2.0,
        "domain_tags": ["daily", "planning"],
    },
    {
        "id": "N4_V_008",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "word": "大切",
        "reading": "たいせつ",
        "kanji": "大切",
        "meaning_vi": "quan trọng, quý giá, trân trọng",
        "part_of_speech": "adjective",
        "example_jp": "健康が一番大切だと思います。",
        "example_reading": "けんこうがいちばんたいせつだとおもいます。",
        "example_vi": "Tôi nghĩ sức khoẻ là điều quý giá nhất.",
        "tags": ["importance", "value", "daily"],
        "search_forms": [
            "大切", "大切な", "大切に", "大切だ",
            "大切です", "たいせつ",
        ],
        "collocations": ["大切にする", "大切なもの", "大切な人"],
        "difficulty_score": 2.0,
        "domain_tags": ["daily"],
        "notes_vi": "Sắc thái cảm xúc hơn 大事 (たいじ) — 大切 nhấn mạnh giá trị quý giá, 大事 nhấn mạnh tầm quan trọng.",
    },
    {
        "id": "N4_V_009",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "word": "便利",
        "reading": "べんり",
        "kanji": "便利",
        "meaning_vi": "tiện lợi, hữu ích, thuận tiện",
        "part_of_speech": "adjective",
        "example_jp": "スマートフォンは生活をとても便利にしてくれました。",
        "example_reading": "スマートフォンはせいかつをとてもべんりにしてくれました。",
        "example_vi": "Điện thoại thông minh đã làm cho cuộc sống trở nên rất tiện lợi.",
        "tags": ["convenience", "utility", "daily"],
        "search_forms": [
            "便利", "便利な", "便利に", "便利だ",
            "便利です", "べんり",
        ],
        "collocations": ["便利なアプリ", "交通が便利", "便利になる", "便利グッズ"],
        "difficulty_score": 1.9,
        "domain_tags": ["daily", "technology"],
    },
    {
        "id": "N4_V_010",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "word": "必ず",
        "reading": "かならず",
        "kanji": "必ず",
        "meaning_vi": "nhất định, chắc chắn (100%, không có ngoại lệ)",
        "part_of_speech": "adverb",
        "example_jp": "約束したことは必ず守ります。",
        "example_reading": "やくそくしたことはかならずまもります。",
        "example_vi": "Những điều đã hứa, tôi nhất định sẽ giữ.",
        "tags": ["certainty", "emphasis", "daily"],
        "search_forms": ["必ず", "かならず"],
        "collocations": ["必ず守る", "必ずしも", "必ず来る"],
        "difficulty_score": 2.0,
        "domain_tags": ["daily"],
        "notes_vi": "Khác きっと (kỳ vọng mạnh, ~95%) — 必ず là tuyệt đối 100%, thường dùng khi hứa hẹn.",
    },
]


# ── N4 Quiz Pack 01 ───────────────────────────────────────────────────────────
# 5 items: N4_Q_001 ~ N4_Q_005
# Mix: 3 fill_in (grammar) + 2 vocabulary_choice

N4_QUIZ_PACK_01: list[dict] = [
    {
        "id": "N4_Q_001",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "type": "grammar",
        "item_type": "fill_in",
        "question": "私は日本語で手紙を書く＿＿ができます。",
        "question_vi": "Điền vào chỗ trống để hoàn thành câu:",
        "choices": ["こと", "もの", "ため", "から"],
        "answer": 0,
        "explanation_vi": "〜ことができる: V辞書形 + こと + ができる。「書くことができる」= có thể viết. 「こと」tạo thành danh từ hoá động từ.",
        "mistake_hint": "「もの」「ため」「から」không dùng được trong cấu trúc này. Chỉ「こと」mới tạo thành ことができる.",
        "grammar_refs": ["N4_G_003"],
        "vocab_refs": [],
        "tags": ["ことができる", "ability", "fill_in"],
        "difficulty_score": 2.1,
    },
    {
        "id": "N4_Q_002",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "type": "vocabulary",
        "item_type": "vocabulary_choice",
        "question": "「決める」の意味はどれですか？",
        "question_vi": "Chọn nghĩa đúng của「決める」:",
        "choices": ["quyết định", "thay đổi", "tiếp tục", "điều tra"],
        "answer": 0,
        "explanation_vi": "決める (きめる) = quyết định. 変える = thay đổi, 続ける = tiếp tục, 調べる = điều tra. Đây là động từ nhóm 2 (ichidan).",
        "mistake_hint": "注意: 変える (かえる) cũng phát âm giống「帰る」(trở về) nhưng kanji khác nhau.",
        "grammar_refs": [],
        "vocab_refs": ["N4_V_001"],
        "tags": ["vocabulary", "verb", "decision"],
        "difficulty_score": 1.8,
    },
    {
        "id": "N4_Q_003",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "type": "grammar",
        "item_type": "fill_in",
        "question": "毎日練習して、やっと泳げる＿＿なりました。",
        "question_vi": "Điền vào chỗ trống (cấu trúc biến đổi trạng thái):",
        "choices": ["ように", "ために", "ことに", "まで"],
        "answer": 0,
        "explanation_vi": "〜ようになる: V可能形 + ようになる = trở nên có thể làm gì. 「泳げる」là potential form của「泳ぐ」. 「泳げるようになる」= trở nên có thể bơi được.",
        "mistake_hint": "「ために」biểu đạt mục đích, không phải kết quả biến đổi. 「ことに」không dùng trước なる theo cách này.",
        "grammar_refs": ["N4_G_002"],
        "vocab_refs": [],
        "tags": ["ようになる", "change_of_state", "fill_in"],
        "difficulty_score": 2.5,
    },
    {
        "id": "N4_Q_004",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "type": "grammar",
        "item_type": "fill_in",
        "question": "学生は毎日勉強し＿＿なりません。",
        "question_vi": "Điền vào chỗ trống (cấu trúc bắt buộc):",
        "choices": ["なければ", "なくても", "ないと", "ないで"],
        "answer": 0,
        "explanation_vi": "〜なければなりません: phải làm gì. 動詞ない形 → 語尾「ない」→「なけ」+ ればなりません。「勉強しない」→「勉強しなけ」+「ればなりません」。",
        "mistake_hint": "「なくてもいい」= không cần phải làm (ngược nghĩa). 「ないで」= không làm mà... (không phải bắt buộc).",
        "grammar_refs": ["N4_G_004"],
        "vocab_refs": [],
        "tags": ["なければならない", "obligation", "fill_in"],
        "difficulty_score": 2.8,
    },
    {
        "id": "N4_Q_005",
        "level": "N4",
        "schema_version": 2,
        "created_at": "2026-05-21",
        "type": "vocabulary",
        "item_type": "vocabulary_choice",
        "question": "「大切」と「便利」の意味の組み合わせで正しいのはどれですか？",
        "question_vi": "Chọn cặp nghĩa đúng của「大切」và「便利」:",
        "choices": [
            "quan trọng / tiện lợi",
            "tiện lợi / quan trọng",
            "cần thiết / hữu ích",
            "quý giá / quan trọng",
        ],
        "answer": 0,
        "explanation_vi": "大切 (たいせつ) = quan trọng / quý giá. 便利 (べんり) = tiện lợi. Thứ tự: 大切 trước, 便利 sau — đáp án 0 đúng.",
        "mistake_hint": "Lưu ý: 大切 có nghĩa 'quý giá / trân trọng' chứ không phải 'cần thiết'. 必要 (ひつよう) mới nghĩa là 'cần thiết'.",
        "grammar_refs": [],
        "vocab_refs": ["N4_V_008", "N4_V_009"],
        "tags": ["vocabulary", "adjective", "meaning_pair"],
        "difficulty_score": 2.0,
    },
]


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("N4 Pack Generator: Schema v2")
    print("=" * 60)

    # ── Grammar ───────────────────────────────────────────────────────────────
    print("\n[GRAMMAR]")
    if not _validate_grammar(N4_GRAMMAR_PACK_01, "N4_GRAMMAR_PACK_01"):
        raise SystemExit("Grammar validation failed — not writing files.")
    grammar_path = DATA_DIR / "N4" / "grammar" / "n4_grammar_pack_01.json"
    write_json(grammar_path, N4_GRAMMAR_PACK_01)

    # ── Vocabulary ────────────────────────────────────────────────────────────
    print("\n[VOCABULARY]")
    if not _validate_vocab(N4_VOCABULARY_PACK_01, "N4_VOCABULARY_PACK_01"):
        raise SystemExit("Vocabulary validation failed — not writing files.")
    vocab_path = DATA_DIR / "N4" / "vocabulary" / "n4_vocabulary_pack_01.json"
    write_json(vocab_path, N4_VOCABULARY_PACK_01)

    # ── Quiz ──────────────────────────────────────────────────────────────────
    print("\n[QUIZ]")
    if not _validate_quiz(N4_QUIZ_PACK_01, "N4_QUIZ_PACK_01"):
        raise SystemExit("Quiz validation failed — not writing files.")
    quiz_path = DATA_DIR / "N4" / "quiz" / "n4_quiz_pack_01.json"
    write_json(quiz_path, N4_QUIZ_PACK_01)

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Done.")
    print(f"  Grammar   : {len(N4_GRAMMAR_PACK_01)} items")
    print(f"  Vocabulary: {len(N4_VOCABULARY_PACK_01)} items")
    print(f"  Quiz      : {len(N4_QUIZ_PACK_01)} items")
    print(f"  Total     : {len(N4_GRAMMAR_PACK_01) + len(N4_VOCABULARY_PACK_01) + len(N4_QUIZ_PACK_01)} items")
    print("=" * 60)


if __name__ == "__main__":
    main()

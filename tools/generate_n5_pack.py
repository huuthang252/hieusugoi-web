"""
tools/generate_n5_pack.py
Generate N5 JLPT dataset packs as clean UTF-8 JSON files.

Usage:
    python tools/generate_n5_pack.py

Output:
    data/jlpt/N5/grammar/n5_grammar_pack_02.json
    data/jlpt/N5/vocabulary/n5_vocabulary_pack_02.json
    data/jlpt/N5/quiz/n5_quiz_pack_02.json
"""

from __future__ import annotations

import json
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────

VALID_POS = {"verb", "noun", "adjective", "adverb", "particle", "expression", "other"}
REQUIRED_VOCAB_FIELDS = {
    "id", "level", "word", "reading", "meaning_vi", "part_of_speech",
    "example_jp", "example_reading", "example_vi", "tags", "search_forms",
}
REQUIRED_GRAMMAR_FIELDS = {
    "id", "level", "pattern", "meaning_vi", "formation",
    "example_jp", "example_reading", "example_vi",
    "tags", "search_forms", "related_grammar",
}
REQUIRED_QUIZ_FIELDS = {
    "id", "level", "type", "question", "choices", "answer",
    "explanation_vi", "grammar_refs", "vocab_refs", "tags",
}

DATA_DIR = Path(__file__).parent.parent / "data" / "jlpt"


# ── I/O helpers ───────────────────────────────────────────────────────────────

def write_json(path: str | Path, data: list) -> None:
    """Write data to path as UTF-8 JSON (no BOM, ensure_ascii=False, indent=2)."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Internal validator ────────────────────────────────────────────────────────

def _validate_vocab(items: list, label: str) -> bool:
    """Validate vocabulary items."""
    errors: list[str] = []
    ids_seen: set[str] = set()

    for item in items:
        item_id = item.get("id", "<no id>")

        if item_id in ids_seen:
            errors.append(f"  [{item_id}] duplicate id")
        ids_seen.add(item_id)

        missing = REQUIRED_VOCAB_FIELDS - item.keys()
        if missing:
            errors.append(f"  [{item_id}] missing fields: {sorted(missing)}")

        pos = item.get("part_of_speech", "")
        if pos not in VALID_POS:
            errors.append(f"  [{item_id}] invalid part_of_speech={pos!r}")

        sf = item.get("search_forms")
        if not isinstance(sf, list) or len(sf) == 0:
            errors.append(f"  [{item_id}] search_forms must be a non-empty list")

    if errors:
        print(f"[VALIDATE] {label}: {len(errors)} error(s):")
        for e in errors:
            print(e)
        return False

    print(f"[VALIDATE] {label}: OK ({len(items)} items)")
    return True


def _validate_grammar(items: list, label: str) -> bool:
    """Validate grammar items."""
    errors: list[str] = []
    ids_seen: set[str] = set()

    for item in items:
        item_id = item.get("id", "<no id>")

        if item_id in ids_seen:
            errors.append(f"  [{item_id}] duplicate id")
        ids_seen.add(item_id)

        missing = REQUIRED_GRAMMAR_FIELDS - item.keys()
        if missing:
            errors.append(f"  [{item_id}] missing fields: {sorted(missing)}")

        sf = item.get("search_forms")
        if not isinstance(sf, list) or len(sf) == 0:
            errors.append(f"  [{item_id}] search_forms must be a non-empty list")

        rg = item.get("related_grammar")
        if not isinstance(rg, list):
            errors.append(f"  [{item_id}] related_grammar must be a list")

    if errors:
        print(f"[VALIDATE] {label}: {len(errors)} error(s):")
        for e in errors:
            print(e)
        return False

    print(f"[VALIDATE] {label}: OK ({len(items)} items)")
    return True


def _validate_quiz(items: list, label: str) -> bool:
    """Validate quiz items."""
    errors: list[str] = []
    ids_seen: set[str] = set()

    for item in items:
        item_id = item.get("id", "<no id>")

        if item_id in ids_seen:
            errors.append(f"  [{item_id}] duplicate id")
        ids_seen.add(item_id)

        missing = REQUIRED_QUIZ_FIELDS - item.keys()
        if missing:
            errors.append(f"  [{item_id}] missing fields: {sorted(missing)}")

        choices = item.get("choices")
        if not isinstance(choices, list) or len(choices) != 4:
            errors.append(f"  [{item_id}] choices must be a list of 4 items")

        answer = item.get("answer")
        if not isinstance(answer, int) or answer not in (0, 1, 2, 3):
            errors.append(f"  [{item_id}] answer must be int 0-3, got {answer!r}")

        for ref_field in ("grammar_refs", "vocab_refs"):
            val = item.get(ref_field)
            if not isinstance(val, list):
                errors.append(f"  [{item_id}] {ref_field} must be a list")

    if errors:
        print(f"[VALIDATE] {label}: {len(errors)} error(s):")
        for e in errors:
            print(e)
        return False

    print(f"[VALIDATE] {label}: OK ({len(items)} items)")
    return True


# ── Grammar Pack 02 data ──────────────────────────────────────────────────────

N5_GRAMMAR_PACK_02: list[dict] = [
    {
        "id": "N5_G_201",
        "level": "N5",
        "pattern": "〜でしょう",
        "meaning_vi": "chắc là..., có lẽ... (phỏng đoán lịch sự)",
        "formation": "普通形 + でしょう / Adj-na な → でしょう / N + でしょう",
        "example_jp": "明日は雨が降るでしょう。",
        "example_reading": "あしたはあめがふるでしょう。",
        "example_vi": "Chắc là ngày mai trời sẽ mưa.",
        "tags": ["conjecture", "polite", "basic"],
        "search_forms": ["でしょう", "でしょうか", "だろう"],
        "related_grammar": ["N5_G_202", "N5_G_101"],
    },
    {
        "id": "N5_G_202",
        "level": "N5",
        "pattern": "〜と思います",
        "meaning_vi": "tôi nghĩ rằng... (diễn đạt ý kiến, suy nghĩ)",
        "formation": "普通形 + と思います",
        "example_jp": "日本語は難しいと思います。",
        "example_reading": "にほんごはむずかしいとおもいます。",
        "example_vi": "Tôi nghĩ tiếng Nhật khó.",
        "tags": ["opinion", "basic"],
        "search_forms": ["と思います", "と思いました", "と思っています", "とおもいます"],
        "related_grammar": ["N5_G_201", "N5_G_101"],
    },
    {
        "id": "N5_G_203",
        "level": "N5",
        "pattern": "〜ながら",
        "meaning_vi": "vừa... vừa... (hai hành động cùng lúc)",
        "formation": "Vます bỏ ます + ながら + V",
        "example_jp": "音楽を聞きながら勉強します。",
        "example_reading": "おんがくをききながらべんきょうします。",
        "example_vi": "Tôi vừa nghe nhạc vừa học.",
        "tags": ["simultaneous", "conjunction", "basic"],
        "search_forms": ["ながら", "ながら、", "ながら勉強", "ながら歩く"],
        "related_grammar": ["N5_G_102"],
    },
    {
        "id": "N5_G_204",
        "level": "N5",
        "pattern": "〜前に",
        "meaning_vi": "trước khi làm gì",
        "formation": "Vる形 + 前に / N + の + 前に",
        "example_jp": "寝る前に歯を磨きます。",
        "example_reading": "ねるまえにはをみがきます。",
        "example_vi": "Trước khi ngủ tôi đánh răng.",
        "tags": ["time", "sequence", "basic"],
        "search_forms": ["前に", "まえに", "寝る前に", "食べる前に", "前にも"],
        "related_grammar": ["N5_G_205"],
    },
    {
        "id": "N5_G_205",
        "level": "N5",
        "pattern": "〜後で",
        "meaning_vi": "sau khi làm gì",
        "formation": "Vた形 + 後で / N + の + 後で",
        "example_jp": "宿題をした後で、テレビを見ます。",
        "example_reading": "しゅくだいをしたあとで、てれびをみます。",
        "example_vi": "Sau khi làm bài tập, tôi xem TV.",
        "tags": ["time", "sequence", "basic"],
        "search_forms": ["後で", "あとで", "した後で", "食べた後で", "のあとで"],
        "related_grammar": ["N5_G_204"],
    },
    {
        "id": "N5_G_206",
        "level": "N5",
        "pattern": "〜とき",
        "meaning_vi": "khi..., lúc... (thời điểm xảy ra việc gì)",
        "formation": "普通形 + とき / N + の + とき",
        "example_jp": "暇なとき、映画を見ます。",
        "example_reading": "ひまなとき、えいがをみます。",
        "example_vi": "Khi rảnh tôi xem phim.",
        "tags": ["time", "conditional", "basic"],
        "search_forms": ["とき", "ときに", "のとき", "なとき", "たとき"],
        "related_grammar": ["N5_G_204", "N5_G_205"],
    },
    {
        "id": "N5_G_207",
        "level": "N5",
        "pattern": "〜たり〜たりする",
        "meaning_vi": "khi thì... khi thì... (liệt kê một số hành động điển hình)",
        "formation": "Vた形 + り、Vた形 + り + する",
        "example_jp": "週末は映画を見たり、本を読んだりします。",
        "example_reading": "しゅうまつはえいがをみたり、ほんをよんだりします。",
        "example_vi": "Cuối tuần tôi khi thì xem phim, khi thì đọc sách.",
        "tags": ["listing", "actions", "basic"],
        "search_forms": ["たり", "たりします", "たりする", "だり", "だりします"],
        "related_grammar": ["N5_G_102", "N5_G_104"],
    },
    {
        "id": "N5_G_208",
        "level": "N5",
        "pattern": "〜ほうがいい",
        "meaning_vi": "tốt hơn là nên làm gì (lời khuyên)",
        "formation": "Vた形 + ほうがいい / Vない形 + ほうがいい",
        "example_jp": "早く寝たほうがいいですよ。",
        "example_reading": "はやくねたほうがいいですよ。",
        "example_vi": "Bạn nên ngủ sớm thì tốt hơn.",
        "tags": ["advice", "recommendation", "basic"],
        "search_forms": ["ほうがいい", "ほうがいいです", "たほうがいい", "ないほうがいい"],
        "related_grammar": ["N5_G_209", "N5_G_101"],
    },
    {
        "id": "N5_G_209",
        "level": "N5",
        "pattern": "〜なければならない",
        "meaning_vi": "phải làm gì, bắt buộc phải làm (nghĩa vụ)",
        "formation": "Vない形 + なければならない",
        "example_jp": "明日早く起きなければなりません。",
        "example_reading": "あしたはやくおきなければなりません。",
        "example_vi": "Ngày mai tôi phải dậy sớm.",
        "tags": ["obligation", "must", "basic"],
        "search_forms": [
            "なければならない", "なければなりません",
            "なければいけない", "なければいけません",
            "ないといけない",
        ],
        "related_grammar": ["N5_G_210", "N5_G_108"],
    },
    {
        "id": "N5_G_210",
        "level": "N5",
        "pattern": "〜なくてもいい",
        "meaning_vi": "không cần phải làm gì (không bắt buộc)",
        "formation": "Vない形 + なくてもいい",
        "example_jp": "今日は来なくてもいいです。",
        "example_reading": "きょうはこなくてもいいです。",
        "example_vi": "Hôm nay bạn không cần đến cũng được.",
        "tags": ["not-necessary", "permission", "basic"],
        "search_forms": ["なくてもいい", "なくてもいいです", "なくていい", "なくてもかまいません"],
        "related_grammar": ["N5_G_209", "N5_G_107"],
    },
    {
        "id": "N5_G_211",
        "level": "N5",
        "pattern": "〜ことができる",
        "meaning_vi": "có thể làm gì, có khả năng làm gì",
        "formation": "Vる形 + ことができる",
        "example_jp": "私は日本語で話すことができます。",
        "example_reading": "わたしはにほんごではなすことができます。",
        "example_vi": "Tôi có thể nói chuyện bằng tiếng Nhật.",
        "tags": ["ability", "potential", "basic"],
        "search_forms": ["ことができる", "ことができます", "ことができません", "ことができた"],
        "related_grammar": ["N5_G_212", "N5_G_102"],
    },
    {
        "id": "N5_G_212",
        "level": "N5",
        "pattern": "〜ことがある",
        "meaning_vi": "đôi khi có / từng có kinh nghiệm làm gì",
        "formation": "Vる形 + ことがある（習慣）/ Vた形 + ことがある（経験）",
        "example_jp": "時々、電車に乗り遅れることがあります。",
        "example_reading": "ときどき、でんしゃにのりおくれることがあります。",
        "example_vi": "Đôi khi tôi bị lỡ tàu.",
        "tags": ["experience", "sometimes", "basic"],
        "search_forms": ["ことがある", "ことがあります", "ことがあった", "たことがある"],
        "related_grammar": ["N5_G_211"],
    },
    {
        "id": "N5_G_213",
        "level": "N5",
        "pattern": "〜になる",
        "meaning_vi": "trở thành... (biến đổi trạng thái đối với danh từ/tính từ -na)",
        "formation": "N + になる / Adj-na + になる",
        "example_jp": "将来、医者になりたいです。",
        "example_reading": "しょうらい、いしゃになりたいです。",
        "example_vi": "Tương lai tôi muốn trở thành bác sĩ.",
        "tags": ["change", "state", "basic"],
        "search_forms": ["になる", "になります", "になった", "になりたい", "になりました"],
        "related_grammar": ["N5_G_214", "N5_G_102"],
    },
    {
        "id": "N5_G_214",
        "level": "N5",
        "pattern": "〜くなる",
        "meaning_vi": "trở nên... (biến đổi trạng thái đối với tính từ -i)",
        "formation": "Adj-i bỏ い + くなる",
        "example_jp": "春になって、暖かくなりました。",
        "example_reading": "はるになって、あたたかくなりました。",
        "example_vi": "Mùa xuân đến, trời đã ấm hơn.",
        "tags": ["change", "state", "i-adjective", "basic"],
        "search_forms": ["くなる", "くなります", "くなった", "くなりました"],
        "related_grammar": ["N5_G_213"],
    },
    {
        "id": "N5_G_215",
        "level": "N5",
        "pattern": "〜すぎる",
        "meaning_vi": "quá..., làm quá mức (mang sắc thái tiêu cực)",
        "formation": "Vます bỏ ます + すぎる / Adj-i bỏ い + すぎる / Adj-na bỏ な + すぎる",
        "example_jp": "昨日食べすぎて、お腹が痛いです。",
        "example_reading": "きのうたべすぎて、おなかがいたいです。",
        "example_vi": "Hôm qua ăn quá nhiều nên đau bụng.",
        "tags": ["excess", "basic"],
        "search_forms": ["すぎる", "すぎます", "すぎた", "すぎて", "すぎない"],
        "related_grammar": ["N5_G_216", "N5_G_217"],
    },
    {
        "id": "N5_G_216",
        "level": "N5",
        "pattern": "〜やすい",
        "meaning_vi": "dễ làm..., hay bị... (dễ xảy ra)",
        "formation": "Vます bỏ ます + やすい",
        "example_jp": "この道は滑りやすいので気をつけてください。",
        "example_reading": "このみちはすべりやすいのできをつけてください。",
        "example_vi": "Con đường này dễ trơn trượt, hãy cẩn thận.",
        "tags": ["tendency", "ease", "basic"],
        "search_forms": ["やすい", "やすいです", "やすくて", "やすかった"],
        "related_grammar": ["N5_G_217"],
    },
    {
        "id": "N5_G_217",
        "level": "N5",
        "pattern": "〜にくい",
        "meaning_vi": "khó làm..., khó bị... (khó xảy ra)",
        "formation": "Vます bỏ ます + にくい",
        "example_jp": "この漢字は書きにくいです。",
        "example_reading": "このかんじはかきにくいです。",
        "example_vi": "Chữ kanji này khó viết.",
        "tags": ["tendency", "difficulty", "basic"],
        "search_forms": ["にくい", "にくいです", "にくくて", "にくかった"],
        "related_grammar": ["N5_G_216"],
    },
    {
        "id": "N5_G_218",
        "level": "N5",
        "pattern": "〜方",
        "meaning_vi": "cách làm..., phương pháp làm... (cách thức)",
        "formation": "Vます bỏ ます + 方（かた）",
        "example_jp": "この料理の作り方を教えてください。",
        "example_reading": "このりょうりのつくりかたをおしえてください。",
        "example_vi": "Xin hãy chỉ tôi cách nấu món ăn này.",
        "tags": ["method", "how-to", "basic"],
        "search_forms": ["方", "かた", "使い方", "読み方", "書き方", "食べ方", "作り方"],
        "related_grammar": ["N5_G_106"],
    },
    {
        "id": "N5_G_219",
        "level": "N5",
        "pattern": "〜だけ",
        "meaning_vi": "chỉ..., chỉ mỗi... (giới hạn)",
        "formation": "N + だけ / 数量 + だけ / Vる形 + だけ",
        "example_jp": "今日は水だけ飲みました。",
        "example_reading": "きょうはみずだけのみました。",
        "example_vi": "Hôm nay tôi chỉ uống nước.",
        "tags": ["limit", "only", "basic"],
        "search_forms": ["だけ", "だけで", "だけです", "だけが", "だけを", "だけは"],
        "related_grammar": ["N5_G_220"],
    },
    {
        "id": "N5_G_220",
        "level": "N5",
        "pattern": "〜しか〜ない",
        "meaning_vi": "chỉ có... thôi (nhấn mạnh sự ít ỏi, thiếu thốn — dùng với phủ định)",
        "formation": "N + しか + V（否定形）",
        "example_jp": "財布に100円しかありません。",
        "example_reading": "さいふにひゃくえんしかありません。",
        "example_vi": "Trong ví chỉ có 100 yên thôi.",
        "tags": ["limit", "only", "negative", "basic"],
        "search_forms": ["しか", "しかない", "しかありません", "しかいません", "しかできない"],
        "related_grammar": ["N5_G_219", "N5_G_103"],
    },
]


# ── Pack data ─────────────────────────────────────────────────────────────────

N5_VOCABULARY_PACK_02: list[dict] = [
    {
        "id": "N5_V_201",
        "level": "N5",
        "word": "電車",
        "reading": "でんしゃ",
        "meaning_vi": "tàu điện, xe điện",
        "part_of_speech": "noun",
        "example_jp": "毎朝電車で会社に行きます。",
        "example_reading": "まいあさでんしゃでかいしゃにいきます。",
        "example_vi": "Mỗi sáng tôi đi làm bằng tàu điện.",
        "tags": ["transport", "daily", "basic"],
        "search_forms": ["電車", "でんしゃ", "電車で", "電車に"],
    },
    {
        "id": "N5_V_202",
        "level": "N5",
        "word": "バス",
        "reading": "ばす",
        "meaning_vi": "xe buýt",
        "part_of_speech": "noun",
        "example_jp": "バスで駅まで行きます。",
        "example_reading": "ばすでえきまでいきます。",
        "example_vi": "Tôi đi xe buýt đến ga.",
        "tags": ["transport", "daily", "basic"],
        "search_forms": ["バス", "ばす", "バスで", "バスに乗る"],
    },
    {
        "id": "N5_V_203",
        "level": "N5",
        "word": "駅",
        "reading": "えき",
        "meaning_vi": "nhà ga, ga tàu",
        "part_of_speech": "noun",
        "example_jp": "駅の近くにコンビニがあります。",
        "example_reading": "えきのちかくにこんびにがあります。",
        "example_vi": "Gần ga có cửa hàng tiện lợi.",
        "tags": ["place", "transport", "basic"],
        "search_forms": ["駅", "えき", "駅まで", "駅で"],
    },
    {
        "id": "N5_V_204",
        "level": "N5",
        "word": "病院",
        "reading": "びょういん",
        "meaning_vi": "bệnh viện",
        "part_of_speech": "noun",
        "example_jp": "具合が悪いので病院に行きます。",
        "example_reading": "ぐあいがわるいのでびょういんにいきます。",
        "example_vi": "Vì thấy không khỏe nên tôi đi bệnh viện.",
        "tags": ["place", "health", "basic"],
        "search_forms": ["病院", "びょういん"],
    },
    {
        "id": "N5_V_205",
        "level": "N5",
        "word": "銀行",
        "reading": "ぎんこう",
        "meaning_vi": "ngân hàng",
        "part_of_speech": "noun",
        "example_jp": "銀行でお金をおろしました。",
        "example_reading": "ぎんこうでおかねをおろしました。",
        "example_vi": "Tôi đã rút tiền ở ngân hàng.",
        "tags": ["place", "money", "basic"],
        "search_forms": ["銀行", "ぎんこう"],
    },
    {
        "id": "N5_V_206",
        "level": "N5",
        "word": "郵便局",
        "reading": "ゆうびんきょく",
        "meaning_vi": "bưu điện",
        "part_of_speech": "noun",
        "example_jp": "郵便局で切手を買いました。",
        "example_reading": "ゆうびんきょくできってをかいました。",
        "example_vi": "Tôi đã mua tem ở bưu điện.",
        "tags": ["place", "basic"],
        "search_forms": ["郵便局", "ゆうびんきょく"],
    },
    {
        "id": "N5_V_207",
        "level": "N5",
        "word": "レストラン",
        "reading": "れすとらん",
        "meaning_vi": "nhà hàng",
        "part_of_speech": "noun",
        "example_jp": "昨日イタリアンレストランで食べました。",
        "example_reading": "きのういたりあんれすとらんでたべました。",
        "example_vi": "Hôm qua tôi đã ăn ở nhà hàng Ý.",
        "tags": ["place", "food", "basic"],
        "search_forms": ["レストラン", "れすとらん"],
    },
    {
        "id": "N5_V_208",
        "level": "N5",
        "word": "公園",
        "reading": "こうえん",
        "meaning_vi": "công viên",
        "part_of_speech": "noun",
        "example_jp": "日曜日に公園で散歩しました。",
        "example_reading": "にちようびにこうえんでさんぽしました。",
        "example_vi": "Chủ nhật tôi đi dạo ở công viên.",
        "tags": ["place", "daily", "basic"],
        "search_forms": ["公園", "こうえん"],
    },
    {
        "id": "N5_V_209",
        "level": "N5",
        "word": "天気",
        "reading": "てんき",
        "meaning_vi": "thời tiết",
        "part_of_speech": "noun",
        "example_jp": "今日は天気がいいですね。",
        "example_reading": "きょうはてんきがいいですね。",
        "example_vi": "Hôm nay thời tiết đẹp nhỉ.",
        "tags": ["weather", "daily", "basic"],
        "search_forms": ["天気", "てんき", "天気が", "天気は"],
    },
    {
        "id": "N5_V_210",
        "level": "N5",
        "word": "雨",
        "reading": "あめ",
        "meaning_vi": "mưa",
        "part_of_speech": "noun",
        "example_jp": "明日は雨が降るそうです。",
        "example_reading": "あしたはあめがふるそうです。",
        "example_vi": "Nghe nói ngày mai trời mưa.",
        "tags": ["weather", "basic"],
        "search_forms": ["雨", "あめ", "雨が降る", "雨が降り"],
    },
    {
        "id": "N5_V_211",
        "level": "N5",
        "word": "朝",
        "reading": "あさ",
        "meaning_vi": "buổi sáng",
        "part_of_speech": "noun",
        "example_jp": "朝ごはんを食べてから学校に行きます。",
        "example_reading": "あさごはんをたべてからがっこうにいきます。",
        "example_vi": "Tôi ăn sáng rồi mới đi học.",
        "tags": ["time", "daily", "basic"],
        "search_forms": ["朝", "あさ", "朝ごはん", "今朝"],
    },
    {
        "id": "N5_V_212",
        "level": "N5",
        "word": "夜",
        "reading": "よる",
        "meaning_vi": "buổi tối, ban đêm",
        "part_of_speech": "noun",
        "example_jp": "夜は早く寝ます。",
        "example_reading": "よるははやくねます。",
        "example_vi": "Buổi tối tôi đi ngủ sớm.",
        "tags": ["time", "daily", "basic"],
        "search_forms": ["夜", "よる", "今夜", "夜に"],
    },
    {
        "id": "N5_V_213",
        "level": "N5",
        "word": "起きる",
        "reading": "おきる",
        "meaning_vi": "thức dậy",
        "part_of_speech": "verb",
        "example_jp": "毎朝6時に起きます。",
        "example_reading": "まいあさろくじにおきます。",
        "example_vi": "Mỗi sáng tôi dậy lúc 6 giờ.",
        "tags": ["action", "daily", "basic"],
        "search_forms": ["起きる", "起きて", "起きます", "起きました", "おきます"],
    },
    {
        "id": "N5_V_214",
        "level": "N5",
        "word": "寝る",
        "reading": "ねる",
        "meaning_vi": "ngủ, đi ngủ",
        "part_of_speech": "verb",
        "example_jp": "夜11時に寝ます。",
        "example_reading": "よるじゅういちじにねます。",
        "example_vi": "Tôi ngủ lúc 11 giờ tối.",
        "tags": ["action", "daily", "basic"],
        "search_forms": ["寝る", "寝て", "寝ます", "寝ました", "ねます"],
    },
    {
        "id": "N5_V_215",
        "level": "N5",
        "word": "着る",
        "reading": "きる",
        "meaning_vi": "mặc (áo, quần áo)",
        "part_of_speech": "verb",
        "example_jp": "今日は白いシャツを着ています。",
        "example_reading": "きょうはしろいしゃつをきています。",
        "example_vi": "Hôm nay tôi mặc áo sơ mi trắng.",
        "tags": ["action", "clothing", "basic"],
        "search_forms": ["着る", "着て", "着ます", "着ました", "きます", "きました"],
    },
    {
        "id": "N5_V_216",
        "level": "N5",
        "word": "使う",
        "reading": "つかう",
        "meaning_vi": "sử dụng, dùng",
        "part_of_speech": "verb",
        "example_jp": "このペンを使ってもいいですか。",
        "example_reading": "このぺんをつかってもいいですか。",
        "example_vi": "Tôi có thể dùng cây bút này không?",
        "tags": ["action", "daily", "basic"],
        "search_forms": ["使う", "使い", "使って", "使います", "使いました", "つかいます"],
    },
    {
        "id": "N5_V_217",
        "level": "N5",
        "word": "作る",
        "reading": "つくる",
        "meaning_vi": "làm, tạo ra, nấu",
        "part_of_speech": "verb",
        "example_jp": "母は毎朝お弁当を作ります。",
        "example_reading": "はははまいあさおべんとうをつくります。",
        "example_vi": "Mẹ tôi mỗi sáng đều làm cơm hộp.",
        "tags": ["action", "food", "daily", "basic"],
        "search_forms": ["作る", "作り", "作って", "作ります", "作りました", "つくります"],
    },
    {
        "id": "N5_V_218",
        "level": "N5",
        "word": "待つ",
        "reading": "まつ",
        "meaning_vi": "chờ, đợi",
        "part_of_speech": "verb",
        "example_jp": "駅で友達を待っています。",
        "example_reading": "えきでともだちをまっています。",
        "example_vi": "Tôi đang chờ bạn ở ga.",
        "tags": ["action", "daily", "basic"],
        "search_forms": ["待つ", "待って", "待ちます", "待ちました", "まちます"],
    },
    {
        "id": "N5_V_219",
        "level": "N5",
        "word": "思う",
        "reading": "おもう",
        "meaning_vi": "nghĩ, cho rằng",
        "part_of_speech": "verb",
        "example_jp": "日本語は難しいと思います。",
        "example_reading": "にほんごはむずかしいとおもいます。",
        "example_vi": "Tôi nghĩ tiếng Nhật khó.",
        "tags": ["action", "thought", "basic"],
        "search_forms": ["思う", "思い", "思って", "思います", "思いました", "おもいます"],
    },
    {
        "id": "N5_V_220",
        "level": "N5",
        "word": "知る",
        "reading": "しる",
        "meaning_vi": "biết",
        "part_of_speech": "verb",
        "example_jp": "その駅を知っていますか。",
        "example_reading": "そのえきをしっていますか。",
        "example_vi": "Bạn có biết ga đó không?",
        "tags": ["action", "knowledge", "basic"],
        "search_forms": ["知る", "知って", "知ります", "知っています", "しっています"],
    },
    {
        "id": "N5_V_221",
        "level": "N5",
        "word": "忙しい",
        "reading": "いそがしい",
        "meaning_vi": "bận rộn",
        "part_of_speech": "adjective",
        "example_jp": "今週はとても忙しいです。",
        "example_reading": "こんしゅうはとてもいそがしいです。",
        "example_vi": "Tuần này rất bận.",
        "tags": ["adjective", "feeling", "work", "basic"],
        "search_forms": ["忙しい", "忙しく", "忙しくて", "いそがしい", "いそがしくて"],
    },
    {
        "id": "N5_V_222",
        "level": "N5",
        "word": "楽しい",
        "reading": "たのしい",
        "meaning_vi": "vui, vui vẻ",
        "part_of_speech": "adjective",
        "example_jp": "日本語の勉強は楽しいです。",
        "example_reading": "にほんごのべんきょうはたのしいです。",
        "example_vi": "Việc học tiếng Nhật rất vui.",
        "tags": ["adjective", "feeling", "basic"],
        "search_forms": ["楽しい", "楽しく", "楽しくて", "たのしい", "たのしくて"],
    },
    {
        "id": "N5_V_223",
        "level": "N5",
        "word": "難しい",
        "reading": "むずかしい",
        "meaning_vi": "khó",
        "part_of_speech": "adjective",
        "example_jp": "この問題はとても難しいです。",
        "example_reading": "このもんだいはとてもむずかしいです。",
        "example_vi": "Bài toán này rất khó.",
        "tags": ["adjective", "study", "basic"],
        "search_forms": ["難しい", "難しく", "難しくて", "むずかしい", "むずかしくて"],
    },
    {
        "id": "N5_V_224",
        "level": "N5",
        "word": "易しい",
        "reading": "やさしい",
        "meaning_vi": "dễ; hiền lành, tốt bụng",
        "part_of_speech": "adjective",
        "example_jp": "この本はとても易しいです。",
        "example_reading": "このほんはとてもやさしいです。",
        "example_vi": "Cuốn sách này rất dễ.",
        "tags": ["adjective", "study", "basic"],
        "search_forms": ["易しい", "やさしい", "やさしく", "やさしくて"],
    },
    {
        "id": "N5_V_225",
        "level": "N5",
        "word": "新しい",
        "reading": "あたらしい",
        "meaning_vi": "mới",
        "part_of_speech": "adjective",
        "example_jp": "新しいパソコンを買いました。",
        "example_reading": "あたらしいぱそこんをかいました。",
        "example_vi": "Tôi đã mua máy tính mới.",
        "tags": ["adjective", "basic"],
        "search_forms": ["新しい", "新しく", "新しくて", "あたらしい", "あたらしくて"],
    },
    {
        "id": "N5_V_226",
        "level": "N5",
        "word": "古い",
        "reading": "ふるい",
        "meaning_vi": "cũ, cổ",
        "part_of_speech": "adjective",
        "example_jp": "この建物はとても古いです。",
        "example_reading": "このたてものはとてもふるいです。",
        "example_vi": "Tòa nhà này rất cũ.",
        "tags": ["adjective", "basic"],
        "search_forms": ["古い", "古く", "古くて", "ふるい", "ふるくて"],
    },
    {
        "id": "N5_V_227",
        "level": "N5",
        "word": "長い",
        "reading": "ながい",
        "meaning_vi": "dài",
        "part_of_speech": "adjective",
        "example_jp": "この道はとても長いです。",
        "example_reading": "このみちはとてもながいです。",
        "example_vi": "Con đường này rất dài.",
        "tags": ["adjective", "size", "basic"],
        "search_forms": ["長い", "長く", "長くて", "ながい", "ながくて"],
    },
    {
        "id": "N5_V_228",
        "level": "N5",
        "word": "短い",
        "reading": "みじかい",
        "meaning_vi": "ngắn",
        "part_of_speech": "adjective",
        "example_jp": "夏は夜が短いです。",
        "example_reading": "なつはよるがみじかいです。",
        "example_vi": "Mùa hè ban đêm ngắn.",
        "tags": ["adjective", "size", "basic"],
        "search_forms": ["短い", "短く", "短くて", "みじかい", "みじかくて"],
    },
    {
        "id": "N5_V_229",
        "level": "N5",
        "word": "元気",
        "reading": "げんき",
        "meaning_vi": "khỏe mạnh, năng động",
        "part_of_speech": "adjective",
        "example_jp": "毎日運動して元気です。",
        "example_reading": "まいにちうんどうしてげんきです。",
        "example_vi": "Mỗi ngày tập thể dục nên tôi rất khỏe.",
        "tags": ["adjective", "health", "basic"],
        "search_forms": ["元気", "げんき", "元気です", "元気な", "お元気ですか"],
    },
    {
        "id": "N5_V_230",
        "level": "N5",
        "word": "暇",
        "reading": "ひま",
        "meaning_vi": "rảnh rỗi",
        "part_of_speech": "adjective",
        "example_jp": "今週末は暇ですか。",
        "example_reading": "こんしゅうまつはひまですか。",
        "example_vi": "Cuối tuần này bạn có rảnh không?",
        "tags": ["adjective", "time", "daily", "basic"],
        "search_forms": ["暇", "ひま", "暇です", "暇な", "暇なとき"],
    },
]


# ── Grammar Pack 03 data ──────────────────────────────────────────────────────

N5_GRAMMAR_PACK_03: list[dict] = [
    {
        "id": "N5_G_301",
        "level": "N5",
        "pattern": "〜てから",
        "meaning_vi": "sau khi làm X xong thì làm Y (tuần tự hành động)",
        "formation": "Vて形 + から + V",
        "example_jp": "手を洗ってから、ご飯を食べます。",
        "example_reading": "てをあらってから、ごはんをたべます。",
        "example_vi": "Tôi rửa tay xong rồi mới ăn cơm.",
        "tags": ["sequence", "time", "basic"],
        "search_forms": ["てから", "でから", "洗ってから", "食べてから", "帰ってから"],
        "related_grammar": ["N5_G_204", "N5_G_205"],
    },
    {
        "id": "N5_G_302",
        "level": "N5",
        "pattern": "〜ましょう / 〜ましょうか",
        "meaning_vi": "nào cùng... nhé / mình... được không? (rủ rê, đề nghị)",
        "formation": "Vます bỏ ます + ましょう / ましょうか",
        "example_jp": "一緒に昼ごはんを食べましょうか。",
        "example_reading": "いっしょにひるごはんをたべましょうか。",
        "example_vi": "Chúng ta cùng ăn trưa nhé?",
        "tags": ["suggestion", "invitation", "polite", "basic"],
        "search_forms": ["ましょう", "ましょうか", "行きましょう", "食べましょう", "始めましょう"],
        "related_grammar": ["N5_G_303", "N5_G_102"],
    },
    {
        "id": "N5_G_303",
        "level": "N5",
        "pattern": "〜ませんか",
        "meaning_vi": "bạn có muốn... không? (mời, rủ lịch sự)",
        "formation": "Vます bỏ ます + ませんか",
        "example_jp": "今夜、一緒に映画を見ませんか。",
        "example_reading": "こんや、いっしょにえいがをみませんか。",
        "example_vi": "Tối nay bạn có muốn cùng xem phim không?",
        "tags": ["invitation", "polite", "basic"],
        "search_forms": ["ませんか", "行きませんか", "食べませんか", "来ませんか"],
        "related_grammar": ["N5_G_302", "N5_G_103"],
    },
    {
        "id": "N5_G_304",
        "level": "N5",
        "pattern": "〜より〜のほうが",
        "meaning_vi": "B hơn A về... (so sánh hai thứ)",
        "formation": "A より B のほうが + Adj",
        "example_jp": "バスより電車のほうが速いです。",
        "example_reading": "ばすよりでんしゃのほうがはやいです。",
        "example_vi": "Tàu điện nhanh hơn xe buýt.",
        "tags": ["comparison", "basic"],
        "search_forms": ["より", "のほうが", "よりも", "よりずっと"],
        "related_grammar": ["N5_G_101"],
    },
    {
        "id": "N5_G_305",
        "level": "N5",
        "pattern": "〜という",
        "meaning_vi": "được gọi là..., có tên là..., (trích dẫn tên/nội dung)",
        "formation": "N / 文 + という + N",
        "example_jp": "「さくら」という映画を見ましたか。",
        "example_reading": "「さくら」というえいがをみましたか。",
        "example_vi": "Bạn đã xem bộ phim tên là 'Sakura' chưa?",
        "tags": ["quotation", "naming", "basic"],
        "search_forms": ["という", "といいます", "というのは", "といわれる"],
        "related_grammar": ["N5_G_202"],
    },
    {
        "id": "N5_G_306",
        "level": "N5",
        "pattern": "〜てみる",
        "meaning_vi": "thử làm gì xem sao",
        "formation": "Vて形 + みる",
        "example_jp": "新しいレストランに行ってみましょう。",
        "example_reading": "あたらしいれすとらんにいってみましょう。",
        "example_vi": "Hãy thử đến nhà hàng mới xem.",
        "tags": ["attempt", "try", "basic"],
        "search_forms": ["てみる", "てみます", "てみました", "てみた", "でみます"],
        "related_grammar": ["N5_G_314"],
    },
    {
        "id": "N5_G_307",
        "level": "N5",
        "pattern": "〜てしまう",
        "meaning_vi": "lỡ làm gì, đã làm gì mất rồi (thường mang sắc thái hối tiếc hoặc hoàn thành)",
        "formation": "Vて形 + しまう",
        "example_jp": "宿題を忘れてしまいました。",
        "example_reading": "しゅくだいをわすれてしまいました。",
        "example_vi": "Tôi đã lỡ quên mất bài tập về nhà.",
        "tags": ["completion", "regret", "basic"],
        "search_forms": ["てしまう", "てしまいます", "てしまいました", "てしまって", "ちゃった", "ちゃいました"],
        "related_grammar": ["N5_G_104"],
    },
    {
        "id": "N5_G_308",
        "level": "N5",
        "pattern": "〜かもしれない",
        "meaning_vi": "có thể là..., biết đâu... (không chắc chắn)",
        "formation": "普通形 + かもしれない / かもしれません",
        "example_jp": "明日は雨が降るかもしれません。",
        "example_reading": "あしたはあめがふるかもしれません。",
        "example_vi": "Biết đâu ngày mai trời mưa.",
        "tags": ["uncertainty", "possibility", "basic"],
        "search_forms": ["かもしれない", "かもしれません", "かもしれなかった"],
        "related_grammar": ["N5_G_201", "N5_G_317"],
    },
    {
        "id": "N5_G_309",
        "level": "N5",
        "pattern": "〜そうです（様態）",
        "meaning_vi": "trông có vẻ..., nhìn thấy như thể... (nhận xét qua quan sát)",
        "formation": "Vます bỏ ます + そうです / Adj-i bỏ い + そうです / Adj-na bỏ な + そうです",
        "example_jp": "空が暗いので、雨が降りそうです。",
        "example_reading": "そらがくらいので、あめがふりそうです。",
        "example_vi": "Bầu trời tối nên trông như sắp mưa.",
        "tags": ["appearance", "conjecture", "basic"],
        "search_forms": ["そうです", "そうな", "そうに", "そうで", "降りそう", "おいしそう"],
        "related_grammar": ["N5_G_310", "N5_G_201"],
    },
    {
        "id": "N5_G_310",
        "level": "N5",
        "pattern": "〜らしいです",
        "meaning_vi": "nghe nói là..., có vẻ như... (dựa trên thông tin nghe được)",
        "formation": "普通形 + らしいです / N + らしいです",
        "example_jp": "田中さんは来週、旅行に行くらしいです。",
        "example_reading": "たなかさんはらいしゅう、りょこうにいくらしいです。",
        "example_vi": "Nghe nói anh Tanaka tuần sau đi du lịch.",
        "tags": ["hearsay", "conjecture", "basic"],
        "search_forms": ["らしいです", "らしい", "らしく", "らしかった"],
        "related_grammar": ["N5_G_309", "N5_G_201"],
    },
    {
        "id": "N5_G_311",
        "level": "N5",
        "pattern": "〜ために",
        "meaning_vi": "để (làm gì), vì mục đích...",
        "formation": "Vる形 + ために / N + の + ために",
        "example_jp": "日本語を上手に話すために、毎日練習します。",
        "example_reading": "にほんごをじょうずにはなすために、まいにちれんしゅうします。",
        "example_vi": "Để nói tiếng Nhật giỏi, tôi luyện tập mỗi ngày.",
        "tags": ["purpose", "reason", "basic"],
        "search_forms": ["ために", "ためです", "ための", "のために"],
        "related_grammar": ["N5_G_110"],
    },
    {
        "id": "N5_G_312",
        "level": "N5",
        "pattern": "〜ても",
        "meaning_vi": "dù... cũng..., dù... đến đâu cũng... (nhượng bộ)",
        "formation": "Vて形 + も / Adj-i くても / Adj-na でも / N でも",
        "example_jp": "忙しくても、毎日運動します。",
        "example_reading": "いそがしくても、まいにちうんどうします。",
        "example_vi": "Dù bận đến đâu tôi cũng tập thể dục mỗi ngày.",
        "tags": ["concession", "even-if", "basic"],
        "search_forms": ["ても", "でも", "くても", "くても、", "ても、"],
        "related_grammar": ["N5_G_107", "N5_G_110"],
    },
    {
        "id": "N5_G_313",
        "level": "N5",
        "pattern": "もう〜た / まだ〜ていない",
        "meaning_vi": "đã...rồi / vẫn chưa... (trạng thái hoàn thành hay chưa)",
        "formation": "もう + Vた形 (đã xong) / まだ + Vていない (chưa xong)",
        "example_jp": "もう宿題をしましたか。いいえ、まだしていません。",
        "example_reading": "もうしゅくだいをしましたか。いいえ、まだしていません。",
        "example_vi": "Bạn đã làm bài tập chưa? Chưa, tôi vẫn chưa làm.",
        "tags": ["completion", "time", "basic"],
        "search_forms": ["もう", "まだ", "もうした", "まだしていない", "まだです"],
        "related_grammar": ["N5_G_104"],
    },
    {
        "id": "N5_G_314",
        "level": "N5",
        "pattern": "〜ておく",
        "meaning_vi": "làm trước để chuẩn bị, làm sẵn cho sau",
        "formation": "Vて形 + おく",
        "example_jp": "旅行の前にホテルを予約しておきます。",
        "example_reading": "りょこうのまえにほてるをよやくしておきます。",
        "example_vi": "Trước chuyến đi tôi đặt khách sạn trước.",
        "tags": ["preparation", "advance", "basic"],
        "search_forms": ["ておく", "ておきます", "ておいた", "ておきました", "でおく"],
        "related_grammar": ["N5_G_306", "N5_G_204"],
    },
    {
        "id": "N5_G_315",
        "level": "N5",
        "pattern": "〜てある",
        "meaning_vi": "(ai đó đã làm và) vẫn còn ở trạng thái đó (kết quả còn tồn tại)",
        "formation": "他動詞Vて形 + ある",
        "example_jp": "部屋の窓が開けてあります。",
        "example_reading": "へやのまどがあけてあります。",
        "example_vi": "Cửa sổ phòng được mở (và vẫn đang mở).",
        "tags": ["resultant-state", "preparation", "basic"],
        "search_forms": ["てある", "てあります", "てあった", "でありますます"],
        "related_grammar": ["N5_G_314", "N5_G_109"],
    },
    {
        "id": "N5_G_316",
        "level": "N5",
        "pattern": "〜ばかり",
        "meaning_vi": "vừa mới...; chỉ toàn... (giới hạn hoặc vừa xảy ra)",
        "formation": "Vた形 + ばかり (vừa mới) / N + ばかり (chỉ toàn)",
        "example_jp": "日本に来たばかりなので、まだ何もわかりません。",
        "example_reading": "にほんにきたばかりなので、まだなにもわかりません。",
        "example_vi": "Vì mới đến Nhật nên tôi vẫn chưa biết gì cả.",
        "tags": ["just-did", "only", "basic"],
        "search_forms": ["ばかり", "たばかり", "ばかりです", "ばかりで", "ばかりだ"],
        "related_grammar": ["N5_G_313"],
    },
    {
        "id": "N5_G_317",
        "level": "N5",
        "pattern": "〜はずです",
        "meaning_vi": "chắc là..., đáng lẽ phải... (kỳ vọng có cơ sở, logic)",
        "formation": "普通形 + はずです / N + の + はずです",
        "example_jp": "彼女は3時に来るはずです。",
        "example_reading": "かのじょはさんじにくるはずです。",
        "example_vi": "Cô ấy chắc chắn sẽ đến lúc 3 giờ.",
        "tags": ["expectation", "certainty", "basic"],
        "search_forms": ["はずです", "はずだ", "はずがない", "はずでした"],
        "related_grammar": ["N5_G_308", "N5_G_201"],
    },
    {
        "id": "N5_G_318",
        "level": "N5",
        "pattern": "〜し〜し",
        "meaning_vi": "vừa... vừa..., ngoài ra còn... (liệt kê nhiều lý do hoặc đặc điểm)",
        "formation": "普通形 + し、普通形 + し",
        "example_jp": "このカフェは安いし、静かだし、よく来ます。",
        "example_reading": "このかふぇはやすいし、しずかだし、よくきます。",
        "example_vi": "Quán cà phê này vừa rẻ vừa yên tĩnh nên tôi hay đến.",
        "tags": ["listing", "reason", "basic"],
        "search_forms": ["し、", "だし", "ですし", "いし、"],
        "related_grammar": ["N5_G_207", "N5_G_110"],
    },
    {
        "id": "N5_G_319",
        "level": "N5",
        "pattern": "〜まで",
        "meaning_vi": "cho đến..., đến tận... (giới hạn thời gian hoặc địa điểm)",
        "formation": "N（時間/場所）+ まで",
        "example_jp": "駅まで歩いて10分かかります。",
        "example_reading": "えきまであるいてじゅっぷんかかります。",
        "example_vi": "Đi bộ đến ga mất 10 phút.",
        "tags": ["limit", "time", "place", "basic"],
        "search_forms": ["まで", "までに", "まで歩く", "まで来る", "まで待つ"],
        "related_grammar": ["N5_G_204"],
    },
    {
        "id": "N5_G_320",
        "level": "N5",
        "pattern": "〜と（条件）",
        "meaning_vi": "nếu... thì... (điều kiện tự nhiên, chỉ đường, quy luật)",
        "formation": "普通形 + と + 結果",
        "example_jp": "右に曲がると、駅が見えます。",
        "example_reading": "みぎにまがると、えきがみえます。",
        "example_vi": "Nếu rẽ phải thì bạn sẽ thấy ga.",
        "tags": ["conditional", "natural", "direction", "basic"],
        "search_forms": ["と、", "すると", "になると", "あけると", "おすと"],
        "related_grammar": ["N5_G_110", "N5_G_206"],
    },
]


# ── Quiz Pack 02 data ─────────────────────────────────────────────────────────

N5_QUIZ_PACK_02: list[dict] = [
    # ── Q201-Q210: vocabulary-focused (transport / places) ────────────────────
    {
        "id": "N5_Q_201",
        "level": "N5",
        "type": "fill_in",
        "question": "毎朝___で会社に行きます。",
        "choices": ["電車", "病院", "銀行", "公園"],
        "answer": 0,
        "explanation_vi": "'電車' (でんしゃ) = tàu điện. Đây là phương tiện di chuyển đến công ty mỗi sáng.",
        "grammar_refs": ["N5_G_102"],
        "vocab_refs": ["N5_V_201"],
        "tags": ["vocabulary", "transport", "N5"],
    },
    {
        "id": "N5_Q_202",
        "level": "N5",
        "type": "fill_in",
        "question": "___で駅まで行きます。電車より安いです。",
        "choices": ["バス", "電車", "タクシー", "自転車"],
        "answer": 0,
        "explanation_vi": "'バス' = xe buýt. Rẻ hơn tàu điện, dùng để đến ga.",
        "grammar_refs": ["N5_G_102"],
        "vocab_refs": ["N5_V_202", "N5_V_201"],
        "tags": ["vocabulary", "transport", "N5"],
    },
    {
        "id": "N5_Q_203",
        "level": "N5",
        "type": "choice",
        "question": "電車に乗るために行く場所はどこですか。",
        "choices": ["駅", "病院", "郵便局", "公園"],
        "answer": 0,
        "explanation_vi": "'駅' (えき) = nhà ga, nơi lên tàu điện.",
        "grammar_refs": ["N5_G_109"],
        "vocab_refs": ["N5_V_203", "N5_V_201"],
        "tags": ["vocabulary", "place", "N5"],
    },
    {
        "id": "N5_Q_204",
        "level": "N5",
        "type": "fill_in",
        "question": "具合が悪いので___に行きました。",
        "choices": ["病院", "銀行", "駅", "レストラン"],
        "answer": 0,
        "explanation_vi": "'病院' (びょういん) = bệnh viện. Khi thấy không khỏe thì đến bệnh viện.",
        "grammar_refs": ["N5_G_110"],
        "vocab_refs": ["N5_V_204"],
        "tags": ["vocabulary", "place", "health", "N5"],
    },
    {
        "id": "N5_Q_205",
        "level": "N5",
        "type": "fill_in",
        "question": "お金をおろしに___に行きます。",
        "choices": ["銀行", "病院", "郵便局", "公園"],
        "answer": 0,
        "explanation_vi": "'銀行' (ぎんこう) = ngân hàng. Nơi rút tiền (お金をおろす).",
        "grammar_refs": ["N5_G_102"],
        "vocab_refs": ["N5_V_205"],
        "tags": ["vocabulary", "place", "money", "N5"],
    },
    {
        "id": "N5_Q_206",
        "level": "N5",
        "type": "fill_in",
        "question": "手紙を送るために___に行きました。",
        "choices": ["郵便局", "銀行", "病院", "駅"],
        "answer": 0,
        "explanation_vi": "'郵便局' (ゆうびんきょく) = bưu điện. Nơi gửi thư (手紙を送る).",
        "grammar_refs": ["N5_G_104"],
        "vocab_refs": ["N5_V_206"],
        "tags": ["vocabulary", "place", "N5"],
    },
    {
        "id": "N5_Q_207",
        "level": "N5",
        "type": "choice",
        "question": "友達と夕食を食べに___に行きましょう。",
        "choices": ["レストラン", "銀行", "病院", "郵便局"],
        "answer": 0,
        "explanation_vi": "'レストラン' = nhà hàng. Nơi ăn bữa tối (夕食).",
        "grammar_refs": ["N5_G_102"],
        "vocab_refs": ["N5_V_207", "N5_V_123"],
        "tags": ["vocabulary", "food", "place", "N5"],
    },
    {
        "id": "N5_Q_208",
        "level": "N5",
        "type": "fill_in",
        "question": "日曜日、家族と___を散歩しました。",
        "choices": ["公園", "病院", "銀行", "駅"],
        "answer": 0,
        "explanation_vi": "'公園' (こうえん) = công viên. Nơi đi dạo (散歩する) với gia đình.",
        "grammar_refs": ["N5_G_104"],
        "vocab_refs": ["N5_V_208", "N5_V_124"],
        "tags": ["vocabulary", "place", "N5"],
    },
    # ── Q209-Q214: weather / time ──────────────────────────────────────────────
    {
        "id": "N5_Q_209",
        "level": "N5",
        "type": "fill_in",
        "question": "今日は___がいいですね。出かけましょう。",
        "choices": ["天気", "時間", "仕事", "元気"],
        "answer": 0,
        "explanation_vi": "'天気' (てんき) = thời tiết. 'てんきがいい' = thời tiết đẹp.",
        "grammar_refs": ["N5_G_101"],
        "vocab_refs": ["N5_V_209"],
        "tags": ["vocabulary", "weather", "N5"],
    },
    {
        "id": "N5_Q_210",
        "level": "N5",
        "type": "fill_in",
        "question": "外は___が降っているので、傘を持っていきます。",
        "choices": ["雨", "天気", "朝", "夜"],
        "answer": 0,
        "explanation_vi": "'雨' (あめ) = mưa. '雨が降る' = mưa rơi. Khi trời mưa cần mang ô.",
        "grammar_refs": ["N5_G_109"],
        "vocab_refs": ["N5_V_210"],
        "tags": ["vocabulary", "weather", "N5"],
    },
    {
        "id": "N5_Q_211",
        "level": "N5",
        "type": "fill_in",
        "question": "___ごはんを食べてから、学校に行きます。",
        "choices": ["朝", "夜", "昨日", "明日"],
        "answer": 0,
        "explanation_vi": "'朝' (あさ) = buổi sáng. '朝ごはん' = bữa sáng. Ăn sáng xong mới đi học.",
        "grammar_refs": ["N5_G_104"],
        "vocab_refs": ["N5_V_211"],
        "tags": ["vocabulary", "time", "N5"],
    },
    {
        "id": "N5_Q_212",
        "level": "N5",
        "type": "fill_in",
        "question": "___は早く寝てください。明日も学校がありますから。",
        "choices": ["夜", "朝", "昨日", "天気"],
        "answer": 0,
        "explanation_vi": "'夜' (よる) = buổi tối. 'よるははやく' = tối thì đi sớm.",
        "grammar_refs": ["N5_G_110"],
        "vocab_refs": ["N5_V_212"],
        "tags": ["vocabulary", "time", "N5"],
    },
    # ── Q213-Q220: verbs (daily actions) ──────────────────────────────────────
    {
        "id": "N5_Q_213",
        "level": "N5",
        "type": "fill_in",
        "question": "毎朝7時に___。それからシャワーを浴びます。",
        "choices": ["起きます", "寝ます", "帰ります", "行きます"],
        "answer": 0,
        "explanation_vi": "'起きます' (おきます) = thức dậy. Thức dậy lúc 7 giờ sáng mỗi ngày.",
        "grammar_refs": ["N5_G_102"],
        "vocab_refs": ["N5_V_213"],
        "tags": ["vocabulary", "action", "daily", "N5"],
    },
    {
        "id": "N5_Q_214",
        "level": "N5",
        "type": "fill_in",
        "question": "疲れたので、もう___たいです。",
        "choices": ["寝", "起き", "来", "行き"],
        "answer": 0,
        "explanation_vi": "'寝たい' (ねたい) = muốn ngủ. Vì mệt (疲れた) nên muốn ngủ. Dùng Vます bỏ ます + たい.",
        "grammar_refs": ["N5_G_105"],
        "vocab_refs": ["N5_V_214"],
        "tags": ["vocabulary", "desire", "N5"],
    },
    {
        "id": "N5_Q_215",
        "level": "N5",
        "type": "fill_in",
        "question": "今日は白いシャツを___います。",
        "choices": ["着て", "飲んで", "見て", "書いて"],
        "answer": 0,
        "explanation_vi": "'着ています' (きています) = đang mặc. Vて形 + います = đang trong trạng thái.",
        "grammar_refs": ["N5_G_102"],
        "vocab_refs": ["N5_V_215"],
        "tags": ["vocabulary", "action", "clothing", "N5"],
    },
    {
        "id": "N5_Q_216",
        "level": "N5",
        "type": "fill_in",
        "question": "この辞書を___もいいですか。",
        "choices": ["使って", "飲んで", "食べて", "着て"],
        "answer": 0,
        "explanation_vi": "'使ってもいいですか' (つかってもいいですか) = được dùng không? 'てもいいですか' là cấu trúc xin phép.",
        "grammar_refs": ["N5_G_107"],
        "vocab_refs": ["N5_V_216"],
        "tags": ["vocabulary", "permission", "N5"],
    },
    {
        "id": "N5_Q_217",
        "level": "N5",
        "type": "fill_in",
        "question": "母は毎朝お弁当を___ます。",
        "choices": ["作り", "食べ", "飲み", "見"],
        "answer": 0,
        "explanation_vi": "'作ります' (つくります) = làm, nấu. Mẹ làm cơm hộp mỗi sáng.",
        "grammar_refs": ["N5_G_102"],
        "vocab_refs": ["N5_V_217"],
        "tags": ["vocabulary", "action", "food", "N5"],
    },
    {
        "id": "N5_Q_218",
        "level": "N5",
        "type": "fill_in",
        "question": "駅で友達を___ています。もうすぐ来るでしょう。",
        "choices": ["待っ", "見", "聞い", "話し"],
        "answer": 0,
        "explanation_vi": "'待っています' (まっています) = đang chờ. Vて形 + います diễn đạt hành động đang tiếp diễn.",
        "grammar_refs": ["N5_G_102"],
        "vocab_refs": ["N5_V_218", "N5_V_123"],
        "tags": ["vocabulary", "action", "N5"],
    },
    {
        "id": "N5_Q_219",
        "level": "N5",
        "type": "fill_in",
        "question": "日本語は難しいと___ます。でも楽しいです。",
        "choices": ["思い", "聞き", "見", "書き"],
        "answer": 0,
        "explanation_vi": "'思います' (おもいます) = nghĩ, cho rằng. 'と思います' = tôi nghĩ rằng...",
        "grammar_refs": ["N5_G_102"],
        "vocab_refs": ["N5_V_219"],
        "tags": ["vocabulary", "thought", "N5"],
    },
    {
        "id": "N5_Q_220",
        "level": "N5",
        "type": "fill_in",
        "question": "あの店を___ていますか。美味しいですよ。",
        "choices": ["知っ", "見", "聞い", "話し"],
        "answer": 0,
        "explanation_vi": "'知っていますか' (しっていますか) = bạn có biết không? '知る' ở dạng '知っています' = biết (trạng thái).",
        "grammar_refs": ["N5_G_102"],
        "vocab_refs": ["N5_V_220"],
        "tags": ["vocabulary", "knowledge", "N5"],
    },
    # ── Q221-Q230: adjectives ──────────────────────────────────────────────────
    {
        "id": "N5_Q_221",
        "level": "N5",
        "type": "fill_in",
        "question": "今週は仕事が多くて、とても___です。",
        "choices": ["忙しい", "楽しい", "難しい", "易しい"],
        "answer": 0,
        "explanation_vi": "'忙しい' (いそがしい) = bận rộn. Công việc nhiều nên bận.",
        "grammar_refs": ["N5_G_101"],
        "vocab_refs": ["N5_V_221", "N5_V_125"],
        "tags": ["vocabulary", "adjective", "work", "N5"],
    },
    {
        "id": "N5_Q_222",
        "level": "N5",
        "type": "choice",
        "question": "日本語の勉強はどうですか。",
        "choices": ["楽しいです", "忙しいです", "難しいです", "古いです"],
        "answer": 0,
        "explanation_vi": "'楽しい' (たのしい) = vui. Khi học tiếng Nhật thấy vui thì trả lời '楽しいです'.",
        "grammar_refs": ["N5_G_101"],
        "vocab_refs": ["N5_V_222"],
        "tags": ["vocabulary", "adjective", "feeling", "N5"],
    },
    {
        "id": "N5_Q_223",
        "level": "N5",
        "type": "fill_in",
        "question": "この問題はとても___から、もう一度考えてください。",
        "choices": ["難しい", "易しい", "楽しい", "忙しい"],
        "answer": 0,
        "explanation_vi": "'難しい' (むずかしい) = khó. Vì bài toán khó nên hãy suy nghĩ thêm.",
        "grammar_refs": ["N5_G_110"],
        "vocab_refs": ["N5_V_223"],
        "tags": ["vocabulary", "adjective", "study", "N5"],
    },
    {
        "id": "N5_Q_224",
        "level": "N5",
        "type": "fill_in",
        "question": "この本はとても___です。子どもでも読めます。",
        "choices": ["易しい", "難しい", "忙しい", "楽しい"],
        "answer": 0,
        "explanation_vi": "'易しい' (やさしい) = dễ. Sách dễ đến mức trẻ em cũng đọc được.",
        "grammar_refs": ["N5_G_101"],
        "vocab_refs": ["N5_V_224"],
        "tags": ["vocabulary", "adjective", "study", "N5"],
    },
    {
        "id": "N5_Q_225",
        "level": "N5",
        "type": "fill_in",
        "question": "___パソコンを買いたいです。今のは古くて遅いです。",
        "choices": ["新しい", "古い", "長い", "短い"],
        "answer": 0,
        "explanation_vi": "'新しい' (あたらしい) = mới. Muốn mua máy tính mới vì cái hiện tại cũ và chậm.",
        "grammar_refs": ["N5_G_105"],
        "vocab_refs": ["N5_V_225", "N5_V_226"],
        "tags": ["vocabulary", "adjective", "N5"],
    },
    {
        "id": "N5_Q_226",
        "level": "N5",
        "type": "choice",
        "question": "この建物は何年も前に建てられました。どんな建物ですか。",
        "choices": ["古い建物", "新しい建物", "大きい建物", "小さい建物"],
        "answer": 0,
        "explanation_vi": "'古い' (ふるい) = cũ. Tòa nhà được xây từ nhiều năm trước nên là tòa nhà cũ.",
        "grammar_refs": ["N5_G_101"],
        "vocab_refs": ["N5_V_226"],
        "tags": ["vocabulary", "adjective", "N5"],
    },
    {
        "id": "N5_Q_227",
        "level": "N5",
        "type": "fill_in",
        "question": "この道はとても___です。端から端まで10キロあります。",
        "choices": ["長い", "短い", "高い", "新しい"],
        "answer": 0,
        "explanation_vi": "'長い' (ながい) = dài. Con đường dài 10 km từ đầu đến cuối.",
        "grammar_refs": ["N5_G_101"],
        "vocab_refs": ["N5_V_227"],
        "tags": ["vocabulary", "adjective", "size", "N5"],
    },
    {
        "id": "N5_Q_228",
        "level": "N5",
        "type": "fill_in",
        "question": "夏は夜が___です。早く暗くなりません。",
        "choices": ["短い", "長い", "楽しい", "忙しい"],
        "answer": 0,
        "explanation_vi": "'短い' (みじかい) = ngắn. Mùa hè ban đêm ngắn, trời không tối sớm.",
        "grammar_refs": ["N5_G_101"],
        "vocab_refs": ["N5_V_228"],
        "tags": ["vocabulary", "adjective", "weather", "N5"],
    },
    {
        "id": "N5_Q_229",
        "level": "N5",
        "type": "fill_in",
        "question": "毎日運動しているので、とても___です。",
        "choices": ["元気", "忙しい", "難しい", "古い"],
        "answer": 0,
        "explanation_vi": "'元気' (げんき) = khỏe mạnh. Vì tập thể dục mỗi ngày nên rất khỏe.",
        "grammar_refs": ["N5_G_110"],
        "vocab_refs": ["N5_V_229"],
        "tags": ["vocabulary", "adjective", "health", "N5"],
    },
    {
        "id": "N5_Q_230",
        "level": "N5",
        "type": "fill_in",
        "question": "今週末は___ですか。一緒に映画を見ませんか。",
        "choices": ["暇", "忙しい", "元気", "楽しい"],
        "answer": 0,
        "explanation_vi": "'暇' (ひま) = rảnh rỗi. Hỏi xem cuối tuần có rảnh không để rủ xem phim cùng.",
        "grammar_refs": ["N5_G_101"],
        "vocab_refs": ["N5_V_230", "N5_V_107"],
        "tags": ["vocabulary", "adjective", "social", "N5"],
    },
]


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    all_ok = True

    # Grammar pack 02
    grammar_path = DATA_DIR / "N5" / "grammar" / "n5_grammar_pack_02.json"
    write_json(grammar_path, N5_GRAMMAR_PACK_02)
    print(f"Generated {len(N5_GRAMMAR_PACK_02)} grammar items -> {grammar_path}")
    all_ok &= _validate_grammar(N5_GRAMMAR_PACK_02, "n5_grammar_pack_02")

    # Grammar pack 03
    grammar_path_03 = DATA_DIR / "N5" / "grammar" / "n5_grammar_pack_03.json"
    write_json(grammar_path_03, N5_GRAMMAR_PACK_03)
    print(f"Generated {len(N5_GRAMMAR_PACK_03)} grammar items -> {grammar_path_03}")
    all_ok &= _validate_grammar(N5_GRAMMAR_PACK_03, "n5_grammar_pack_03")

    # Vocabulary pack 02
    vocab_path = DATA_DIR / "N5" / "vocabulary" / "n5_vocabulary_pack_02.json"
    write_json(vocab_path, N5_VOCABULARY_PACK_02)
    print(f"Generated {len(N5_VOCABULARY_PACK_02)} vocabulary items -> {vocab_path}")
    all_ok &= _validate_vocab(N5_VOCABULARY_PACK_02, "n5_vocabulary_pack_02")

    # Quiz pack 02
    quiz_path = DATA_DIR / "N5" / "quiz" / "n5_quiz_pack_02.json"
    write_json(quiz_path, N5_QUIZ_PACK_02)
    print(f"Generated {len(N5_QUIZ_PACK_02)} quiz items -> {quiz_path}")
    all_ok &= _validate_quiz(N5_QUIZ_PACK_02, "n5_quiz_pack_02")

    if all_ok:
        print("Validation OK")
    else:
        raise SystemExit("Validation failed -- fix errors above before using these packs.")


if __name__ == "__main__":
    main()

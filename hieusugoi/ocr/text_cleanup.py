import re
import unicodedata


def is_katakana_char(ch):
    """True n蘯ｿu kﾃｽ t盻ｱ thu盻冂 Katakana full-width ho蘯ｷc half-width."""
    return (
        "\u30A0" <= ch <= "\u30FF" or
        "\uFF66" <= ch <= "\uFF9F"
    )


def fix_katakana_long_vowel(text):
    """
    S盻ｭa cﾃ｡c kﾃｽ t盻ｱ OCR hay nh蘯ｭn nh蘯ｧm thﾃnh d蘯･u trﾆｰ盻拵g ﾃ｢m Katakana "繝ｼ".
    Vﾃｭ d盻･: 繝ｬ繝ｳ繧ｿ繧ｫ荳 / 繝ｬ繝ｳ繧ｿ繧ｫ- / 繝ｬ繝ｳ繧ｿ繧ｫ・ｰ -> 繝ｬ繝ｳ繧ｿ繧ｫ繝ｼ
    """
    text = unicodedata.normalize("NFKC", text.strip())

    replacements = {
        "荳": "繝ｼ",
        "窶・": "繝ｼ",
        "竏・": "繝ｼ",
        "-": "繝ｼ",
        "・ｰ": "繝ｼ",
        "窶・": "繝ｼ",
        "笏・": "繝ｼ",
        "笏": "繝ｼ",
        "・｣": "繝ｼ",
        "・・": "繝ｼ",
    }

    result = ""
    for i, ch in enumerate(text):
        if ch in replacements:
            prev_ch = result[-1] if result else ""
            next_ch = text[i + 1] if i + 1 < len(text) else ""
            if is_katakana_char(prev_ch) or is_katakana_char(next_ch):
                result += "繝ｼ"
            else:
                result += ch
        else:
            result += ch

    return result


def is_hiragana_char(ch):
    return "\u3040" <= ch <= "\u309F"


def is_japanese_kana_char(ch):
    return (
        "\u3040" <= ch <= "\u309F" or   # Hiragana
        "\u30A0" <= ch <= "\u30FF" or   # Katakana
        "\uFF66" <= ch <= "\uFF9F"      # Half-width Katakana
    )


def is_kanji_char(ch):
    return "\u4E00" <= ch <= "\u9FFF"


def contains_kanji(text):
    return any(is_kanji_char(ch) for ch in text)


def contains_japanese(text):
    return any(
        is_japanese_kana_char(ch) or is_kanji_char(ch)
        for ch in text
    )


def normalize_selected_ocr_text(text):
    """
    Ch盻・chu蘯ｩn hﾃｳa r蘯･t nh蘯ｹ sau khi ngﾆｰ盻拱 dﾃｹng ch盻肱 vﾃｹng OCR.
    Khﾃｴng xﾃｳa kana/tr盻｣ t盻ｫ b蘯ｱng rule c盻ｩng n盻ｯa, vﾃｬ d盻・lﾃm m蘯･t cﾃ｢u ti蘯ｿng Nh蘯ｭt.
    Vi盻㌘ lo蘯｡i rﾃ｡c/ghﾃｩp cﾃ｢u s蘯ｽ chuy盻ハ sang AI clean layer.
    """
    text = unicodedata.normalize("NFKC", text.strip())
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_japanese_ocr_text(text):
    """
    Lﾃm s蘯｡ch OCR ti蘯ｿng Nh蘯ｭt:
    - Ch盻・lo蘯｡i kana/c盻･m kana rﾃ｡c ﾄ黛ｻｩng TRﾆｯ盻咾 Kanji
    - Khﾃｴng lo蘯｡i kana ﾄ黛ｻｩng SAU Kanji vﾃｬ cﾃｳ th盻・lﾃ okurigana th蘯ｭt
      Vﾃｭ d盻･: 隱ｿ縺ｹ繧・ 蜍輔°縺・ 隕九ｋ
    - Gi盻ｯ 縺ｫ / 縺・/ 縺・    """
    text = unicodedata.normalize("NFKC", text.strip())

    if not text:
        return text

    if not contains_kanji(text):
        return text

    keep_prefix = {"縺ｫ", "縺・", "縺・"}

    if len(text) > 8:
        return text

    # Kana/c盻･m kana + Kanji
    # 繝ｳ繧ｹ螳御ｺ・竊・螳御ｺ・    # 縺ｮ蜀崎ｵｷ蜍・竊・蜀崎ｵｷ蜍・    # 縺泌鵠蜉・竊・gi盻ｯ nguyﾃｪn
    # 縺願ｦ狗ｩ阪ｊ 竊・gi盻ｯ nguyﾃｪn
    m = re.match(r"^([縺・繧薙ぃ-繝ｳ・ｦ-・溘・]+)([\u4E00-\u9FFF].*)$", text)
    if m:
        prefix = m.group(1)
        body = m.group(2)

        if prefix not in keep_prefix:
            text = body

    return text.strip()


def clean_japanese_selected_text(text):
    """
    Lﾃm s蘯｡ch text sau khi ch盻肱 vﾃｹng OCR.
    - B盻・kana rﾃ｡c ﾄ黛ｻｩng trﾆｰ盻嫩 t盻ｫ cﾃｳ Kanji
    - Nhﾆｰng khﾃｴng b盻・n蘯ｿu phﾃｭa trﾆｰ盻嫩 ﾄ妥｣ cﾃｳ Kanji
      ﾄ黛ｻ・trﾃ｡nh phﾃ｡ cﾃ｢u nhﾆｰ: 菴・縺・繧・隱ｿ縺ｹ繧・    - Gi盻ｯ 縺ｫ / 縺・/ 縺・    """
    text = unicodedata.normalize("NFKC", text.strip())

    if not text:
        return text

    keep_prefix = {"縺ｫ", "縺・", "縺・"}

    parts = text.split()
    cleaned = []

    for i, part in enumerate(parts):
        prev_part = parts[i - 1] if i > 0 else ""
        next_part = parts[i + 1] if i + 1 < len(parts) else ""

        if (
            part not in keep_prefix
            and all(is_japanese_kana_char(ch) for ch in part)
            and contains_kanji(next_part)
            and not contains_kanji(prev_part)
        ):
            continue

        cleaned.append(part)

    return " ".join(cleaned).strip()

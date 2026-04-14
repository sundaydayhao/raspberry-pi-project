import re
from typing import Dict, Iterable, List, Tuple

PROVINCE_MAP: Dict[str, str] = {
    "北京市": "京",
    "天津市": "津",
    "上海市": "沪",
    "重庆市": "渝",
    "河北省": "冀",
    "山西省": "晋",
    "辽宁省": "辽",
    "吉林省": "吉",
    "黑龙江省": "黑",
    "江苏省": "苏",
    "浙江省": "浙",
    "安徽省": "皖",
    "福建省": "闽",
    "江西省": "赣",
    "山东省": "鲁",
    "河南省": "豫",
    "湖北省": "鄂",
    "湖南省": "湘",
    "广东省": "粤",
    "海南省": "琼",
    "四川省": "川",
    "贵州省": "贵",
    "云南省": "云",
    "陕西省": "陕",
    "甘肃省": "甘",
    "青海省": "青",
    "台湾省": "台",
    "内蒙古自治区": "蒙",
    "广西壮族自治区": "桂",
    "西藏自治区": "藏",
    "宁夏回族自治区": "宁",
    "新疆维吾尔自治区": "新",
}

SPECIAL_PLATE_PREFIXES: Dict[str, str] = {
    "香港": "港",
    "澳门": "澳",
    "使馆": "使",
    "领馆": "领",
    "警用": "警",
    "警": "警",
    "学": "学",
}

PROVINCE_CHARS = "".join(PROVINCE_MAP.values()) + "".join(SPECIAL_PLATE_PREFIXES.values())
PROVINCE_SET = set(PROVINCE_CHARS)
PROVINCE_TOKEN_MAP: Dict[str, str] = {}
PROVINCE_TOKEN_MAP.update(PROVINCE_MAP)
PROVINCE_TOKEN_MAP.update(SPECIAL_PLATE_PREFIXES)
PROVINCE_TOKENS: List[Tuple[str, str]] = sorted(
    PROVINCE_TOKEN_MAP.items(), key=lambda item: len(item[0]), reverse=True
)

PLATE_PATTERN = re.compile(rf"^[{re.escape(PROVINCE_CHARS)}][A-Z][A-Z0-9]{{5,6}}$")
FALLBACK_PATTERN = re.compile(r"^[A-Z0-9]{6,8}$")

LETTER_SUBSTITUTIONS = {
    "0": "O",
    "1": "I",
    "2": "Z",
    "5": "S",
    "6": "G",
    "8": "B",
}

ALNUM_SUBSTITUTIONS = {
    "O": "0",
    "Q": "0",
    "D": "0",
    "I": "1",
    "L": "1",
    "Z": "2",
    "S": "5",
    "B": "8",
    "G": "6",
}

SYMBOL_SUBSTITUTIONS = {
    "|": "1",
    "!": "1",
    "[": "1",
    "]": "1",
    "/": "7",
    "\\": "1",
    "-": "",
    "_": "",
    " ": "",
    ".": "",
    ":": "",
}


def supported_provinces() -> List[str]:
    return list(PROVINCE_MAP.values())


def normalize_province_char(char: str) -> str:
    return PROVINCE_TOKEN_MAP.get(char, char)


def _normalize_symbols(text: str) -> str:
    normalized = text
    for token, replacement in SYMBOL_SUBSTITUTIONS.items():
        normalized = normalized.replace(token, replacement)
    return normalized


def _replace_province_tokens(text: str) -> str:
    normalized = _normalize_symbols(text.strip())
    for token, replacement in PROVINCE_TOKENS:
        normalized = normalized.replace(token, replacement)
    return normalized


def _iter_clean_chars(text: str) -> Iterable[str]:
    replaced = _replace_province_tokens(text)
    for char in replaced.upper():
        if char in PROVINCE_SET or (char.isascii() and char.isalnum()):
            yield char


def normalize_plate_text(text: str) -> str:
    return "".join(_iter_clean_chars(text))


def _to_letter(char: str) -> str:
    if char.isalpha():
        return char
    return LETTER_SUBSTITUTIONS.get(char, char)


def _to_alnum(char: str) -> str:
    if char.isascii() and char.isalnum():
        return ALNUM_SUBSTITUTIONS.get(char, char)
    return char


def extract_plate_suffix(text: str) -> str:
    cleaned = normalize_plate_text(text)
    if not cleaned:
        return ""

    ascii_only = "".join(
        _to_alnum(char)
        for char in cleaned
        if char.isascii() and char.isalnum()
    )
    if not ascii_only:
        return ""

    candidates: List[str] = []
    for start in range(len(ascii_only)):
        if not ascii_only[start].isalpha():
            continue
        for length in (7, 6):
            end = start + length
            if end > len(ascii_only):
                continue
            chunk = ascii_only[start:end]
            if chunk[0].isalpha() and all(ch.isalnum() for ch in chunk[1:]):
                candidates.append(chunk)

    if not candidates:
        return ""

    def candidate_score(chunk: str) -> Tuple[int, int, int]:
        digits = sum(ch.isdigit() for ch in chunk[1:])
        extra_letters = sum(ch.isalpha() for ch in chunk[1:])
        regular_plate_bonus = 1 if len(chunk) == 6 else 0
        return (regular_plate_bonus, digits, -extra_letters)

    return max(candidates, key=candidate_score)


def repair_plate_text(text: str) -> str:
    cleaned = normalize_plate_text(text)
    if not cleaned:
        return ""

    first_char = normalize_province_char(cleaned[0])
    if first_char in PROVINCE_SET:
        if len(cleaned) == 1:
            return first_char

        suffix = extract_plate_suffix(text)
        if suffix and suffix[0].isalpha():
            max_tail = 6 if len(suffix) >= 7 else 5
            return first_char + suffix[0] + suffix[1 : 1 + max_tail]

        if not _to_letter(cleaned[1]).isalpha():
            return first_char

        prefix = first_char
        region = _to_letter(cleaned[1])
        tail = "".join(_to_alnum(char) for char in cleaned[2:])
        max_tail = 6 if len(tail) >= 6 else 5
        return prefix + region + tail[:max_tail]

    fallback = extract_plate_suffix(cleaned)
    return fallback[:8]


def looks_like_plate(text: str) -> bool:
    repaired = repair_plate_text(text)
    return bool(PLATE_PATTERN.match(repaired) or FALLBACK_PATTERN.match(repaired))


def score_plate_text(text: str, confidence: float = 0.0) -> float:
    repaired = repair_plate_text(text)
    if not repaired:
        return 0.0

    confidence = max(0.0, min(confidence, 100.0))
    pattern_bonus = 0.75 if PLATE_PATTERN.match(repaired) else 0.45
    length_bonus = 0.1 if len(repaired) in (7, 8) else 0.0
    province_bonus = 0.05 if repaired[0] in PROVINCE_SET else 0.0
    confidence_bonus = confidence / 100.0 * 0.1
    return min(1.0, pattern_bonus + length_bonus + province_bonus + confidence_bonus)

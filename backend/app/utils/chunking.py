# backend/app/utils/chunking.py
import re

# 结构切分的标题正则：按文档类型选不同的"语义边界"
HEADING_PATTERNS = {
    "manual": re.compile(r"^(#{1,3}\s|第[一二三四五六七八九十\d]+[章节]|\d+(\.\d+)*\s)"),
    "case":   re.compile(r"^(案例\s*[0-9一二三四五六七八九十]+|【案例)"),
    "sop":    re.compile(r"^(步骤\s*[0-9一二三四五六七八九十]+|Step\s*\d+)", re.IGNORECASE),
}
TARGET_MIN, TARGET_MAX, OVERLAP = 300, 500, 50


def split_document(text: str, doc_type: str) -> list[str]:
    """两级切分：先按结构边界切段，再把每段归并/拆长到 300~500 字、重叠 50 字。"""
    pattern = HEADING_PATTERNS.get(doc_type)
    sections = _split_by_structure(text, pattern)
    chunks = []
    for section in sections:
        if len(section) <= TARGET_MAX:
            chunks.append(section)
        else:
            chunks.extend(_split_by_length(section))
    return _merge_short(chunks)


def _split_by_structure(text: str, pattern) -> list[str]:
    """按标题行切分；没有匹配到标题（如 API 文档）则整段返回，交给长度切分兜底。"""
    sections, current = [], []
    for line in text.splitlines():
        if pattern and pattern.match(line.strip()) and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("\n".join(current).strip())
    return [s for s in sections if s]


def _split_by_length(section: str) -> list[str]:
    """超长段按 500 字滑窗切，相邻 chunk 重叠 50 字保持上下文连续。"""
    chunks, start = [], 0
    while start < len(section):
        chunks.append(section[start:start + TARGET_MAX])
        start += TARGET_MAX - OVERLAP
    return chunks


def _merge_short(chunks: list[str]) -> list[str]:
    """过短的 chunk 并入前一个，避免检索到没信息量的碎片。

    当被合并的短 chunk 来自 _split_by_length 的滑窗重叠时，
    检测尾部重叠并跳过，避免同一段内容在合并后的 chunk 里出现两次。
    """
    merged = []
    for chunk in chunks:
        if merged and len(chunk) < TARGET_MIN:
            prev = merged[-1]
            if len(prev) >= OVERLAP and chunk[:OVERLAP] == prev[-OVERLAP:]:
                merged[-1] = prev + "\n" + chunk[OVERLAP:]
            else:
                merged[-1] = prev + "\n" + chunk
        else:
            merged.append(chunk)
    return merged

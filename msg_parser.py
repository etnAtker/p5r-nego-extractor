"""Parsers for Persona 5 Royal TALK *.msg and *.msg.h files."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from models import MsgIndex, TextEntry

LOGGER = logging.getLogger(__name__)

MESSAGE_BLOCK_RE = re.compile(r"^\[(msg|sel)\s+([^\]\s]+)([^\]]*)\]")
TAG_RE = re.compile(r"\[([^\]]+)\]")
QUESTION_RE = re.compile(r"CHAT_(FQ|SQ)_(\d+)", re.IGNORECASE)


def parse_msg_resources(
    talk_script: str, msg_path: Path, header_path: Path
) -> MsgIndex:
    """Parse .msg text and .msg.h id mapping files."""

    key_to_id = _parse_header(header_path)
    id_to_key = {value: key for key, value in key_to_id.items()}
    index = MsgIndex(talk_script=talk_script, key_to_id=key_to_id, id_to_key=id_to_key)

    for entry in _parse_msg_file(talk_script, msg_path, index):
        index.add_entry(entry)

    return index


def _parse_header(header_path: Path) -> Dict[str, int]:
    mapping: Dict[str, int] = {}
    header_text = header_path.read_text(encoding="utf-8", errors="ignore")
    for line in header_text.splitlines():
        line = line.strip()
        if not line.startswith("const int"):
            continue

        parts = line.replace("const int", "", 1).strip().split("=")
        if len(parts) != 2:
            continue

        name = parts[0].strip()
        try:
            value = int(parts[1].strip().rstrip(";"))
        except ValueError:
            continue
        mapping[name] = value

    return mapping


def _parse_msg_file(
    talk_script: str, msg_path: Path, index: MsgIndex
) -> Iterable[TextEntry]:
    content = msg_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    current_type: Optional[str] = None
    current_key: Optional[str] = None
    buffer: List[str] = []

    for line in content:
        match = MESSAGE_BLOCK_RE.match(line)
        if match:
            yield from _flush_block(talk_script, msg_path.name, current_type, current_key, buffer, index)
            current_type = match.group(1)
            current_key = match.group(2)
            buffer = []
        else:
            buffer.append(line)

    yield from _flush_block(talk_script, msg_path.name, current_type, current_key, buffer, index)


def _flush_block(
    talk_script: str,
    source_file: str,
    block_type: Optional[str],
    key: Optional[str],
    buffer: List[str],
    index: MsgIndex,
) -> Iterable[TextEntry]:
    if not block_type or not key:
        return []

    raw_text = "\n".join(buffer).strip()
    msg_id = index.key_to_id.get(key)
    question_group = None
    question_no = None

    match = QUESTION_RE.search(key)
    if match:
        question_group = match.group(1).upper()
        question_no = match.group(2)

    if block_type == "msg":
        msg_type = _classify_msg_key(key)
        clean_text = _clean_msg_text(raw_text)
        yield TextEntry(
            talk_script=talk_script,
            msg_id=msg_id,
            msg_key=key,
            msg_type=msg_type,
            source_file=source_file,
            text_raw=raw_text,
            text_clean=clean_text,
            choice_index=None,
            question_group=question_group,
            question_no=question_no,
        )
    elif block_type == "sel":
        for index_value, option_text in enumerate(_extract_selection_options(raw_text), start=1):
            clean_text = _clean_msg_text(option_text)
            yield TextEntry(
                talk_script=talk_script,
                msg_id=msg_id,
                msg_key=key,
                msg_type="selection",
                source_file=source_file,
                text_raw=option_text.strip(),
                text_clean=clean_text,
                choice_index=index_value,
                question_group=question_group,
                question_no=question_no,
            )
    else:
        LOGGER.debug("Unknown block type %s in %s", block_type, source_file)
        return []


def _classify_msg_key(key: str) -> str:
    if "_CHAT_" in key.upper():
        if "_R" in key.upper():
            return "reaction"
        return "question"
    if key.startswith("TalkSel"):
        return "selection"
    return "other"


def _extract_selection_options(raw_text: str) -> List[str]:
    options = re.findall(r"\[s[^\]]*\](.*?)\[e\]", raw_text, flags=re.DOTALL | re.IGNORECASE)
    return [option.strip() for option in options if option.strip()]


def _clean_msg_text(raw_text: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        token = match.group(1).strip().lower()
        if token.startswith("n"):
            return "\n"
        if token in {"s", "w", "e", "r", "top"}:
            return ""
        if token.startswith("vo") or token.startswith("se"):
            return ""
        return ""

    cleaned = TAG_RE.sub(_replace, raw_text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()

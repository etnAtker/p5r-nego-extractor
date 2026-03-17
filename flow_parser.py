"""Parse TALK *.flow files to extract negotiation reaction rules."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from models import MsgIndex, ReactionRule

LOGGER = logging.getLogger(__name__)

QUESTION_RE = re.compile(r"CHAT_(FQ|SQ)_(\d+)", re.IGNORECASE)

PERSONALITY_LABELS = {
    0: "懦弱",
    1: "性急",
    2: "开朗",
    3: "阴沉",
}

REACTION_GRADE_LABELS = {
    1: "喜欢",
    2: "一般",
    3: "反感",
}

@dataclass
class VariantConfig:
    label: str
    dispatch_func: str
    choice_var: str
    function_prefix: str


VARIANTS: Dict[str, VariantConfig] = {
    "FQ": VariantConfig(
        label="FQ",
        dispatch_func="chatFQ_get_reaction",
        choice_var="sVar125",
        function_prefix="chatFQ_get_reaction_FQ_",
    ),
    "SQ": VariantConfig(
        label="SQ",
        dispatch_func="chatSQ_get_reaction",
        choice_var="sVar183",
        function_prefix="chatSQ_get_reaction_SQ_",
    ),
}


class FlowParser:
    """Extracts rule mappings from a .flow file."""

    def __init__(self, talk_script: str, flow_path: Path, msg_index: MsgIndex):
        self.talk_script = talk_script
        self.flow_text = flow_path.read_text(encoding="utf-8", errors="ignore")
        self.msg_index = msg_index

    def extract_rules(self) -> List[ReactionRule]:
        rules: List[ReactionRule] = []

        for variant_name, config in VARIANTS.items():
            if config.dispatch_func not in self.flow_text:
                continue

            dispatch_body = self._get_function_body(config.dispatch_func)
            mapping = self._parse_dispatch(dispatch_body)

            for selection_id, function_name in mapping:
                if config.function_prefix not in function_name:
                    continue

                function_body = self._get_function_body(function_name)
                choice_map = self._parse_reaction_function(function_body, config.choice_var)
                selection_key = self.msg_index.id_to_key.get(selection_id)
                selection_choice_count = self.msg_index.selection_choice_counts.get(selection_id, 0)

                question_key = self.msg_index.derive_question_key(selection_key)
                question_msg_id = (
                    self.msg_index.key_to_id.get(question_key)
                    if question_key
                    else selection_id - 1
                )
                question_entry = (
                    self.msg_index.id_to_entry.get(question_msg_id) if question_msg_id else None
                )

                question_group = None
                question_no = None
                if question_entry and question_entry.question_group:
                    question_group = question_entry.question_group
                    question_no = question_entry.question_no
                elif question_key:
                    match = QUESTION_RE.search(question_key)
                    if match:
                        question_group = match.group(1).upper()
                        question_no = match.group(2)

                for choice_raw, persona_map in choice_map.items():
                    if selection_choice_count and choice_raw + 1 > selection_choice_count:
                        continue

                    for personality, payload in persona_map.items():
                        reaction_msg_id = selection_id + 1 + (choice_raw * 4) + payload.offset
                        reaction_msg_key = self.msg_index.id_to_key.get(reaction_msg_id)

                        rule = ReactionRule(
                            talk_script=self.talk_script,
                            variant=variant_name,
                            question_group=question_group,
                            question_no=question_no,
                            question_msg_id=question_msg_id,
                            question_msg_key=question_entry.msg_key if question_entry else question_key,
                            selection_msg_id=selection_id,
                            selection_msg_key=selection_key,
                            choice_raw=choice_raw,
                            choice_index=choice_raw + 1,
                            personality_value=personality,
                            personality_label=PERSONALITY_LABELS.get(personality, ""),
                            reaction_grade_raw=payload.grade,
                            reaction_grade_label=REACTION_GRADE_LABELS.get(payload.grade, ""),
                            reaction_offset=payload.offset,
                            reaction_msg_id=reaction_msg_id,
                            reaction_msg_key=reaction_msg_key,
                        )
                        rules.append(rule)

        return rules

    def _parse_dispatch(self, body: str) -> List[Tuple[int, str]]:
        pattern = re.compile(r"(?:else\s+)?if\s*\(\s*var\d+\s*==\s*(\d+)\s*\)\s*\{")
        mappings: List[Tuple[int, str]] = []
        pos = 0

        while True:
            match = pattern.search(body, pos)
            if not match:
                break

            selection_id = int(match.group(1))
            block, block_end = self._extract_brace_block(body, match.end() - 1)
            func_match = re.search(r"([a-zA-Z0-9_]+)\s*\(\s*\)\s*;", block)
            if func_match:
                mappings.append((selection_id, func_match.group(1)))
            else:
                LOGGER.warning("No reaction function call found for selection %s", selection_id)
            pos = block_end

        return mappings

    def _parse_reaction_function(
        self, body: str, choice_var: str
    ) -> Dict[int, Dict[int, "_ReactionPayload"]]:
        pattern = re.compile(
            r"(?:else\s+)?if\s*\(\s*%s\s*==\s*(\d+)\s*\)\s*\{" % re.escape(choice_var)
        )
        choice_map: Dict[int, Dict[int, _ReactionPayload]] = {}
        pos = 0

        while True:
            match = pattern.search(body, pos)
            if not match:
                break

            choice_value = int(match.group(1))
            block, block_end = self._extract_brace_block(body, match.end() - 1)
            persona_map = self._parse_personality_blocks(block)
            if persona_map:
                choice_map[choice_value] = persona_map
            pos = block_end

        return choice_map

    def _parse_personality_blocks(self, block: str) -> Dict[int, "_ReactionPayload"]:
        pattern = re.compile(r"(?:else\s+)?if\s*\(\s*sVar7\s*==\s*(\d+)\s*\)\s*\{")
        persona_map: Dict[int, _ReactionPayload] = {}
        pos = 0

        while True:
            match = pattern.search(block, pos)
            if not match:
                break

            personality = int(match.group(1))
            sub_block, sub_end = self._extract_brace_block(block, match.end() - 1)
            payload = self._extract_payload(sub_block)
            if payload:
                persona_map[personality] = payload
            pos = sub_end

        return persona_map

    def _extract_payload(self, block: str) -> Optional["_ReactionPayload"]:
        offset_match = re.search(r"var\d+\s*=\s*(\d+);", block)
        grade_match = re.search(r"sVar26\s*=\s*(\d+);", block)

        if not offset_match or not grade_match:
            LOGGER.warning("Failed to extract payload from block: %s", block.strip())
            return None

        return _ReactionPayload(offset=int(offset_match.group(1)), grade=int(grade_match.group(1)))

    def _get_function_body(self, function_name: str) -> str:
        pattern = re.compile(r"void\s+%s\s*\([^)]*\)\s*\{" % re.escape(function_name))
        match = pattern.search(self.flow_text)
        if not match:
            raise ValueError(f"Function {function_name} not found in flow script")

        body, _ = self._extract_brace_block(self.flow_text, match.end() - 1)
        return body

    @staticmethod
    def _extract_brace_block(text: str, open_brace_index: int) -> Tuple[str, int]:
        depth = 0
        i = open_brace_index
        while i < len(text):
            char = text[i]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[open_brace_index + 1 : i], i + 1
            i += 1

        raise ValueError("Braces did not match while extracting block")


@dataclass
class _ReactionPayload:
    offset: int
    grade: int

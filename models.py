"""Dataclasses shared across the negotiation extraction pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class TextEntry:
    """Represents a single text record extracted from a .msg file."""

    talk_script: str
    msg_id: Optional[int]
    msg_key: str
    msg_type: str
    source_file: str
    text_raw: str
    text_clean: str
    choice_index: Optional[int] = None
    question_group: Optional[str] = None
    question_no: Optional[str] = None


@dataclass
class MsgIndex:
    """Holds parsed message metadata for quick lookup during joins."""

    talk_script: str
    entries: List[TextEntry] = field(default_factory=list)
    key_to_id: Dict[str, int] = field(default_factory=dict)
    id_to_key: Dict[int, str] = field(default_factory=dict)
    id_to_entry: Dict[int, TextEntry] = field(default_factory=dict)
    selection_entries: Dict[Tuple[int, int], TextEntry] = field(default_factory=dict)
    selection_choice_counts: Dict[int, int] = field(default_factory=dict)

    def add_entry(self, entry: TextEntry) -> None:
        self.entries.append(entry)

        if entry.msg_id is not None:
            if entry.msg_type == "selection" and entry.choice_index:
                key = (entry.msg_id, entry.choice_index)
                self.selection_entries[key] = entry
                current = self.selection_choice_counts.get(entry.msg_id, 0)
                self.selection_choice_counts[entry.msg_id] = max(current, entry.choice_index)
            else:
                self.id_to_entry[entry.msg_id] = entry

    def derive_question_key(self, selection_key: Optional[str]) -> Optional[str]:
        if not selection_key:
            return None

        if selection_key.startswith("TalkSel"):
            candidate = selection_key.replace("TalkSel", "TalkMsg", 1)
            if candidate in self.key_to_id:
                return candidate

        return None


@dataclass
class ReactionRule:
    """Represents one rule extracted from the .flow file."""

    talk_script: str
    variant: str
    question_group: Optional[str]
    question_no: Optional[str]
    question_msg_id: Optional[int]
    question_msg_key: Optional[str]
    selection_msg_id: int
    selection_msg_key: Optional[str]
    choice_raw: int
    choice_index: int
    personality_value: int
    personality_label: str
    reaction_grade_raw: int
    reaction_grade_label: str
    reaction_offset: int
    reaction_msg_id: Optional[int]
    reaction_msg_key: Optional[str]


@dataclass
class FlatRow:
    """A fully joined row ready for the final CSV output."""

    talk_script: str
    question_group: Optional[str]
    question_no: Optional[str]
    question_msg_id: Optional[int]
    question_msg_key: Optional[str]
    question_text_raw: Optional[str]
    question_text_clean: Optional[str]
    choice_index: int
    choice_text_raw: Optional[str]
    choice_text_clean: Optional[str]
    personality_value: int
    personality_label: str
    reaction_grade_raw: int
    reaction_grade_label: str
    reaction_msg_id: Optional[int]
    reaction_msg_key: Optional[str]
    reaction_text_raw: Optional[str]
    reaction_text_clean: Optional[str]


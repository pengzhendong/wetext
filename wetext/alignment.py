# Copyright (c) 2026, WENET COMMUNITY.
#
# Licensed under the Apache License, Version 2.0 (the "License");

from dataclasses import dataclass
from typing import Dict, Tuple


class AlignmentError(RuntimeError):
    """Raised when a normalization path cannot be traced exactly."""


@dataclass(frozen=True)
class NormalizationMapping:
    kind: str
    token_type: str
    input_start: int
    input_end: int
    output_start: int
    output_end: int
    input_text: str
    output_text: str

    def as_dict(self) -> Dict:
        return {
            "kind": self.kind,
            "token_type": self.token_type,
            "input": {"start": self.input_start, "end": self.input_end, "text": self.input_text},
            "output": {"start": self.output_start, "end": self.output_end, "text": self.output_text},
        }


@dataclass(frozen=True)
class NormalizationResult:
    input_text: str
    output_text: str
    mappings: Tuple[NormalizationMapping, ...]

    def as_dict(self) -> Dict:
        return {
            "input": self.input_text,
            "output": self.output_text,
            "mappings": [mapping.as_dict() for mapping in self.mappings],
        }

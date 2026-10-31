"""Reverse-only directions use upstream's grouped candidates and exclusions."""

import json
from pathlib import Path

import pytest

from wetext import Normalizer

DATA = Path(__file__).parent / "data"
CONTRACTS = json.loads((DATA / "reverse_contracts.json").read_text(encoding="utf-8"))
CASES = []
EXCLUDED = []
for contract in CONTRACTS:
    groups = {}
    for path in sorted((DATA / contract["lang"] / contract["source_operator"]).glob("*.txt")):
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                left, *right = (line[:-1] if line.endswith("\n") else line).split("~")
                for value in right:
                    groups.setdefault(value, []).append(left)
    assert len(groups) == contract["group_count"]
    assert set(contract["excluded"]) <= set(groups)
    accepted = 0
    for source, expected in groups.items():
        case = pytest.param(contract, source, expected, id=f"{contract['lang']}/{source or 'empty'}")
        if source in contract["excluded"]:
            EXCLUDED.append(case)
        else:
            CASES.append(case)
            accepted += 1
    assert accepted == contract["checked_count"]


@pytest.mark.parametrize("contract,source,expected", CASES)
def test_reversed_output_and_mapping(contract, source, expected):
    normalizer = Normalizer(lang=contract["lang"], operator=contract["operator"])
    output = normalizer.normalize(source)
    assert output in expected
    result = normalizer.normalize_with_mapping(source, include_identity=True)
    assert result.output_text == output
    for mapping in result.mappings:
        assert source[mapping.input_start : mapping.input_end] == mapping.input_text
        assert output[mapping.output_start : mapping.output_end] == mapping.output_text


@pytest.mark.parametrize("contract,source,expected", EXCLUDED)
def test_documented_exclusions(contract, source, expected):
    assert contract["excluded"][source]
    normalizer = Normalizer(lang=contract["lang"], operator=contract["operator"])
    output = normalizer.normalize(source)
    # These are explicit upstream limitations, not silent skips. Canonical
    # semantics for Marathi/Hebrew are covered by separate hand-written cases.
    if contract["lang"] in ("rw", "it", "hu"):
        assert output not in expected
    assert normalizer.normalize_with_mapping(source).output_text == output
    if contract["lang"] == "rw":
        assert output == contract["excluded"][source]

"""Offline regression against upstream full-pipeline fixture inventories."""

import json
from pathlib import Path

import pytest

from wetext import Normalizer

DATA = Path(__file__).parent / "data"
SUITES = json.loads((DATA / "suites.json").read_text(encoding="utf-8"))


def load_cases():
    cases = []
    for suite in SUITES:
        count = 0
        for filename in suite["files"]:
            path = DATA / suite["lang"] / suite["operator"] / filename
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if suite["lang"] == "ko":
                    source, expected = line.split("~")
                else:
                    # Match upstream parse_test_case; Korean spaces are significant.
                    source, expected = (value.strip() for value in line.split("=>"))
                cases.append(pytest.param(suite, source, expected, id=f"{suite['id']}/{filename}:{number}"))
                count += 1
        assert count == suite["count"], suite["id"]
    return cases


CASES = load_cases()


@pytest.mark.parametrize("suite,source,expected", CASES)
def test_normalize(suite, source, expected):
    normalizer = Normalizer(lang=suite["lang"], operator=suite["operator"], **suite["options"])
    assert normalizer.normalize(source) == expected


@pytest.mark.parametrize("suite,source,expected", CASES)
def test_mapping(suite, source, expected):
    normalizer = Normalizer(lang=suite["lang"], operator=suite["operator"], **suite["options"])
    result = normalizer.normalize_with_mapping(source, include_identity=True)
    assert result.output_text == expected
    if source:
        assert result.mappings
    input_end = output_end = 0
    for mapping in result.mappings:
        assert mapping.input_start >= input_end
        assert mapping.output_start >= output_end
        input_end, output_end = mapping.input_end, mapping.output_end
        assert 0 <= mapping.input_start <= mapping.input_end <= len(source)
        assert 0 <= mapping.output_start <= mapping.output_end <= len(expected)
        assert source[mapping.input_start : mapping.input_end] == mapping.input_text
        assert expected[mapping.output_start : mapping.output_end] == mapping.output_text

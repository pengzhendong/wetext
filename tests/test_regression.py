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
            with path.open(encoding="utf-8") as stream:
                for number, line in enumerate(stream, 1):
                    line = line[:-1] if line.endswith("\n") else line
                    if suite.get("format") == "tilde" or suite["lang"] in ("ko", "de"):
                        source, *expected = line.split("~")
                        reverse = suite.get("reverse", suite["lang"] == "de" and suite["operator"] == "tn")
                        if reverse or filename in suite.get("reverse_files", []):
                            source, expected = expected[0], [source]
                        if suite.get("strip_expected"):
                            expected = [value.strip() for value in expected]
                    else:
                        source, expected = (value.strip() for value in line.split("=>"))
                        expected = [expected]
                    cases.append(pytest.param(suite, source, expected, id=f"{suite['id']}/{filename}:{number}"))
                    count += 1
        assert count == suite["count"], suite["id"]
    return cases


CASES = load_cases()


def select_output(normalizer, suite, source, expected):
    """Respect upstream's first-output versus bounded candidate contracts."""
    limit = suite.get("candidate_limit", 1)
    if limit == 1:
        output = normalizer.normalize(source)
        assert output in expected
        return 1, output
    for nbest in (10, limit):
        outputs = normalizer.normalize(source, nbest=nbest)
        for rank, output in enumerate(outputs, 1):
            if output in expected:
                return rank, output
    pytest.fail(f"No expected output among top {limit}: {expected!r}")


@pytest.mark.parametrize("suite,source,expected", CASES)
def test_normalize(suite, source, expected):
    normalizer = Normalizer(lang=suite["lang"], operator=suite["operator"], **suite["options"])
    select_output(normalizer, suite, source, expected)


@pytest.mark.parametrize("suite,source,expected", CASES)
def test_mapping(suite, source, expected):
    normalizer = Normalizer(lang=suite["lang"], operator=suite["operator"], **suite["options"])
    rank, output = select_output(normalizer, suite, source, expected)
    result = normalizer.normalize_with_mapping(source, nbest=rank, include_identity=True)
    if rank > 1:
        result = result[-1]
    assert result.output_text == output
    if source.strip():
        assert result.mappings
    input_end = output_end = 0
    for mapping in result.mappings:
        assert mapping.input_start >= input_end
        assert mapping.output_start >= output_end
        input_end, output_end = mapping.input_end, mapping.output_end
        assert 0 <= mapping.input_start <= mapping.input_end <= len(source)
        assert 0 <= mapping.output_start <= mapping.output_end <= len(output)
        assert source[mapping.input_start : mapping.input_end] == mapping.input_text
        assert output[mapping.output_start : mapping.output_end] == mapping.output_text

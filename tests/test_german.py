"""German candidate fixtures and runtime integration, without Pynini."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from wetext import Normalizer, StreamNormalizer, tag
from wetext.cli import main
from wetext.token_parser import TokenParser

DATA = Path(__file__).parent / "data" / "de" / "tn"
SINGLE = []
ORDINAL = []
for path in sorted(DATA.glob("*.txt")):
    if path.name == "test_cases_normalize_with_audio.txt":
        continue
    for line in path.read_text(encoding="utf-8").splitlines():
        spoken, source = line.split("~")
        (ORDINAL if path.name == "test_cases_ordinal.txt" else SINGLE).append((source, spoken))

MULTIPLE = []
for line in (DATA / "test_cases_normalize_with_audio.txt").read_text(encoding="utf-8").splitlines():
    if line.startswith("~"):
        MULTIPLE.append((line[1:], []))
    else:
        MULTIPLE[-1][1].append(line)


def test_fixture_inventory():
    assert len(SINGLE) == 265
    assert len(ORDINAL) == 19
    assert len(MULTIPLE) == 31
    assert sum(len(expected) for _, expected in MULTIPLE) == 100


def contains_candidates(normalizer, source, expected):
    # Same 1000-candidate ceiling as upstream; avoid expanding once all
    # required outputs are present, as upstream Swedish tests already do.
    for nbest in (10, 100, 1000):
        if set(expected) <= set(normalizer.normalize(source, nbest=nbest)):
            return True
    return False


@pytest.mark.parametrize("source,expected", SINGLE + ORDINAL)
def test_nondeterministic_source(source, expected):
    normalizer = Normalizer(lang="de", deterministic=False)
    assert contains_candidates(normalizer, source, [expected])


@pytest.mark.parametrize("source,expected", MULTIPLE)
def test_multiple_candidates(source, expected):
    assert contains_candidates(Normalizer(lang="de", deterministic=False), source, expected)


@pytest.mark.parametrize(
    "operator,source",
    [("tn", "02.03.2003"), ("tn", "$2,20"), ("tn", "11:30 Uhr"), ("itn", "halb zwölf"), ("itn", "zwei euro")],
)
def test_candidate_mapping_consistency(operator, source):
    normalizer = Normalizer(lang="de", operator=operator, deterministic=False)
    outputs = normalizer.normalize(source, nbest=3)
    assert outputs[0] == normalizer.normalize(source)
    assert len(set(outputs)) == len(outputs)
    assert [c.text for c in normalizer.normalize_candidates(source, nbest=3)] == outputs
    assert [r.output_text for r in normalizer.normalize_with_mapping(source, nbest=3)] == outputs


@pytest.mark.parametrize("operator,source", [("tn", "Heute 12 Euro。"), ("itn", "heute zwölf euro")])
def test_stream(operator, source):
    stream = StreamNormalizer(lang="de", operator=operator)
    for char in source:
        stream.feed(char)
    assert stream.flush() == Normalizer(lang="de", operator=operator).normalize(source)


def test_modes_cli_escaping_and_raw_fields():
    assert Normalizer(lang="de").normalize("dr.") == "dr."
    assert Normalizer(lang="de", deterministic=False).normalize("dr.") == "doktor"
    result = CliRunner().invoke(main, ["--lang", "de", "--no-deterministic", "dr."])
    assert result.exit_code == 0
    assert result.output == "doktor\n"
    for op in ("tn", "itn"):
        source = 'grün\\pfad"中文'
        normalizer = Normalizer(lang="de", operator=op)
        assert normalizer.normalize(source) == source
        assert normalizer.normalize_with_mapping(source).output_text == source
        assert normalizer.normalize("") == ""
    parser = TokenParser("de")
    parser.parse(tag("02:03:01 Uhr", "de", "tn"))
    assert parser.tokens[0].members == {"hours": "02", "minutes": "03", "seconds": "01"}

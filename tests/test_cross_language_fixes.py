"""Runtime regressions for upstream's cross-language consistency changes."""

import re

import pytest

from wetext import Normalizer, tag
from wetext.languages import LANGUAGES
from wetext.token_parser import TokenParser

PIPELINES = [(lang, op) for lang, spec in LANGUAGES.items() for op in spec["directions"]]
INPUTS = ["a  b", "#1", "1#", "a #1", 'quote "x"', "back\\slash", "hello , world .", "x\ty", "😀 ok"]


@pytest.mark.parametrize("lang,operator", PIPELINES)
@pytest.mark.parametrize("source", INPUTS)
def test_every_pipeline_returns_output(lang, operator, source):
    normalizer = Normalizer(lang=lang, operator=operator)
    output = normalizer.normalize(source)
    assert output.strip()
    assert normalizer.normalize_with_mapping(source, include_identity=True).output_text == output


@pytest.mark.parametrize(
    "lang", [code for code, spec in LANGUAGES.items() if "tn" in spec["directions"] and code != "de"]
)
@pytest.mark.parametrize("source", ["(5)", "5, 6.", "x (12) y, 7!"])
def test_attached_punctuation(lang, source):
    output = Normalizer(lang=lang).normalize(source)
    assert not re.search(r" [,.!?;:)\]}]", output), output
    assert not re.search(r"[(\[{] ", output), output


@pytest.mark.parametrize("lang", ["de", "fr", "ru", "sv"])
@pytest.mark.parametrize("source", ["3.14", "03.14", "3.13", "3.00"])
def test_invalid_numeric_dates(lang, source):
    parser = TokenParser(lang)
    parser.parse(tag(source, lang, "tn"))
    assert all(token.name != "date" for token in parser.tokens)


@pytest.mark.parametrize(
    "lang,operator,source,expected",
    [
        ("ko", "tn", "1,000,000", "백만"),
        ("hi", "tn", "5%", "पाँच प्रतिशत"),
        ("fr", "tn", "(5)", "(cinq)"),
        ("fr", "tn", "20 !", "vingt !"),
        ("de", "tn", "20!", "zwanzig !"),
        ("rw", "tn", "1:00", "saa saba "),
        ("it", "itn", "a chiocciola b punto com e poi", "a@b.com e poi"),
        ("es_en", "itn", "pagué doce dólares and two dollars", "pagué $12 and $2"),
        ("es_en", "itn", "two lakh five thousand", "205000"),
        ("mr", "tn", "५८०१", "पाच हजार आठशे एक"),
        ("mr", "tn", "१०:५८", "अकराला दोन मिनिटे"),
        ("mr", "tn", "०६:४८", "सहा वाजून अठ्ठेचाळीस मिनिटे"),
        ("mr", "tn", "०९:३०", "साडे नऊ"),
        ("he", "tn", "15 איש", "חמישה עשר איש"),
    ],
)
def test_specific_semantics(lang, operator, source, expected):
    normalizer = Normalizer(lang=lang, operator=operator)
    assert normalizer.normalize(source) == expected
    assert normalizer.normalize_with_mapping(source).output_text == expected

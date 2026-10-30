import pytest
from click.testing import CliRunner

from wetext import Normalizer, StreamNormalizer
from wetext.cli import main
from wetext.token_parser import TokenParseError, TokenParser
from wetext.utils import get_lang


@pytest.mark.parametrize(
    "operator,source",
    [
        ("tn", "2024년"),
        ("tn", "1/2"),
        ("tn", "$10"),
        ("tn", "10:30"),
        ("itn", "십이"),
        ("itn", "이분의일"),
        ("itn", "만천"),
        ("itn", "만천백십일"),
    ],
)
def test_nbest(operator, source):
    normalizer = Normalizer(lang="ko", operator=operator, enable_0_to_9=True)
    outputs = normalizer.normalize(source, nbest=3)
    assert outputs[0] == normalizer.normalize(source)
    assert len(outputs) == len(set(outputs))
    assert [c.text for c in normalizer.normalize_candidates(source, nbest=3)] == outputs
    assert [r.output_text for r in normalizer.normalize_with_mapping(source, nbest=3)] == outputs


@pytest.mark.parametrize("operator,source", [("tn", "2024년입니다。12월"), ("itn", "십이 개입니다")])
def test_stream(operator, source):
    stream = StreamNormalizer(lang="ko", operator=operator)
    for char in source:
        stream.feed(char)
    assert stream.flush() == Normalizer(lang="ko", operator=operator).normalize(source)


@pytest.mark.parametrize("operator", ["tn", "itn"])
def test_escaping_and_empty(operator):
    normalizer = Normalizer(lang="ko", operator=operator)
    source = '경로\\a"b'
    assert normalizer.normalize(source) == source
    assert normalizer.normalize_with_mapping(source).output_text == source
    for empty in ("", " ", "\t\n"):
        assert normalizer.normalize(empty) == ""
        assert normalizer.normalize(empty, nbest=3) == [""]


def test_auto_and_cli():
    assert get_lang("가격 12원") == "ko"
    assert get_lang("こんにちは12") == "ja"
    assert get_lang("你好12") == "zh"
    assert get_lang("123") == "zh"
    assert Normalizer().normalize("2024년") == Normalizer(lang="ko").normalize("2024년")
    result = CliRunner().invoke(main, ["--lang", "ko", "--operator", "itn", "십이"])
    assert result.exit_code == 0
    assert result.output == "12\n"


@pytest.mark.parametrize("text", ['word { value: "unterminated', 'word { value: "x"', 'word { value: "x" value: "y" }'])
def test_malformed_tokens(text):
    with pytest.raises(TokenParseError):
        TokenParser("ko").reorder(text)

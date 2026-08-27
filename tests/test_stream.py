import pytest

import wetext.stream as streaming
from wetext import StreamNormalizer

RULE = "二十米"


def fake_match_prefix_position(text, _lang, _operator, _enable_0_to_9):
    for index in range(len(text)):
        if RULE.startswith(text[index:]):
            return index
    return len(text)


def fake_normalize(text, config):
    del config
    return text.replace(RULE, "20m").replace("二十", "20")


@pytest.fixture(autouse=True)
def fake_runtime(monkeypatch):
    monkeypatch.setattr(streaming, "_match_prefix_position", fake_match_prefix_position)
    monkeypatch.setattr(streaming, "normalize", fake_normalize)


def test_stream_owns_pending_state_and_returns_current_text():
    stream = StreamNormalizer(lang="zh")

    assert stream.feed("今天有") == "今天有"
    assert stream.feed("二十") == "今天有20"
    assert stream.feed("米") == "今天有20m"
    assert stream.flush() == "今天有20m"


@pytest.mark.parametrize("operator", ["itn", "tn"])
def test_missing_prefix_graph_buffers_until_flush(monkeypatch, operator):
    monkeypatch.setattr(streaming, "_match_prefix_position", lambda *_args: None)
    stream = StreamNormalizer(lang="zh", operator=operator)

    assert stream.feed("二十") == "20"
    assert stream.feed("米") == "20m"
    assert stream.flush() == "20m"


def test_tn_selects_tn_prefix_graph(monkeypatch):
    operators = []

    def match(text, _lang, operator, _enable_0_to_9):
        operators.append(operator)
        return len(text)

    monkeypatch.setattr(streaming, "_match_prefix_position", match)
    stream = StreamNormalizer(lang="zh", operator="tn")

    assert stream.feed("价格") == "价格"
    assert operators == ["tn"]


def test_tn_keeps_cross_chunk_decimal_and_unit_together(monkeypatch):
    rule = "12.5元"

    def match(text, _lang, operator, _enable_0_to_9):
        assert operator == "tn"
        for index in range(len(text)):
            if rule.startswith(text[index:]):
                return index
        return len(text)

    def normalize_tn(text, config):
        assert config.operator == "tn"
        return text.replace(rule, "十二点五元").replace("12.5", "十二点五")

    monkeypatch.setattr(streaming, "_match_prefix_position", match)
    monkeypatch.setattr(streaming, "normalize", normalize_tn)
    stream = StreamNormalizer(lang="zh", operator="tn")

    assert stream.feed("价格是12") == "价格是12"
    assert stream.feed(".5") == "价格是十二点五"
    assert stream.feed("元") == "价格是十二点五元"
    assert stream.flush() == "价格是十二点五元"


def test_ascii_token_is_not_committed_across_chunk_boundary(monkeypatch):
    monkeypatch.setattr(streaming, "_match_prefix_position", lambda text, *_args: len(text))
    stream = StreamNormalizer(lang="en", fix_contractions=True)

    assert stream.feed("don") == "don"
    assert stream.feed("'t") == "don't"
    assert stream.feed(" ") == "don't"
    assert stream.feed("stop") == "don't stop"


def test_nested_prefix_rolls_back_to_fixed_point(monkeypatch):
    positions = {
        "二分之一加三分": 5,
        "二分之一加": 3,
        "二分之": 0,
    }
    monkeypatch.setattr(
        streaming,
        "_match_prefix_position",
        lambda text, *_args: positions.get(text, len(text)),
    )
    stream = StreamNormalizer(lang="zh")

    assert stream._safe_position("二分之一加三分") == 0


def test_long_open_prefix_uses_bounded_probe(monkeypatch):
    calls = []

    def match(text, *_args):
        calls.append(len(text))
        return 0

    monkeypatch.setattr(streaming, "_match_prefix_position", match)
    stream = StreamNormalizer(lang="zh")

    assert stream._safe_position("一" * 255) == 0
    assert calls == [streaming._PREFIX_PROBE_CHARS]


def test_hard_boundary_commits_without_prefix_scan(monkeypatch):
    def unexpected_match(*_args):
        raise AssertionError("hard boundaries must not scan the prefix graph")

    monkeypatch.setattr(streaming, "_match_prefix_position", unexpected_match)
    stream = StreamNormalizer(lang="zh")

    text = "一" * 255 + "。"
    assert stream._safe_position(text) == len(text)


def test_pending_render_normalizes_a_bounded_tail(monkeypatch):
    lengths = []

    def normalize_tail(text, config):
        del config
        lengths.append(len(text))
        return text

    monkeypatch.setattr(streaming, "normalize", normalize_tail)
    monkeypatch.setattr(streaming, "_match_prefix_position", lambda *_args: 0)
    stream = StreamNormalizer(lang="zh")

    text = "一" * 255
    assert stream.feed(text) == text
    assert lengths == [streaming._PENDING_RENDER_CHARS]


def test_flush_normalizes_the_complete_pending_input(monkeypatch):
    monkeypatch.setattr(
        streaming,
        "normalize",
        lambda text, config: f"<{len(text)}:{config.lang}>",
    )
    monkeypatch.setattr(streaming, "_match_prefix_position", lambda *_args: 0)
    stream = StreamNormalizer(lang="zh")
    text = "一" * 255

    current = stream.feed(text)
    assert current.endswith(f"<{streaming._PENDING_RENDER_CHARS}:zh>")
    assert stream.flush() == "<255:zh>"


def test_english_boundary_whitespace_is_canonicalized(monkeypatch):
    monkeypatch.setattr(streaming, "_match_prefix_position", lambda text, *_args: len(text))
    stream = StreamNormalizer(lang="en")

    assert stream.feed("hello  ") == "hello"
    assert stream.feed("world") == "hello world"


def test_flush_is_idempotent_but_feed_requires_reset():
    stream = StreamNormalizer(lang="zh")
    stream.feed("普通文本")
    final = stream.flush()

    assert stream.flush() == final
    with pytest.raises(RuntimeError, match="reset"):
        stream.feed("新句子")

    stream.reset()
    assert stream.feed("新句子") == "新句子"


@pytest.mark.parametrize("kwargs", [{}, {"lang": "zh", "operator": "invalid"}])
def test_stream_requires_fixed_language_and_valid_operator(kwargs):
    with pytest.raises(ValueError):
        StreamNormalizer(**kwargs)


def test_feed_rejects_non_string_input():
    stream = StreamNormalizer(lang="zh")
    with pytest.raises(TypeError):
        stream.feed(None)

"""Fused character rewrites must preserve the existing processor order."""

from itertools import product
import random

import pytest

from wetext.constants import FSTS, processor_key
from wetext.fst_utils import transduce_with_spans
from wetext.utils import _read_fst
from wetext.constants import FST_PATHS


def sequential(text, options):
    for name, group in (
        ("traditional_to_simple", "preprocess"),
        ("full_to_half", "postprocess"),
        ("remove_interjections", "postprocess"),
        ("remove_puncts", "postprocess"),
        ("tag_oov", "postprocess"),
    ):
        if options[name]:
            text = FSTS[group][name](text)
    return text


@pytest.mark.parametrize("flags", list(product((False, True), repeat=5)))
def test_all_option_combinations(flags):
    names = ("traditional_to_simple", "remove_interjections", "remove_puncts", "full_to_half", "tag_oov")
    options = dict(zip(names, flags))
    key = processor_key(options)
    rng = random.Random(383)
    alphabet = '蘋果呃啊Ａａ１２３，。！？\\" 🙂한글日本語\t\n'
    samples = ["", alphabet, "這是12.5元，呃啊！", "Ａ，１２３！", '路徑\\a"b']
    samples += ["".join(rng.choice(alphabet) for _ in range(20)) for _ in range(30)]
    for source in samples:
        expected = sequential(source, options)
        output = FSTS["processors"][key](source) if any(flags) else source
        assert output == expected
        if any(flags):
            # The same graph is composed into n-best/mapping verbalizers.
            output, _ = transduce_with_spans(source, _read_fst(FST_PATHS["processors"][key]))
            assert output == expected


def test_legacy_bundle_fallback(monkeypatch):
    from wetext import Normalizer
    from wetext.utils import _cached_graphs

    normalizer = Normalizer(lang="zh", full_to_half=True, remove_interjections=True)
    source = "呃价格１２元"
    expected = normalizer.normalize(source)
    _cached_graphs.cache_clear()
    key = processor_key(dict(full_to_half=True, remove_interjections=True))
    monkeypatch.setitem(FST_PATHS["processors"], key, "/missing-legacy-fused-processor.fst")
    assert normalizer.normalize(source) == expected
    assert normalizer.normalize_with_mapping(source).output_text == expected
    _cached_graphs.cache_clear()

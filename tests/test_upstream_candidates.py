"""Candidate-only contracts and original audio fixture groups."""

from pathlib import Path

import pytest

from wetext import Normalizer

DATA = Path(__file__).parent / "data"
# Preserve the upstream Russian test's explicit handling of two source typos.
RUSSIAN_TYPOS = {
    "сорое шесть тысяч шестьсот шестьдесят четыре": "сорок шесть тысяч шестьсот шестьдесят четыре",
    "сорое шесть тысяч шестьсот шестьдесят четырый": "сорок шесть тысяч шестьсот шестьдесят четвертый",
}


def audio_cases():
    cases = []
    for lang, filename in (
        ("sv", "test_cases_normalize_with_audio.txt"),
        ("es", "test_cases_normalize_with_audio.txt"),
        ("ru", "test_cases_cardinal_normalize_with_audio.txt"),
    ):
        groups = []
        for line in (DATA / lang / "tn" / filename).read_text(encoding="utf-8").splitlines():
            if line.startswith("~"):
                groups.append((line[1:], []))
            else:
                groups[-1][1].append(line)
        for source, expected in groups:
            cases.append(pytest.param(lang, source, expected, id=f"{lang}/{source}"))
    return cases


AUDIO = audio_cases()


@pytest.mark.parametrize("lang,source,expected", AUDIO)
def test_audio_candidates(lang, source, expected):
    corrected = {RUSSIAN_TYPOS.get(value, value) if lang == "ru" else value for value in expected}
    normalizer = Normalizer(lang=lang, deterministic=False)
    limit = 100 if lang == "ru" else 1000
    for nbest in (10, 100, limit):
        outputs = set(normalizer.normalize(source, nbest=nbest))
        if corrected <= outputs:
            break
    assert corrected <= outputs
    if lang == "ru":
        assert not set(RUSSIAN_TYPOS) & outputs


NONDETERMINISTIC = []
for lang, limit in (("sv", 1000), ("es", 500)):
    for path in sorted((DATA / lang / "tn").glob("*.txt")):
        if "normalize_with_audio" in path.name:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            source, *expected = line.split("~")
            NONDETERMINISTIC.append(pytest.param(lang, source, expected, limit, id=f"{lang}/{path.name}:{number}"))


@pytest.mark.parametrize("lang,source,expected,limit", NONDETERMINISTIC)
def test_nondeterministic_source(lang, source, expected, limit):
    normalizer = Normalizer(lang=lang, deterministic=False)
    for nbest in (10, min(100, limit), limit):
        outputs = normalizer.normalize(source, nbest=nbest)
        if any(value in outputs for value in expected):
            return
    pytest.fail(f"Missing expected reading among {limit} candidates: {expected!r}")


def test_audio_inventory():
    # Russian has 23 fixture groups for 21 distinct inputs; keep repeats.
    assert len(AUDIO) == 3 + 29 + 23
    for lang, groups, unique_inputs, outputs in (("sv", 3, 3, 11), ("es", 29, 27, 133), ("ru", 23, 21, 28)):
        cases = [case.values for case in AUDIO if case.values[0] == lang]
        assert len(cases) == groups
        assert len({source for _, source, _ in cases}) == unique_inputs
        assert sum(len(expected) for _, _, expected in cases) == outputs
    assert len(NONDETERMINISTIC) == 253 + 537

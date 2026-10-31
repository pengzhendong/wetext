"""Runtime language inventory and graph-variant selection (no compiler imports)."""

import json
from importlib.resources import files

LANGUAGES = json.loads(files("wetext").joinpath("language_registry.json").read_text(encoding="utf-8"))


def model_names(lang, operator, enable_0_to_9=False, remove_erhua=False, deterministic=True, cased=False):
    pipeline = LANGUAGES[lang]
    suffix = ""
    if operator == "tn" and pipeline["tn_deterministic"] and not deterministic:
        suffix = "_nondeterministic"
    if operator == "itn" and pipeline["itn_cased"] and cased:
        suffix = "_cased"
    tagger, verbalizer = "tagger" + suffix, "verbalizer" + suffix
    if enable_0_to_9 and lang in ("zh", "ja") and operator == "itn":
        tagger, verbalizer = "tagger_enable_0_to_9", "verbalizer_enable_0_to_9"
    if remove_erhua and lang == "zh" and operator == "tn":
        verbalizer = "verbalizer_remove_erhua"
    return tagger, verbalizer

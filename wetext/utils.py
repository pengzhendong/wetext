# Copyright (c) 2024 Zhendong Peng (pzd17@tsinghua.org.cn)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import heapq
import re
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

import contractions
import kaldifst

from wetext.alignment import NormalizationCandidate, NormalizationMapping, NormalizationResult
from wetext.config import NormalizerConfig
from wetext.constants import FSTS, FST_PATHS, processor_key
from wetext.fst_utils import (
    UniqueOutputPathStream,
    compose_input,
    trace_input_spans,
    transduce_with_spans,
)
from wetext.token_parser import TokenParser
from wetext.languages import model_names


@dataclass(frozen=True)
class _NormalizationCandidate:
    tagged: str
    output: str
    tagger_weight: float
    verbalizer_weight: float
    best_verbalizer_weight: float
    tagger_rank: int
    verbalizer_rank: int

    @property
    def weight(self):
        return self.tagger_weight + self.verbalizer_weight - self.best_verbalizer_weight


@lru_cache(maxsize=None)
def _read_fst(path):
    return kaldifst.StdVectorFst.read(path)


def _processor_path(key):
    path = FST_PATHS["processors"][key]
    return path if Path(path).is_file() else None


def _graphs(config, lang):
    return _cached_graphs(lang, tuple(vars(config).items()))


@lru_cache(maxsize=32)
def _cached_graphs(lang, options):
    config = NormalizerConfig(**dict(options))
    tagger_name, verbalizer_name = model_names(
        lang, config.operator, config.enable_0_to_9, config.remove_erhua, config.deterministic, config.cased
    )
    tagger = _read_fst(FST_PATHS[lang][config.operator][tagger_name])
    verbalizer = _read_fst(FST_PATHS[lang][config.operator][verbalizer_name])
    key = processor_key(vars(config))
    if "1" in key:
        verbalizer = verbalizer.copy()
        fused = _processor_path(key)
        paths = (
            [fused]
            if fused
            else [
                FST_PATHS[group][name]
                for group, name in (
                    ("preprocess", "traditional_to_simple"),
                    ("postprocess", "full_to_half"),
                    ("postprocess", "remove_interjections"),
                    ("postprocess", "remove_puncts"),
                    ("postprocess", "tag_oov"),
                )
                if getattr(config, name)
            ]
        )
        for path in paths:
            kaldifst.arcsort(verbalizer, "olabel")
            verbalizer = kaldifst.compose(verbalizer, _read_fst(path))
    return tagger, verbalizer


def _validate_nbest(nbest):
    if isinstance(nbest, bool) or not isinstance(nbest, int) or nbest < 1:
        raise ValueError("nbest must be a positive integer")


def _normalization_candidates(text, lang, operator, tagger, verbalizer, nbest):
    tagger_stream = UniqueOutputPathStream(
        compose_input(text, tagger), prefer_native=not (lang == "en" and operator == "tn")
    )
    frontier = []
    activated = 0
    candidates = []
    seen_outputs = set()

    def activate_next_tag():
        nonlocal activated
        tagged_path = tagger_stream.pop()
        if tagged_path is None:
            return False
        reordered = TokenParser(lang, operator).reorder(tagged_path.text)
        verbalizer_stream = UniqueOutputPathStream(
            compose_input(reordered, verbalizer),
            prefer_native=True,
            native_projection=lang == "en" and operator == "tn",
        )
        verbalized_path = verbalizer_stream.pop()
        tagger_rank = tagged_path.rank
        activated += 1
        if verbalized_path is None:
            return True
        candidate = _NormalizationCandidate(
            tagged_path.text,
            verbalized_path.text,
            tagged_path.weight,
            verbalized_path.weight,
            verbalized_path.weight,
            tagger_rank,
            verbalized_path.rank,
        )
        heapq.heappush(
            frontier,
            (
                candidate.weight,
                candidate.tagger_rank,
                candidate.verbalizer_rank,
                activated,
                candidate,
                verbalizer_stream,
            ),
        )
        return True

    while len(candidates) < nbest:
        next_tag = tagger_stream.peek()
        if not frontier:
            if not activate_next_tag():
                break
            continue
        if next_tag is not None and (next_tag.weight, next_tag.rank, 0) < frontier[0][:3]:
            activate_next_tag()
            continue
        _, _, _, serial, candidate, verbalizer_stream = heapq.heappop(frontier)
        if candidate.output not in seen_outputs:
            seen_outputs.add(candidate.output)
            candidates.append(candidate)
            if len(candidates) == nbest:
                break
        next_verbalized = verbalizer_stream.pop()
        if next_verbalized is not None:
            next_candidate = _NormalizationCandidate(
                candidate.tagged,
                next_verbalized.text,
                candidate.tagger_weight,
                next_verbalized.weight,
                candidate.best_verbalizer_weight,
                candidate.tagger_rank,
                next_verbalized.rank,
            )
            heapq.heappush(
                frontier,
                (
                    next_candidate.weight,
                    next_candidate.tagger_rank,
                    next_candidate.verbalizer_rank,
                    serial,
                    next_candidate,
                    verbalizer_stream,
                ),
            )
    if not candidates:
        raise RuntimeError("no normalization path for the requested input")
    return candidates


def get_lang(text: str) -> Literal["en", "zh", "ja", "ko", "de", "hy", "ar", "fr", "pt", "vi", "ru", "sv", "es", "hi"]:
    """
    Get the language of the text.

    Args:
        text: The text to get the language of.
    Returns:
        The language of the text.
    """
    if any("\uac00" <= ch <= "\ud7af" or "\u1100" <= ch <= "\u11ff" or "\u3130" <= ch <= "\u318f" for ch in text):
        return "ko"
    if any("\u3040" <= ch <= "\u30ff" for ch in text):
        return "ja"
    for lang, ranges in (
        ("hy", ((0x0530, 0x058F),)),
        ("ar", ((0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF))),
        ("hi", ((0x0900, 0x097F),)),
        ("ru", ((0x0400, 0x052F),)),
    ):
        if any(start <= ord(char) <= end for char in text for start, end in ranges):
            return lang
    contains_chinese = False
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            contains_chinese = True
    return "zh" if contains_chinese or text.isdigit() else "en"


def preprocess(text: str, traditional_to_simple: bool = False) -> str:
    """
    Preprocess the text before normalization.

    Args:
        text: The text to preprocess.
        traditional_to_simple: Whether to convert traditional Chinese to simplified Chinese.
    Returns:
        The preprocessed text.
    """
    if traditional_to_simple:
        text = FSTS["preprocess"]["traditional_to_simple"](text)
    return text.strip()


def postprocess(
    text: str,
    full_to_half: bool = False,
    remove_interjections: bool = False,
    remove_puncts: bool = False,
    tag_oov: bool = False,
    strip: bool = True,
) -> str:
    """
    Postprocess the text after normalization.

    Args:
        text: The text to postprocess.
        full_to_half: Whether to convert full-width characters to half-width.
        remove_interjections: Whether to remove interjections.
        remove_puncts: Whether to remove punctuations.
        tag_oov: Whether to tag out-of-vocabulary words.
    Returns:
        The postprocessed text.
    """
    key = processor_key(
        dict(
            full_to_half=full_to_half,
            remove_interjections=remove_interjections,
            remove_puncts=remove_puncts,
            tag_oov=tag_oov,
        )
    )
    if "1" in key:
        if _processor_path(key):
            text = FSTS["processors"][key](text)
        else:
            # Bundles predating fused graphs retain the sequential behavior.
            for enabled, name in (
                (full_to_half, "full_to_half"),
                (remove_interjections, "remove_interjections"),
                (remove_puncts, "remove_puncts"),
                (tag_oov, "tag_oov"),
            ):
                if enabled:
                    text = FSTS["postprocess"][name](text)
    return text.strip() if strip else text


def should_normalize(text: str, lang: str, operator: Literal["tn", "itn"], remove_erhua: bool = False) -> bool:
    """
    Check if the text should be normalized.

    Args:
        text: The text to check.
        lang: The language of the text.
        operator: The operator to use.
        remove_erhua: Whether to remove erhua for TN.
    Returns:
        True if the text should be normalized, False otherwise.
    """
    if operator == "tn" and lang in ("zh", "ja"):
        if bool(re.search(r"\d", text)):
            return True
        if remove_erhua and re.search(r"儿|兒", text):
            return True
        return False
    return len(text) > 0


def reorder(
    text: str,
    lang: Literal["en", "zh", "ja", "ko", "de", "hy", "ar", "fr", "pt", "vi", "ru", "sv", "es", "hi"],
    operator: Literal["tn", "itn"],
) -> str:
    """
    Reorder the text.

    Args:
        text: The text to reorder.
        lang: The language of the text.
    Returns:
        The reordered text.
    """
    return TokenParser(lang, operator).reorder(text)


def tag(
    text: str,
    lang: Literal["en", "zh", "ja", "ko", "de", "hy", "ar", "fr", "pt", "vi", "ru", "sv", "es", "hi"],
    operator: Literal["tn", "itn"],
    enable_0_to_9: bool = False,
    deterministic: bool = True,
    cased: bool = False,
) -> str:
    """
    Tag the text.

    Args:
        text: The text to tag.
        lang: The language of the text.
        operator: The operator to use.
        enable_0_to_9: Whether to enable 0-to-9 conversion for ITN.
    Returns:
        The tagged text.
    """
    name, _ = model_names(lang, operator, enable_0_to_9=enable_0_to_9, deterministic=deterministic, cased=cased)
    return FSTS[lang][operator][name](text).strip()


def verbalize(
    text: str,
    lang: Literal["en", "zh", "ja", "ko", "de", "hy", "ar", "fr", "pt", "vi", "ru", "sv", "es", "hi"],
    operator: Literal["tn", "itn"],
    remove_erhua: bool = False,
    enable_0_to_9: bool = False,
    deterministic: bool = True,
    cased: bool = False,
) -> str:
    """
    Verbalize the text.

    Args:
        text: The text to verbalize.
        lang: The language of the text.
        operator: The operator to use.
        remove_erhua: Whether to remove erhua for TN.
    Returns:
        The verbalized text.
    """
    _, name = model_names(lang, operator, enable_0_to_9, remove_erhua, deterministic, cased)
    output = FSTS[lang][operator][name](text)
    return output if lang == "ko" else output.strip()


def normalize(text: str, config: Optional[NormalizerConfig] = None, nbest: int = 1, **kwargs):
    """
    Normalize the text.

    Args:
        text: The text to normalize.
        config: Optional normalization config object.
    Returns:
        The normalized text.
    """
    _validate_nbest(nbest)
    config = replace(config or NormalizerConfig(), **kwargs)

    if config.fix_contractions and "'" in text:
        text = contractions.fix(text)
    prepared = text.strip()
    lang = config.lang
    if lang == "auto":
        lang = get_lang(prepared)
    if nbest == 1:
        output = preprocess(prepared, config.traditional_to_simple)
        if should_normalize(output, lang, config.operator, config.remove_erhua):
            output = tag(output, lang, config.operator, config.enable_0_to_9, config.deterministic, config.cased)
            output = reorder(output, lang, config.operator)
            output = verbalize(
                output,
                lang,
                config.operator,
                config.remove_erhua,
                config.enable_0_to_9,
                config.deterministic,
                config.cased,
            )
        return postprocess(
            output,
            config.full_to_half,
            config.remove_interjections,
            config.remove_puncts,
            config.tag_oov,
            strip=lang != "ko",
        )
    if should_normalize(prepared, lang, config.operator, config.remove_erhua):
        tagger, verbalizer = _graphs(config, lang)
        outputs = [
            candidate.output
            for candidate in _normalization_candidates(prepared, lang, config.operator, tagger, verbalizer, nbest)
        ]
    else:
        output = preprocess(prepared, config.traditional_to_simple)
        output = postprocess(
            output,
            config.full_to_half,
            config.remove_interjections,
            config.remove_puncts,
            config.tag_oov,
            strip=lang != "ko",
        )
        outputs = [output]
    return outputs[0] if nbest == 1 else outputs


def normalize_candidates(text: str, config: Optional[NormalizerConfig] = None, nbest: int = 1, **kwargs):
    """Return distinct outputs together with their WFST ranking costs.

    Costs are tropical weights: lower values rank first. They are not
    probabilities or calibrated confidence scores.
    """

    _validate_nbest(nbest)
    config = replace(config or NormalizerConfig(), **kwargs)
    if config.fix_contractions and "'" in text:
        text = contractions.fix(text)
    prepared = text.strip()
    lang = config.lang
    if lang == "auto":
        lang = get_lang(prepared)
    if not should_normalize(prepared, lang, config.operator, config.remove_erhua):
        output = preprocess(prepared, config.traditional_to_simple)
        output = postprocess(
            output,
            config.full_to_half,
            config.remove_interjections,
            config.remove_puncts,
            config.tag_oov,
            strip=lang != "ko",
        )
        return [NormalizationCandidate(output, 0.0, 0.0, 0.0, 0, 0)]

    tagger, verbalizer = _graphs(config, lang)
    candidates = _normalization_candidates(prepared, lang, config.operator, tagger, verbalizer, nbest)
    return [
        NormalizationCandidate(
            text=candidate.output,
            cost=candidate.weight,
            tagger_cost=candidate.tagger_weight,
            verbalizer_cost=candidate.verbalizer_weight,
            tagger_rank=candidate.tagger_rank,
            verbalizer_rank=candidate.verbalizer_rank,
        )
        for candidate in candidates
    ]


def normalize_with_mapping(
    text: str, config: Optional[NormalizerConfig] = None, nbest: int = 1, include_identity: bool = False, **kwargs
):
    _validate_nbest(nbest)
    config = replace(config or NormalizerConfig(), **kwargs)
    if config.fix_contractions:
        raise ValueError("normalize_with_mapping is incompatible with fix_contractions=True")

    prepared = text.strip()
    leading_offset = len(text) - len(text.lstrip())
    lang = config.lang
    if lang == "auto":
        lang = get_lang(prepared)
    if not should_normalize(prepared, lang, config.operator, config.remove_erhua):
        output = normalize(text, config=config)
        mappings = ()
        if include_identity and prepared:
            mappings = (
                NormalizationMapping(
                    "equal" if prepared == output else "replace",
                    "raw",
                    leading_offset,
                    leading_offset + len(prepared),
                    0,
                    len(output),
                    prepared,
                    output,
                ),
            )
        result = NormalizationResult(text, output, mappings)
        return result if nbest == 1 else [result]

    tagger, verbalizer = _graphs(config, lang)
    candidates = _normalization_candidates(prepared, lang, config.operator, tagger, verbalizer, nbest)
    results = []
    for candidate in candidates:
        parser = TokenParser(lang, config.operator)
        reordered, token_spans = parser.reorder_with_spans(candidate.tagged)
        output, output_spans = transduce_with_spans(
            reordered,
            verbalizer,
            token_spans,
            output_text=candidate.output,
        )
        input_spans = trace_input_spans(
            prepared,
            candidate.tagged,
            tagger,
            ((token.start, token.end) for token in parser.tokens),
        )
        mappings = []
        for token, (input_start, input_end), (output_start, output_end) in zip(
            parser.tokens, input_spans, output_spans
        ):
            source = prepared[input_start:input_end]
            spoken = output[output_start:output_end]
            kind = "equal" if source == spoken else ("delete" if not spoken else "replace")
            if include_identity or kind != "equal":
                mappings.append(
                    NormalizationMapping(
                        kind,
                        token.name,
                        input_start + leading_offset,
                        input_end + leading_offset,
                        output_start,
                        output_end,
                        source,
                        spoken,
                    )
                )
        results.append(NormalizationResult(text, output, tuple(mappings)))
    return results[0] if nbest == 1 else results

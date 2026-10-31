<div align="center">

# WeTextProcessing Runtime

**Multilingual text normalization for speech applications, without a Pynini runtime dependency.**

[Quick start](#quick-start) · [Languages](#supported-languages) · [Python API](#python-api) · [Streaming](#streaming) · [Development](#development-and-model-builds)

[![PyPI](https://img.shields.io/pypi/v/wetext)](https://pypi.org/project/wetext/)
[![License](https://img.shields.io/github/license/pengzhendong/wetext)](LICENSE)

</div>

`wetext` runs the weighted finite-state transducer (WFST) grammars from
[WeTextProcessing](https://github.com/wenet-e2e/WeTextProcessing) using
[kaldifst](https://github.com/k2-fsa/kaldifst). Published wheels bundle the compiled
models; Pynini is needed only when building models from source.

- **TN and ITN** — convert written expressions into spoken forms for speech synthesis, or spoken expressions into written forms after speech recognition.
- **Multilingual pipelines** — 19 languages with TN/ITN, plus Hindi–English and Spanish–English ITN.
- **Inspectable results** — unique n-best candidates, WFST costs, and exact input/output token spans.
- **Streaming input** — feed new text chunks and finalize each utterance with `flush()`.
- **On-demand models** — load and cache only the languages and processing options your application uses.

## Supported languages

| Language | Code | TN | ITN |
| --- | --- | --- | --- |
| Chinese | `zh` | Yes | Yes |
| English | `en` | Yes | Yes |
| Japanese | `ja` | Yes | Yes |
| Korean | `ko` | Yes | Yes |
| German | `de` | Yes | Yes |
| Armenian | `hy` | Yes | Yes |
| Arabic | `ar` | Yes | Yes |
| French | `fr` | Yes | Yes |
| Portuguese | `pt` | Yes | Yes |
| Vietnamese | `vi` | Yes | Yes |
| Russian | `ru` | Yes | Yes |
| Swedish | `sv` | Yes | Yes |
| Spanish | `es` | Yes | Yes |
| Hindi | `hi` | Yes | Yes |
| Kinyarwanda | `rw` | Yes | Yes |
| Marathi | `mr` | Yes | Yes |
| Italian | `it` | Yes | Yes |
| Hebrew | `he` | Yes | Yes |
| Hungarian | `hu` | Yes | Yes |
| Hindi–English | `hi_en` | No | Yes |
| Spanish–English | `es_en` | No | Yes |

`lang="auto"` uses script-based heuristics for Chinese, Japanese kana, Hangul,
Armenian, Arabic, Hebrew, Devanagari (Hindi), and Cyrillic (Russian). Digits alone use
Chinese; Latin text uses English. Specify a language for other Latin languages
and for ambiguous inputs, such as Japanese text containing only kanji.
Specify `lang="mr"` for Marathi; its script overlaps with Hindi. Code-mixed
ITN also requires an explicit language code.

The latest languages are available in this source checkout. Before the next
package release, follow the [model build instructions](#development-and-model-builds).

## Quick start

### Install

```bash
pip install wetext
```

### Python

```python
from wetext import Normalizer

normalizer = Normalizer(lang="zh", operator="tn")
print(normalizer.normalize("价格是12.5元"))  # 价格是十二点五元

inverse_normalizer = Normalizer(lang="en", operator="itn")
print(inverse_normalizer.normalize("twenty three dollars and fifty cents"))  # $23.50
```

### Command line

```bash
wetext --lang zh --operator tn "价格是12.5元"
wetext --lang en --operator itn "twenty three dollars and fifty cents"
wetext --lang ja --operator tn "12時"
wetext --lang ko --operator tn "오후 3시 30분"
wetext --lang ko --operator itn "오천원"
wetext --lang de --operator tn "12 Euro"
wetext --lang de --operator itn "zwölf euro"
wetext --lang hi_en --operator itn "मैं twenty three साल का हूँ"
wetext --lang es_en --operator itn "pagué doce dólares and two dollars"
```

Each command prints the normalized text. `--lang` defaults to `auto` and
`--operator` defaults to `tn`. Inspect all options with `wetext --help`.

## Python API

### Normalize text

Choose the language and direction when constructing a `Normalizer`. Individual
calls can override the same options:

```python
from wetext import Normalizer

normalizer = Normalizer(lang="zh", operator="tn", remove_erhua=True)
print(normalizer.normalize("全新版本儿，简直666"))  # 全新版本，简直六百六十六
print(normalizer.normalize("十二", operator="itn"))  # 12
```

The function API is also available as `wetext.normalize(text, lang="zh", operator="tn")`.
Input is trimmed before normalization. Korean and Kinyarwanda TN retain meaningful trailing
spaces emitted by upstream rules:

```python
from wetext import Normalizer

normalizer = Normalizer(lang="ko", operator="tn")
print(repr(normalizer.normalize("2024년")))  # '이천이십사년 '
print(normalizer.normalize("십이", operator="itn"))  # 12
```

### Rule modes and case

German, Spanish, and Swedish TN default to `deterministic=True`. Enable the
upstream alternative readings with `deterministic=False`, and use `nbest` to
retrieve candidates:

```python
from wetext import Normalizer

normalizer = Normalizer(lang="de", deterministic=False)
print(normalizer.normalize("dr."))  # doktor
print(normalizer.normalize("12 Euro", nbest=3))
```

The CLI exposes `--deterministic` / `--no-deterministic` for these modes. The
option has no effect on other pipelines. Russian TN always exposes alternative
readings and does not use this switch.

Spanish and code-mixed ITN additionally support `cased=True` (`--cased` on the CLI):

```python
from wetext import Normalizer

normalizer = Normalizer(lang="es", operator="itn", cased=True)
print(normalizer.normalize("Doce Dólares"))  # $12
```

Some upstream fixtures allow multiple readings. N-best ordering follows WFST
costs; equal-cost alternatives may differ in order across inference engines.

### Code-mixed ITN

`hi_en` and `es_en` support ITN only. Always set `operator="itn"`; TN requests
are rejected with a clear error. Both pipelines support `cased=True` / `--cased`
for capitalized input:

```python
from wetext import Normalizer

normalizer = Normalizer(lang="hi_en", operator="itn")
print(normalizer.normalize("मैं twenty three साल का हूँ"))  # मैं 23 साल का हूँ
normalizer = Normalizer(lang="es_en", operator="itn", cased=True)
print(normalizer.normalize("Doce Dólares"))  # $12
```

### Processing options

The processing options below default to `False`. The CLI uses the corresponding
hyphenated flag, for example `remove_erhua=True` becomes `--remove-erhua`.

| Python option | Behavior |
| --- | --- |
| `fix_contractions` | Expand English contractions, for example `don't` → `do not` |
| `traditional_to_simple` | Convert traditional Chinese characters to simplified Chinese |
| `full_to_half` | Convert full-width characters to half-width |
| `remove_interjections` | Apply the Chinese interjection-removal rules |
| `remove_puncts` | Remove punctuation |
| `tag_oov` | Apply the Chinese vocabulary's out-of-vocabulary tagging rules |
| `enable_0_to_9` | Enable single-digit conversion for Chinese and Japanese ITN |
| `remove_erhua` | Remove erhua suffixes for Chinese TN |

```bash
wetext --traditional-to-simple "你好，這是測試。"
wetext --remove-puncts "你好，這是測試。"
wetext --lang zh --remove-erhua "全新版本儿"
```

### N-best candidates and costs

Request up to `nbest` distinct outputs, ordered by WFST cost:

```python
from wetext import Normalizer

normalizer = Normalizer(lang="en", operator="tn")
print(normalizer.normalize("4x6", nbest=3))
# ['four by six', 'four times six', 'four x six']

candidates = normalizer.normalize_candidates("4x6", nbest=3)
print(candidates[0].text, candidates[0].cost)
```

Costs are tropical WFST weights: lower is better; they are not probabilities.
`normalize()` returns a string for `nbest=1`, or a list for `nbest>1`.
`normalize_candidates()` always returns a list with text, costs, and path ranks.

### Exact input/output mappings

```python
from wetext import Normalizer

normalizer = Normalizer(lang="zh", operator="itn")
result = normalizer.normalize_with_mapping("价格是十三点五元")
print(result.output_text)  # 价格是¥13.5
for mapping in result.mappings:
    print(mapping.token_type, mapping.input_text, "=>", mapping.output_text)
# money 十三点五元 => ¥13.5
```

Mappings trace the selected WFST path. Offsets are half-open Unicode character
positions in the original input and normalized output. Use `include_identity=True`
to include unchanged tokens, or `result.as_dict()` for a serializable representation.

The mapping API returns a single `NormalizationResult` for `nbest=1` and a list
for `nbest>1`. It cannot be combined with `fix_contractions=True`, because
contraction expansion is not represented by the WFST path.

## Streaming

Pass only the new text to each `feed()` call. The return value is the complete
current output, which may change while a trailing expression is unfinished.
Use one instance per utterance and call `flush()` when it ends:

```python
from wetext import StreamNormalizer

stream = StreamNormalizer(lang="zh", operator="itn")
print(stream.feed("今天是二零"))  # 今天是二零
print(stream.feed("二六年"))  # 今天是2026年
print(stream.flush())  # 今天是2026年

stream = StreamNormalizer(lang="zh", operator="tn")
print(stream.feed("价格是12"))  # 价格是十二
print(stream.feed(".5元"))  # 价格是十二点五元
print(stream.flush())  # 价格是十二点五元
```

Streaming requires an explicit language. Its default direction is `itn`;
`Normalizer` defaults to `tn`. Call `reset()` before reusing a flushed stream.

All languages except Chinese, English, and Japanese retain their input context
until `flush()` to preserve exact normalization.
Older model bundles without streaming prefix graphs also retain more context.
For unusually long unfinished expressions, only the tail is normalized for the
current display; `flush()` normalizes all remaining input exactly.

## Development and model builds

The runtime and grammar compiler have separate dependencies:

| Task | Requirements |
| --- | --- |
| Run a published wheel | `wetext` and its runtime dependencies; bundled FST models |
| Build models | WeTextProcessing source and a working Pynini/OpenFst environment |
| Run source tests | Generated FST models and `pytest` |

To build all models from the upstream revision used by this release workflow:

```bash
git clone https://github.com/wenet-e2e/WeTextProcessing.git /tmp/WeTextProcessing
git -C /tmp/WeTextProcessing checkout c3b4d88d11c5efef817881f7e515cbdd3a19d99b
pip install -e . /tmp/WeTextProcessing pytest build
PYTHONPATH=/tmp/WeTextProcessing python build_fsts.py
python -m pytest tests -q
python -m build
```

Pynini must be available before building. If no compatible wheel is available,
follow the [Pynini installation instructions](https://www.openfst.org/twiki/bin/view/GRM/Pynini).

Generated models live in `wetext/fsts/` and are included in distribution packages.
Rebuild a single language with `python build_fsts.py --lang ko` (with the same
upstream `PYTHONPATH`). Korean models require upstream commit `31779ac` or later,
which includes [WeTextProcessing PR #381](https://github.com/wenet-e2e/WeTextProcessing/pull/381).

The [regression fixture inventory](tests/data/README.md) covers every supported pipeline
through ordinary output and exact mapping checks. Pull requests rebuild models
and run this suite automatically.

German models and fused postprocessors were introduced with upstream revision `9432590`, which
includes [German TN/ITN (#382)](https://github.com/wenet-e2e/WeTextProcessing/pull/382)
and [character-level postprocessor composition (#383)](https://github.com/wenet-e2e/WeTextProcessing/pull/383).
The build exports all 31 nonempty postprocessor configurations, so the runtime
can load a fused rewrite instead of composing multiple whole-string rewrites.

Builds now pin upstream revision `c3b4d88`, including the cross-language
punctuation and robustness fixes in [#393](https://github.com/wenet-e2e/WeTextProcessing/pull/393)
and the pipeline additions in #394–#400.
`wetext/language_registry.json` declares available directions, whitespace contracts, and model variants.
New-language field-order schemas are exported with the FSTs and loaded as JSON;
runtime inference does not import upstream Python rules.

The release workflow accepts an `upstream_ref` to select the grammar revision and
runs regression tests before packaging. Models are loaded on first use and
cached in process; the runtime does not compile rules or write a model cache.

## License

[Apache License 2.0](LICENSE).

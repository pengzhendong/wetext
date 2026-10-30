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
- **Four languages** — Chinese, English, Japanese, and Korean through one Python API and CLI.
- **Inspectable results** — unique n-best candidates, WFST costs, and exact input/output token spans.
- **Streaming input** — feed new text chunks and finalize each utterance with `flush()`.
- **On-demand models** — load and cache only the languages and processing options your application uses.

## Supported languages

| Language | Code | TN | ITN | Example |
| --- | --- | --- | --- | --- |
| Chinese | `zh` | Yes | Yes | `12` → `十二` |
| English | `en` | Yes | Yes | `12` → `twelve` |
| Japanese | `ja` | Yes | Yes | `12` → `十二` |
| Korean | `ko` | Yes | Yes | `12` → `십이` |

`lang="auto"` detects Hangul, Japanese kana, and Chinese characters. Digits alone
use Chinese; Latin text uses English. Specify a language for ambiguous inputs,
including Japanese text containing only kanji and numbers.

Korean support is available in this source checkout. Before the next package
release, follow the [model build instructions](#development-and-model-builds).

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
Input is trimmed before normalization. Korean TN retains meaningful trailing
spaces emitted by upstream rules:

```python
from wetext import Normalizer

normalizer = Normalizer(lang="ko", operator="tn")
print(repr(normalizer.normalize("2024년")))  # '이천이십사년 '
print(normalizer.normalize("십이", operator="itn"))  # 12
```

### Processing options

All Boolean options default to `False`. The CLI uses the corresponding
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

Korean retains its input context until `flush()` to preserve exact normalization.
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
git -C /tmp/WeTextProcessing checkout 31779ac
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

The [regression fixture inventory](tests/data/README.md) covers all four languages
through ordinary output and exact mapping checks. Pull requests rebuild models
and run this suite automatically.

The release workflow accepts an `upstream_ref` to select the grammar revision and
runs regression tests before packaging. Models are loaded on first use and
cached in process; the runtime does not compile rules or write a model cache.

## License

[Apache License 2.0](LICENSE).

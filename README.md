# WeTextProcessing Runtime

[![PyPI](https://img.shields.io/pypi/v/wetext)](https://pypi.org/project/wetext/)
[![License](https://img.shields.io/github/license/pengzhendong/wetext)](LICENSE)

Python runtime for WeTextProcessing (does not depend on Pynini).

WeTextProcessing is a text processing library that provides text normalization (TN) and inverse text normalization (ITN) capabilities for Chinese, English and Japanese text. It uses Finite State Transducers (FSTs) for efficient text processing.

## Features

- Text Normalization (TN) for Chinese, English and Japanese
- Inverse Text Normalization (ITN) for Chinese, English and Japanese
- Traditional to Simplified Chinese conversion
- Full-width to Half-width character conversion
- Interjection removal
- Punctuation removal
- Out-of-vocabulary (OOV) word tagging
- Erhua removal (for Chinese)
- 0-to-9 conversion (for Chinese and Japanese ITN)

## Installation

```bash
pip install wetext
```

## Usage

### Python API

#### Text Normalization (TN)

```python
from wetext import Normalizer

# Chinese TN with erhua removal
normalizer = Normalizer(lang="zh", operator="tn", remove_erhua=True)
result = normalizer.normalize("你好 WeTextProcessing 1.0，全新版本儿，简直666")
print(result)  # 你好 WeTextProcessing 一点零，全新版本，简直六六六

# English TN
normalizer = Normalizer(lang="en", operator="tn")
result = normalizer.normalize("The price is $12.50, please pay now.")
print(result)  # The price is twelve point five dollars, please pay now.
```

#### Inverse Text Normalization (ITN)

```python
from wetext import Normalizer

# Chinese ITN
normalizer = Normalizer(lang="zh", operator="itn", enable_0_to_9=False)
result = normalizer.normalize("你好 WeTextProcessing 一点零，全新版本儿，简直六六六，九和六")
print(result)  # 你好 WeTextProcessing 1.0，全新版本儿，简直666，九和六

# English ITN
normalizer = Normalizer(lang="en", operator="itn")
result = normalizer.normalize("twenty three dollars and fifty cents")
print(result)  # $23.50
```

#### Streaming ITN

`StreamNormalizer` keeps unfinished ITN context internally. Pass only the new
text on each call; `feed()` returns the complete current output. Use one
instance per utterance and call `flush()` when the utterance ends.

```python
from wetext import StreamNormalizer

stream = StreamNormalizer(lang="zh", operator="itn")
print(stream.feed("今天是二零"))  # 今天是二零
print(stream.feed("二六年"))  # 今天是2026年
print(stream.flush())  # 今天是2026年
```

Streaming currently requires an explicit language and supports ITN. Model
bundles built before streaming prefix graphs were introduced remain compatible;
they retain more internal context until `flush()`. For an unusually long
unfinished expression, only its tail is normalized for the current display;
`flush()` always returns the exact normalization of all remaining input.

#### N-best and exact mappings

```python
# Distinct candidates in official WFST weight order
normalizer = Normalizer(lang="en", operator="tn")
print(normalizer.normalize("4x6", nbest=3))
# ["four by six", "four times six", "four x six"]

# Include tropical WFST costs (lower is better; costs are not probabilities)
candidates = normalizer.normalize_candidates("4x6", nbest=3)
print(candidates[0].text, candidates[0].cost)

# Exact token spans traced through the selected WFST path
normalizer = Normalizer(lang="zh", operator="itn")
result = normalizer.normalize_with_mapping("价格是十三点五元")
print(result.output_text)  # 价格是¥13.5
print(result.mappings[0].as_dict())
```

`normalize_with_mapping()` cannot be combined with `fix_contractions=True`,
because contraction expansion is not represented by the WFST path.

### Command Line Interface

```bash
# Basic usage
wetext "你好 WeTextProcessing 1.0，全新版本儿，简直666"

# With options
wetext --lang zh --operator tn --remove-erhua "你好 WeTextProcessing 1.0，全新版本儿，简直666"

# Convert traditional to simplified Chinese
wetext --traditional-to-simple "你好，這是測試。"

# Remove punctuations
wetext --remove-puncts "你好，這是測試。"
```

## API Reference

### Normalizer Class

```python
Normalizer(
    lang: Literal["auto", "en", "zh", "ja"] = "auto",
    operator: Literal["tn", "itn"] = "tn",
    traditional_to_simple: bool = False,
    full_to_half: bool = False,
    remove_interjections: bool = False,
    remove_puncts: bool = False,
    tag_oov: bool = False,
    enable_0_to_9: bool = False,
    remove_erhua: bool = False,
)
```

#### Parameters

- `lang`: The language of the text. Can be "auto", "en", "zh" or "ja". Default is "auto".
- `operator`: The operator to use. Can be "tn" (text normalization) or "itn" (inverse text normalization). Default is "tn".
- `traditional_to_simple`: Whether to convert traditional Chinese to simplified Chinese. Default is False.
- `full_to_half`: Whether to convert full-width characters to half-width characters. Default is False.
- `remove_interjections`: Whether to remove interjections. Default is False.
- `remove_puncts`: Whether to remove punctuation. Default is False.
- `tag_oov`: Whether to tag out-of-vocabulary words. Default is False.
- `enable_0_to_9`: Whether to enable 0-to-9 conversion for ITN. Default is False.
- `remove_erhua`: Whether to remove erhua for TN. Default is False.

#### Methods

- `normalize(text: str, lang: Optional[Literal["auto", "en", "zh", "ja"]] = None) -> str`: Normalize the text.

## CLI Options

- `--lang, -l`: Set the language. Choices are "auto", "en", "zh", "ja". Default is "auto".
- `--operator, -o`: Set the operator. Choices are "tn", "itn". Default is "tn".
- `--traditional-to-simple`: Convert traditional Chinese to simplified Chinese.
- `--full-to-half`: Convert full-width characters to half-width characters.
- `--remove-interjections`: Remove interjections.
- `--remove-puncts`: Remove punctuation.
- `--tag-oov`: Tag out-of-vocabulary words.
- `--enable-0-to-9`: Enable 0-to-9 conversion.
- `--remove-erhua`: Remove erhua.

## License

[Apache License 2.0](LICENSE)

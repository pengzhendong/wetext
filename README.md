# WeTextProcessing Runtime

[![PyPI](https://img.shields.io/pypi/v/wetext)](https://pypi.org/project/wetext/)
[![License](https://img.shields.io/github/license/pengzhendong/wetext)](LICENSE)

Python runtime for WeTextProcessing (does not depend on Pynini).

WeTextProcessing is a text processing library that provides text normalization (TN) and inverse text normalization (ITN) capabilities for Chinese and English text. It uses Finite State Transducers (FSTs) for efficient text processing.

## Features

- Text Normalization (TN) for Chinese and English
- Inverse Text Normalization (ITN) for Chinese
- Traditional to Simplified Chinese conversion
- Full-width to Half-width character conversion
- Interjection removal
- Punctuation removal
- Out-of-vocabulary (OOV) word tagging
- Erhua removal (for Chinese)
- 0-to-9 conversion (for Chinese ITN)

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
result = normalizer.normalize("Today is August 8, 2024.")
print(result)  # Today is the eighth of august , twenty twenty four.
```

#### Inverse Text Normalization (ITN)

```python
from wetext import Normalizer

# Chinese ITN
normalizer = Normalizer(lang="zh", operator="itn", enable_0_to_9=False)
result = normalizer.normalize("你好 WeTextProcessing 一点零，全新版本儿，简直六六六，九和六")
print(result)  # 你好 WeTextProcessing 1.0，全新版本儿，简直666，九和六
```

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
    lang: Literal["auto", "en", "zh"] = "auto",
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

- `lang`: The language of the text. Can be "auto", "en", or "zh". Default is "auto".
- `operator`: The operator to use. Can be "tn" (text normalization) or "itn" (inverse text normalization). Default is "tn".
- `traditional_to_simple`: Whether to convert traditional Chinese to simplified Chinese. Default is False.
- `full_to_half`: Whether to convert full-width characters to half-width characters. Default is False.
- `remove_interjections`: Whether to remove interjections. Default is False.
- `remove_puncts`: Whether to remove punctuation. Default is False.
- `tag_oov`: Whether to tag out-of-vocabulary words. Default is False.
- `enable_0_to_9`: Whether to enable 0-to-9 conversion for ITN. Default is False.
- `remove_erhua`: Whether to remove erhua for TN. Default is False.

#### Methods

- `normalize(text: str, lang: Optional[Literal["auto", "en", "zh"]] = None) -> str`: Normalize the text.

## CLI Options

- `--lang, -l`: Set the language. Choices are "auto", "en", "zh". Default is "auto".
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

# wetext

Python runtime for WeTextProcessing (does not depend on Pynini).

## Usage

```bash
$ pip install wetext
$ python
```

### TN (Text Normalization)

```python
>>> from wetext import Normalizer
>>> normalizer = Normalizer(lang="zh", operator="tn", remove_erhua=True)
>>> normalizer.normalize("你好 WeTextProcessing 1.0，全新版本儿，简直666")
你好 WeTextProcessing 一点零，全新版本，简直六六六
```

### ITN (Inverse Text Normalization)

```python
>>> from wetext import Normalizer
>>> normalizer = Normalizer(lang="zh", operator="itn", enable_0_to_9=False)
>>> normalizer.normalize("你好 WeTextProcessing 一点零，全新版本儿，简直六六六，九和六")
你好 WeTextProcessing 1.0，全新版本儿，简直666，九和六
```

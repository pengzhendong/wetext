# wetext

Python runtime for WeTextProcessing (does not depend on Pynini).

## Usage

``` bash
$ pip install wetext
$ python
```

``` python
>>> from wetext import Normalizer
>>> normalizer = Normalizer(lang="zh", operator="tn", remove_erhua=True)
>>> normalizer.normalize("你好 WeTextProcessing 1.0，全新版本儿，全新体验儿，简直666")
你好 WeTextProcessing 一点零，全新版本，全新体验，简直六六六
```

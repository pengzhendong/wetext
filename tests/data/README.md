# Upstream regression fixtures

Fixtures are copied byte-for-byte from
[wenet-e2e/WeTextProcessing at 31779ac](https://github.com/wenet-e2e/WeTextProcessing/tree/31779ac)
(Apache-2.0). Korean TN fixtures originate from NVIDIA NeMo Text Processing
(Copyright NVIDIA CORPORATION, Apache-2.0); see [ko/README.md](ko/README.md).

`suites.json` records the fixture inventory, runtime options, and expected case
count for each suite. `test_regression.py` checks every case through both
`normalize()` and `normalize_with_mapping(include_identity=True)`, including
input/output offsets and text slices. It uses only the runtime and bundled FSTs;
Pynini and network access are not needed to execute the tests.

| Language | TN cases | ITN cases | Total configured cases |
| --- | ---: | ---: | ---: |
| Chinese (`zh`) | 95 | 288 | 383 |
| English (`en`) | 11 | 487 | 498 |
| Japanese (`ja`) | 141 | 232 | 373 |
| Korean (`ko`) | 395 | 209 | 604 |
| Total | 642 | 1216 | 1858 |

Inventories and options follow the upstream **full normalizer** test suites for
configurations exposed by this runtime. Chinese and Japanese ITN cover both
`enable_0_to_9=True` and `False`; shared cases run under both configurations and
are counted twice. Chinese TN enables upstream's default preprocessing options
and OOV tagging; Japanese TN enables `full_to_half`. Chinese ITN enables upstream's
default interjection removal.

Upstream tests for isolated rules are not full-pipeline expectations and are not
included here. In particular, English TN has 11 sentence-level fixtures; its
isolated-rule fixtures are a separate upstream suite. Upstream configurations
with `enable_standalone_number=False` are not exposed by this runtime and are
also outside this inventory.

Chinese, English, and Japanese fixtures use `source => expected`; whitespace is
trimmed on each side, matching upstream's `parse_test_case`. Korean fixtures use
`source~expected`, with spaces preserved exactly, including date output suffixes.

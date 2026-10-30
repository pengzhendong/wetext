# Upstream regression fixtures

Fixtures are copied byte-for-byte from
[wenet-e2e/WeTextProcessing at 9432590](https://github.com/wenet-e2e/WeTextProcessing/tree/943259052c15bd6999f5c46d931241d5e9b4df86)
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
| German (`de`) | 265 | 288 | 553 |
| Total | 907 | 1504 | 2411 |

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

German fixtures are from PR #382 and originate from NVIDIA NeMo Text Processing
(Copyright NVIDIA CORPORATION & AFFILIATES, Apache-2.0). All 25 files are kept
unchanged. German TN's `spoken~written` pairs are read in reverse; ITN pairs
are already `spoken~written`. `test_german.py` separately checks the 19 ordinal
candidate cases, all 31 multi-candidate groups (100 expected outputs), and the
265 ordinary TN cases under nondeterministic rules. These candidate checks are
in addition to the 2411 cases in the table.

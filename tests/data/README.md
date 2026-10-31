# Upstream regression fixtures

Fixtures are copied byte-for-byte from
[wenet-e2e/WeTextProcessing at 590ee51](https://github.com/wenet-e2e/WeTextProcessing/tree/590ee51e8a8eb583bd3422ebd6566dd7124a0bf7)
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
| Armenian (`hy`) | 134 | 160 | 294 |
| Arabic (`ar`) | 124 | 126 | 250 |
| French (`fr`) | 117 | 307 | 424 |
| Portuguese (`pt`) | 359 | 281 | 640 |
| Vietnamese (`vi`) | 472 | 453 | 925 |
| Russian (`ru`) | 169 | 226 | 395 |
| Swedish (`sv`) | 253 | 135 | 388 |
| Spanish (`es`) | 537 | 659 | 1196 |
| Hindi (`hi`) | 784 | 352 | 1136 |
| Total | 3856 | 4203 | 8059 |

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
in addition to the configured cases in the table.

## Additional language fixture contracts

All 302 fixture files are preserved byte-for-byte. Parsing and acceptance follow
the corresponding upstream full-normalizer tests:

- Armenian, French, Vietnamese, Swedish and Hindi use written-first TN pairs;
  ITN uses spoken-first pairs. Hindi TN expected output is stripped as upstream
  specifies. Arabic TN fraction/measure files and Russian TN are spoken-first.
- Portuguese TN has three lines with alternative readings, and Spanish TN has
  seven; any listed output is accepted. Source files are not rewritten.
- Russian TN expectations are checked among the top 100 candidates. The 57
  Russian ITN `ordinal_hard` lines also use the upstream candidate contract.
  Mapping checks select and trace an accepted candidate with its original rank.
- Spanish ITN runs 278 ordinary cases in both modes and 103 cased cases in
  `cased=True` mode. These repeated configurations are included in the table.
- Audio groups: Swedish 3 groups / 11 outputs; Spanish 29 groups / 133 outputs
  (27 distinct inputs); Russian 23 groups / 28 outputs (21 distinct inputs). `test_upstream_candidates.py` also covers the 253 Swedish and
  537 Spanish single cases in nondeterministic mode, with the same upstream
  maximum candidate limits (1000 and 500 respectively).
- Two misspelled Russian audio expectations are corrected explicitly in the
  test adapter, matching upstream's documented handling. Their original bytes
  remain in the fixture, and the misspellings must never appear in outputs.

Most added fixtures originate from NVIDIA NeMo Text Processing (Copyright
NVIDIA CORPORATION & AFFILIATES, Apache-2.0). See upstream PRs #384–#392 for
per-language scope and known grammar choices. Isolated rule tests outside the
full-normalizer inventories are not included.

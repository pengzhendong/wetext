# Upstream regression fixtures

Fixtures are copied byte-for-byte from
[wenet-e2e/WeTextProcessing at c3b4d88](https://github.com/wenet-e2e/WeTextProcessing/tree/c3b4d88d11c5efef817881f7e515cbdd3a19d99b)
(Apache-2.0). Korean TN fixtures originate from NVIDIA NeMo Text Processing
(Copyright NVIDIA CORPORATION, Apache-2.0); see [ko/README.md](ko/README.md).

`suites.json` records the fixture inventory, runtime options, and expected case
count for each suite. `test_regression.py` checks every case through both
`normalize()` and `normalize_with_mapping(include_identity=True)`, including
input/output offsets and text slices. It uses only the runtime and bundled FSTs;
Pynini and network access are not needed to execute the tests.

| Language code | Original TN cases | Original ITN cases | Total configured cases |
| --- | ---: | ---: | ---: |
| `zh` | 95 | 288 | 383 |
| `en` | 11 | 487 | 498 |
| `ja` | 141 | 232 | 373 |
| `ko` | 395 | 209 | 604 |
| `de` | 265 | 288 | 553 |
| `hy` | 134 | 160 | 294 |
| `ar` | 124 | 126 | 250 |
| `fr` | 117 | 307 | 424 |
| `pt` | 359 | 281 | 640 |
| `vi` | 472 | 453 | 925 |
| `ru` | 169 | 226 | 395 |
| `sv` | 253 | 135 | 388 |
| `es` | 537 | 659 | 1196 |
| `hi` | 784 | 352 | 1136 |
| `rw` | 100 | 0 | 100 |
| `mr` | 0 | 131 | 131 |
| `it` | 52 | 0 | 52 |
| `he` | 0 | 337 | 337 |
| `hu` | 205 | 0 | 205 |
| `hi_en` | 0 | 902 | 902 |
| `es_en` | 0 | 1725 | 1725 |
| Total | 4213 | 7298 | 11511 |

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

All 373 fixture files are preserved byte-for-byte. Parsing and acceptance follow
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

## New directions and code-mixed fixtures (#394–#400)

The table counts only original fixture directions. Reversed fixture groups are
checked separately in `test_reversed_pipelines.py`:

| Direction | Grouped inputs | Accepted reverse groups | Documented exclusions |
| --- | ---: | ---: | ---: |
| Kinyarwanda ITN | 98 | 93 | 5 |
| Marathi TN | 128 | 121 | 7 |
| Italian ITN | 55 | 50 | 5 |
| Hebrew TN | 296 | 271 | 25 |
| Hungarian ITN | 178 | 166 | 12 |

`reverse_contracts.json` preserves upstream's exact exclusion mappings and source
comments. Tests execute the excluded inputs too: Kinyarwanda asserts canonical
fallbacks; Italian/Hungarian ensure the documented original style is not
invented; Marathi/Hebrew verify mapped canonical output, with additional fixed
semantic cases. Exclusions reflect unrecoverable formatting or conflicting
fixture readings, and are not silent pytest skips.

All 486 original `hi_en` and 976 original `es_en` lines are preserved. Ordinary
fixtures also run under `cased=True`, so the configured counts include 416 and
749 repeated cases respectively. Neither mixed pipeline has a TN direction.

`test_cross_language_fixes.py` additionally covers upstream #393: attached and
explicitly spaced punctuation, no-path inputs across every available direction,
invalid numeric dates, grouped Korean numbers, Hindi percentages, and new
language semantics. Kinyarwanda whole-hour trailing spaces remain significant.

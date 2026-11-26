# Verification record

*Plain-language summary: when and how the author approved this release.*

- **Release:** v1.0.0
- **Approved by:** Maurice Kuubata (ORCID 0009-0003-3178-5971)
- **Date:** 2026-11-20
- **Author's statement:** "I have reviewed and everything looks good. Please produce the final version and remove all the draft stamp." The author confirmed the data have been verified.
- **Decisions D1-D9 (docs/VERIFY_CHECKLIST.md Part 4):** accepted as built: bentonite stand-in SWy-1; seacoal stand-in kerogen BK-Cornell; iron oxide stand-in hematite GDS69 <10 um; calibration with one shared offset per DC2 group; silica sand 250 um and bentonite 10 um effective sizes; water path factor 1.0; noise tiers ideal/lab/plant as configured; detection rule 5% false alarms and 95% detection at the level and all higher levels; four Zenodo records.
- **Mechanical gate:** `python tools/publish_gate.py . --allow-draft-in src/ tests/ tools/ code/ docs/GLOSSARY.md` passed on 2026-11-20.

## Post-approval corrections (2026-11-26)

- **What changed:** code and wording corrections from a review on 2026-11-20, rebuilt from the raw data in final mode. No computed result changed: every library spectrum value, fitted size, trend check and detection limit is identical to the 2026-11-20 build.
- **Data files:** instrument-resolution library files now label channels to 0.01 nm (`R_1006.93`, previously truncated to `R_1006`), matching the benchmark sets; values unchanged.
- **Labels and wording:** "USGS priors" renamed "assumed sizes, no lab calibration"; GDS27 crossover stated as about 1135 nm; fitted-size grid resolution added to LIMITATIONS; unsupported "first" and "nobody has published" claims softened; JOSS paper restructured to the current required sections.
- **Code:** numpy < 2.0 compatibility, token masking in `tools/publish_github.py`, Zenodo record-file support in `tools/zenodo_deposit.py`, input checks in `code/score_submission.py`, deterministic release archives, 3 new tests (22 total, all passing).
- **Author's decisions:** the author received the list of corrections on 2026-11-20 and on 2026-11-26 asked for them to be pushed. He chose the JOSS paper's AI-use statement ("Claude (Anthropic)", no version) and funding statement ("This work received no specific funding.").
- **Mechanical gate:** passed on 2026-11-26.

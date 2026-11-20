# Verification record

*Plain-language summary: when and how the author approved this release.*

- **Release:** v1.0.0
- **Approved by:** Maurice Kuubata (ORCID 0009-0003-3178-5971)
- **Date:** 2026-11-20
- **Author's statement:** "I have reviewed and everything looks good. Please produce the final version and remove all the draft stamp." The author confirmed the data have been verified.
- **Decisions D1-D9 (docs/VERIFY_CHECKLIST.md Part 4):** accepted as built: bentonite stand-in SWy-1; seacoal stand-in kerogen BK-Cornell; iron oxide stand-in hematite GDS69 <10 um; calibration with one shared offset per DC2 group; silica sand 250 um and bentonite 10 um effective sizes; water path factor 1.0; noise tiers ideal/lab/plant as configured; detection rule 5% false alarms and 95% detection at the level and all higher levels; four Zenodo records.
- **Mechanical gate:** `python tools/publish_gate.py . --allow-draft-in src/ tests/ tools/ code/ docs/GLOSSARY.md` passed on 2026-11-20.

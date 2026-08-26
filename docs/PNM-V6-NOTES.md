# PNM V6 build notes

V6 uses the supplied 2026 East Java headline corpora as a discovery-pattern source. The corpora contain repeated operational signals including tangkap lepas, pungli, suap/setoran/upeti, backing/pembiaran, Propam escalation, journalist intimidation, SIM/Samsat issues, illegal mining/gambling/liquor/cigarette/fuel activities, sexual/relationship/violence-related allegations, and public-order/security incidents such as demonstrations, clashes, and attacks on police posts.

These signals are grouped into discovery families instead of being treated as factual labels. The collector uses the families to broaden discovery and improve classification recall; the Case Engine uses them as supporting evidence for incident clustering and severity.

Source corpora:
- docs/discovery_2026_jatim_source_a.md
- docs/discovery_2026_jatim_source_b.md

The 2025 corpus can be incorporated in a later vocabulary expansion after the V6 baseline has been evaluated against live runs.

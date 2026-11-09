# Changelog

All notable changes to this project. Format: Keep a Changelog 1.1.
Versions follow Semantic Versioning; no release is tagged yet.

## [Unreleased]

### Changed
- 2026-11-08: Adopted the portfolio standard v2. README opens with the
  question, headline, field, job family and verdict (Functional). The
  old README narrative (problem, purpose, arms, error character) moved
  into REPORT.md. AUDIT.md became REPORT.md, the study report; its
  grade moved out of the public repo (grades are internal) and its
  itemized deductions became "Threats to validity" without points. The
  lock is tagged proposal-v1 on 0774bfd, and a test fails if
  PREREGISTRATION.md changes by one byte. CI checks that RESULTS.md
  and results/metrics.json regenerate unchanged from the raw records.
  CodeQL and Dependabot added; main protected.
- 2026-11-08: REPORT.md corrects two small figures from the audit: the
  H1 difference is 0.3385 as generated (0.3384 was the difference of
  rounded values), and the 7.05 s failed-call median is the 27 HTTP
  429 failures (7.08 s over all 29 failed documents).

### Fixed
- 2026-11-08: The credential-helper import in src/arm_b.py is guarded
  so tests import on a clean CI runner (DECISIONS.md D3).

### Added
- 2026-11-08: Results: both arms on all 50 FUNSD test documents,
  verdicts generated from the frozen pass lines (H1 and H2 confirmed,
  H3 inconclusive), audit.
- 2026-11-08: Study harness: Tesseract arm, Gemini vision arm, shared
  scorer, results generator, tests, CI.
- 2026-11-08: Pre-registration (0774bfd), before any code or run.

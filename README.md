# TLC-Harmony-Codex-Audit
tlc_audit_core.py
# T.L.C. Harmony Codex: Empirical Verification Repository

This repository contains the code and methodology used to identify a 180Hz TLC signature within the LIGO O4b dataset.

## Discovery Metrics
- **GPS Timestamp:** 1420879098.9972
- **Verified SNR:** 606.84
- **L1-H1 Latency:** 5.92 ms
- **Statistical Significance:** p < 10^-5 (100,000 Trial Audit)

## Reproduction Instructions
The scripts provided utilize the standard `h5py` and `scipy` libraries to perform a matched-filter search on the raw GWOSC 16kHz strain data. The background audit is conducted via randomized time-slides to establish the local noise floor of the O4b run.

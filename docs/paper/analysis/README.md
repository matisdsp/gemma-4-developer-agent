# Analyses behind gaps.md

All scripts run offline on the Mac; competition data stays in the gitignored `data/` and is never
copied here. Outputs that contain per-task, data-derived content (`graph_localization/out/`,
`graph_localization/snap/`) are gitignored; only aggregate numbers are quoted in `gaps.md`.

| Measurement | Script | Notes |
|---|---|---|
| M1 decode latency vs batch | `latency/decode_latency_vs_batch.py <mlx model id> <new tokens>` | needs `mlx-lm` (0.32.2 used); results in `latency/results_mac_m4pro.md` |
| M3 graph vs grep vs BM25 vs embeddings | `graph_localization/run_all.py` (`--force`, `--df-max X`) | extracts `*.py` from `data/snapshots` into `snap/` first (`extract_snaps.sh`); deterministic |
| M4 best score vs submissions | `leaderboard/best_score_vs_submissions.py <csv>` | public leaderboard CSV |
| M5 tests needing names absent from the issue | `spec_gap/spec_gap.py data/tasks.jsonl <out.json>` | heuristic, not hand-audited |

M2 (E4B budget use) comes from the score agent's Kaggle run, logged in `reports/ledger.jsonl`.

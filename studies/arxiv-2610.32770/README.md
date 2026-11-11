# arXiv:2610.32770 — On-Policy Self-Training (OPST)

Independent, standard-library mechanism study of OPST: the skewed-JSD self-distillation objective, pseudo-verification + consensus-gate sample selection, EMA-teacher bookkeeping and loss aggregation. A Qwen2.5-0.5B wrong-answer robustness analogue (C6) ran once on GitHub Actions and was INCONCLUSIVE. No paper-level training is run. See `status.yaml` for the current boundary and `HANDOFF.md` for continuation.

    python studies/arxiv-2610.32770/experiments/run_opst_mechanism.py
    python -m pytest -q tests/test_opst_mechanism.py

    python studies/arxiv-2610.32770/experiments/aggregate_opst_wr.py studies/arxiv-2610.32770/evidence/opst_wr_qwen0.5b_v1_cells
    python -m pytest -q tests/test_opst_wr.py

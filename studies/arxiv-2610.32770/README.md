# arXiv:2610.32770 — On-Policy Self-Training (OPST)

Independent, standard-library mechanism study of OPST: the skewed-JSD self-distillation objective, pseudo-verification + consensus-gate sample selection, EMA-teacher bookkeeping and loss aggregation. No model, benchmark or paper-level training is run. See `status.yaml` for the current boundary and `HANDOFF.md` for continuation.

    python studies/arxiv-2610.32770/experiments/run_opst_mechanism.py
    python -m pytest -q tests/test_opst_mechanism.py

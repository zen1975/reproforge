# SOMA Protocol and Asset Review

Source: arXiv 2610.26793 v1, submitted 2026-10-19. Full text: https://arxiv.org/html/2610.26793v1. License recorded: arXiv.org perpetual non-exclusive distribution license. Reviewed 2026-10-21.

At each reasoning pause, the monitor returns a probability. The controller converts it to log-odds evidence and keeps a non-negative running score. The first positive score causes a reminder and resets the score. Later evidence can trigger an intervention only after that reminder. If evidence falls back to zero, the reminder episode resets. The paper's single-run analysis evaluates possible thresholds on a reminder-enabled trajectory without executing the final intervention; this study implements the threshold readout but does not regenerate model trajectories.

Published settings recorded: Qwen3-8B and DeepSeek-R1-Distill-Llama-8B for System Two; Jev API for System One; 32,768-token generation limit; Qwen3 temperature 0.6, top-p 0.95, top-k 20; scan interval 256 thinking tokens; up to 128 extra tokens to reach a line break; monitor state window 2,048 tokens. Threshold grid: 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 4, 6, 8, 12; calibration tolerance delta 0; calibration and test sets are disjoint.

Benchmarks named in the paper: GSM8K, MATH-500, AIME 2024-2025, AMC 2023, GPQA-Diamond, SUM, and UMWP. Exact immutable model revisions are not specified and remain unknown.

No author code, PDF, figures, weights, or benchmark data were copied. Jev is a hosted API; no call was made. Dataset access and licenses must be reviewed before future use. The synthetic fixture is original ReproForge work and cannot establish model accuracy, token savings, abstention, latency, or empirical transfer.

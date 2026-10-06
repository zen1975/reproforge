# Evidence-Aware Stopping Gate

Experimental deterministic harness primitive extracted from arXiv:2610.06191.

The gate receives per-observation usefulness judgments and forces answer mode after a configurable run of consecutive `USELESS` judgments. The initial paper-derived default is five.

The current ReproForge implementation is deliberately small and transport-neutral. It does not perform the usefulness judgment itself; judgment production and stopping enforcement remain separate components.

Current evidence verifies the deterministic gate mechanism on frozen synthetic scenarios. It does not yet reproduce the paper's trajectory statistics or time-matched contrast.

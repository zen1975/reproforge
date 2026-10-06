# Decision-Preserving Context Compressor

Experimental span-level context-selection capability derived independently from the published FOCUS algorithm (arXiv:2609.37590).

The deterministic core deliberately does **not** generate plan rollouts. It accepts dependency sets produced by a draft-model adapter, estimates each historical span's utility by citation frequency, retains spans above threshold, then unions any spans rescued by defensive verification.

This separation keeps the reusable policy testable without pretending that synthetic dependency sets reproduce the paper's LLM behavior.

Current evidence verifies:
- citation-frequency utility;
- threshold retention at the published default `N=3`, `tau=0.3`;
- whole-span integrity;
- defensive rescue;
- preservation of the paper-described set-valued-goal failure mode as negative evidence.

Paper benchmark performance is not reproduced.

# Gemma 3 Reproduction Gate

The paper evaluates Gemma 3 1B and 4B variants. ReproForge has a ready-to-run
Gemma 3 1B protocol baseline workflow, but it intentionally does not run
without authorized model access.

## Blocking dependency

`google/gemma-3-1b-it` is gated on Hugging Face. The operator must:

1. sign in to Hugging Face;
2. accept Google's Gemma usage license for the model;
3. create a Hugging Face access token with model read access;
4. add it to this repository as the Actions secret `HF_TOKEN`;
5. manually dispatch **Gemma 3 1B protocol baseline**.

The workflow fails closed when `HF_TOKEN` is absent. Qwen or MiniLM results
must never be relabeled as Gemma reproduction evidence.

## Ready artifacts

- `generate_protocol_equivalent_mcp.py`: independent structural reproduction
  of the paper's 12-server, 8/4 server-disjoint, N=2/3, correct/wrong/null,
  candidate-level classification protocol.
- `run_gemma3_protocol_baseline.py`: authenticated Gemma 3 1B baseline.
- `task-tool-gemma3-base.yml`: manual workflow.

## Evidence boundary

Even after the Gemma workflow runs, results remain protocol-equivalent rather
than paper-dataset reproduction until the authors' dataset/code becomes
actually accessible and its license is verified.

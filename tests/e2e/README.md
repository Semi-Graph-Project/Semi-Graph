# Comparison UI browser tests

The default browser suite uses a fake backend. It clicks the real Streamlit UI
but does not call Neo4j or an LLM, so it is safe to run repeatedly and in CI.

```bash
pip install -e '.[e2e]'
python -m playwright install chromium
pytest tests/test_demo_ui.py tests/test_demo_backend.py tests/e2e/test_comparison_ui.py -q
```

The live smoke is separate and opt-in. It submits the same NVIDIA question
**once to each corpus** (7690 and 7687). Each submission starts all four
configurations, including multi-call Agents, so it can incur LLM costs. Do not
rerun it automatically after a failure. It starts a separate Streamlit process
for each corpus and stops that process after the result or 120-second UI limit.

```bash
SEMIGRAPH_LIVE_UI_TEST=1 pytest tests/e2e/test_comparison_live.py -q -s
```

Live reports and failure screenshots are written under `tests/e2e/artifacts/`
(ignored by Git). The smoke checks UI completion, answers, traces and clickable
citations; it does not judge answer correctness.

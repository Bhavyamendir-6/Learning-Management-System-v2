# ADK Evaluation Suite

Automated evaluations for the LMS Agent ADK layer using `adk eval`.

## Prerequisites

- Python virtual environment with `google-adk` installed
- `GEMINI_API_KEY` set in `.env`
- `POSTGRES_URL` set in `.env` (tools hit the real DB)

> **Windows / PowerShell note:** PowerShell does not support `\` for line continuation.
> All commands below are written as **single lines** so they work on both Windows and Unix.
> If you prefer multi-line in PowerShell, use backtick `` ` `` as the continuation character.

---

## Eval Configs

| Config | Purpose | Criteria |
|--------|---------|----------|
| `eval_config.json` | Regression / CI (fast, deterministic) | `tool_trajectory_avg_score` (IN_ORDER) + `response_match_score` |
| `eval_config_routing.json` | Routing correctness only | `tool_trajectory_avg_score` (IN_ORDER) |
| `eval_config_quality.json` | Response quality (LLM judge) | `rubric_based_final_response_quality_v1` + `hallucinations_v1` + `safety_v1` |
| `eval_config_simulation.json` | User simulation multi-turn | `hallucinations_v1` + `safety_v1` + rubric quality + rubric tool use |

---

## Running Evaluations

All commands run from the **project root** (`LMS_Project_V2/`).

### Routing Tests (fast — start here)

```
adk eval . tests/eval/evalsets/routing_evalset.json --config_file_path=tests/eval/eval_config_routing.json --print_detailed_results
```

### Sub-Agent Tool Trajectory Tests

```
adk eval . tests/eval/evalsets/quiz_agent_evalset.json --config_file_path=tests/eval/eval_config.json --print_detailed_results
```

```
adk eval . tests/eval/evalsets/learning_content_evalset.json --config_file_path=tests/eval/eval_config.json --print_detailed_results
```

```
adk eval . tests/eval/evalsets/tutor_agent_evalset.json --config_file_path=tests/eval/eval_config.json --print_detailed_results
```

```
adk eval . tests/eval/evalsets/quiz_history_evalset.json --config_file_path=tests/eval/eval_config.json --print_detailed_results
```

```
adk eval . tests/eval/evalsets/community_agent_evalset.json --config_file_path=tests/eval/eval_config.json --print_detailed_results
```

### Response Quality Tests (LLM judge)

```
adk eval . tests/eval/evalsets/learning_content_evalset.json --config_file_path=tests/eval/eval_config_quality.json --print_detailed_results
```

### User Simulation Tests (dynamic multi-turn)

```
adk eval . tests/eval/evalsets/simulation/quiz_flow_simulation.json --config_file_path=tests/eval/eval_config_simulation.json --print_detailed_results
```

```
adk eval . tests/eval/evalsets/simulation/tutor_flow_simulation.json --config_file_path=tests/eval/eval_config_simulation.json --print_detailed_results
```

### Run All Static Evals (single command)

```
adk eval . tests/eval/evalsets/routing_evalset.json tests/eval/evalsets/quiz_agent_evalset.json tests/eval/evalsets/learning_content_evalset.json tests/eval/evalsets/tutor_agent_evalset.json tests/eval/evalsets/quiz_history_evalset.json tests/eval/evalsets/community_agent_evalset.json --config_file_path=tests/eval/eval_config.json --print_detailed_results
```

### Run a Single Eval Case

```
adk eval . tests/eval/evalsets/routing_evalset.json:route_to_quiz --config_file_path=tests/eval/eval_config_routing.json --print_detailed_results
```

---

## Using Make (if `make` is available)

```bash
make eval-routing      # Routing tests
make eval-tools        # All sub-agent tool trajectory tests
make eval-quality      # Response quality (LLM judge)
make eval-simulation   # User simulation tests
make eval              # Routing + tool trajectory (CI default)
```

> On Windows, install `make` via [Chocolatey](https://chocolatey.org/): `choco install make`
> Or use the single-line commands above directly.

---

## PowerShell Multi-Line Alternative

If you prefer readable multi-line commands in PowerShell, use backtick `` ` `` for continuation:

```powershell
adk eval . tests/eval/evalsets/routing_evalset.json `
  --config_file_path=tests/eval/eval_config_routing.json `
  --print_detailed_results
```

---

## Iterating on Failures

When a score is below threshold:

1. Read the detailed results to identify what failed
2. Fix agent instructions (prompts), tool logic, or relax evalset expectations
3. Re-run just that failing case: `adk eval . evalset.json:failing_case_id --config_file_path=...`
4. Repeat until passing
5. Expect 5–10 iterations per evalset — this is normal

### Common fixes

| Failure | Fix |
|---------|-----|
| Wrong agent routed | Update root agent prompt routing rules in `prompts.py` |
| Wrong tool called | Update sub-agent prompt or tool descriptions |
| Extra tools called | Already handled by `IN_ORDER` match type |
| Response doesn't match | Relax `response_match_score` threshold or adjust expected response text |
| Hallucination detected | Tighten agent instructions to stay grounded in document content |

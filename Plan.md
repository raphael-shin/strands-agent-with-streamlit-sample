# UI Handler Refactor Plan

> Based on `UI_HANDLERS_ANALYSIS.md` and the Strands Agent event contracts (per `https://strandsagents.com/latest/llms.txt`). Network access is currently restricted, so protocol details will be derived from existing handlers and updated once direct doc access is available.

## Phase 0 – Preparation
- Audit current `handlers/ui_handlers.py` behaviour and identify all Strands event types already in use (`reasoningText`, `current_tool_use`, `tool_result`, `data`, `result`, `force_stop`, `event`).
- Catalogue Streamlit placeholder usage so we can reattach them cleanly after the split.
- Verify existing unit tests in `tests/test_streamlit_flow.py` to understand behavioural expectations.

## Phase 1 – Utility Extraction
- Create `handlers/ui/utils.py` housing pure helper functions: `parse_model_response`, `strip_partial_thinking`, `normalize_tool_value`, `render_tool_value`.
- Replace direct imports in the handler and tests with the new module to keep a single source of truth.
- Ensure docstrings stay concise and emphasise readability over brevity (“읽기 좋은 코드”).

## Phase 2 – State Restructuring
- Introduce `handlers/ui/state.py` with dataclasses (or lightweight classes) for reasoning, tool, message, and placeholder state.
- Keep the public surface area compatible with the current `StreamlitUIState` to avoid breaking the agent.
- Move placeholder bookkeeping (including tool placeholder registry) into `handlers/ui/placeholders.py` for clarity.

## Phase 3 – Manager Modules
- Build dedicated managers:
  - `handlers/ui/reasoning.py` – reasoning-specific handlers and finalisation.
  - `handlers/ui/tools.py` – tool invocation/result rendering, spinner handling, placeholder reuse.
  - `handlers/ui/messages.py` – streaming data, final message synthesis, chain-of-thought rendering.
- Each manager exposes `can_handle(event: Dict[str, Any])`, `handle(event)`, and `finalize()` to conform to the coordinator contract.
- Favour small, well-named methods so the flow reads top-to-bottom without jumps.

## Phase 4 – Coordinator Refactor
- Slim down `handlers/ui_handlers.py` so `StreamlitUIHandler` becomes an orchestrator:
  - Instantiate the managers with shared state in `__init__`.
  - Route events to the first manager that can handle them.
  - Delegate `finalize_response()` to each manager before composing the final payload.
- Maintain existing priority (`priority = 10`) and approval logic to stay aligned with Strands Agent requirements.

## Phase 5 – Alignment & Cleanup
- Double-check that event keys and status updates match the (currently cached) Strands schema; leave TODO markers if any behaviour needs confirmation once the official doc is accessible.
- Update imports across the project (including tests) to reference the new package layout.
- Remove obsolete attributes (e.g., `_ui_key` hacks) and prefer explicit state containers for readability.

## Phase 6 – Verification
- Extend `tests/test_streamlit_flow.py` (or add new suites) to cover each manager in isolation.
- Run the full test suite to confirm streaming and finalisation flows are intact.
- Perform a manual Streamlit smoke check if possible to validate spinner → completion transitions.

## Phase 7 – Documentation
- Refresh developer docs (if any) to reference the modular structure.
- Summarise the refactor in the project changelog or README as needed.

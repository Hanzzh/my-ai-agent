# Multi-Turn Conversation Implementation Plan

Date: 2026-03-08

## Overview

This plan breaks down the implementation of multi-turn conversation support into discrete, testable steps.

## Dependencies

None - this is a new feature with no blocking dependencies.

## Implementation Steps

### Step 1: Add message_history to ReActAgent

**Files to modify:**
- `src/agent/react.py`
- `src/agent/factory.py` (add `clear_history` to abstract base)

**Changes:**
1. Add `self.message_history: list = []` in `ReActAgent.__init__`
2. Add `_build_messages(question: str) -> list` method
3. Modify `run()` to use `_build_messages()` and update history after final answer
4. Add `clear_history()` method
5. Update `Agent` abstract class to include optional `clear_history` method

**Tests:**
- `test_react_agent_history_initially_empty`
- `test_react_agent_history_updated_after_answer`
- `test_react_agent_clear_history`
- `test_react_agent_multi_turn_context`

**Verification:**
```bash
pytest tests/agent/test_react.py -v
```

---

### Step 2: Create Session class

**Files to create:**
- `src/session/__init__.py`
- `src/session/session.py`

**Changes:**
1. Create `src/session/` directory
2. Create `Session` class with:
   - `@classmethod async def create(cls, config_path, verbose) -> Session`
   - `async def ask(self, question: str) -> str`
   - `async def close(self) -> None`
   - `def clear_history(self) -> None`
   - `@property def history_length(self) -> int`
3. Session holds references to: `llm_provider`, `mcp_loader`, `agent`, `config`
4. Implement async context manager support (`__aenter__`, `__aexit__`)

**Tests:**
- `test_session_create`
- `test_session_ask_single`
- `test_session_ask_multi_turn`
- `test_session_close`
- `test_session_clear_history`
- `test_session_history_length`
- `test_session_context_manager`

**Verification:**
```bash
pytest tests/session/ -v
```

---

### Step 3: Update CLI for interactive chat

**Files to modify:**
- `main.py`

**Changes:**
1. Add `interactive_session(debug: bool)` async function
2. Modify `main_async()` to:
   - If no question provided: start interactive session
   - If question provided: use existing single-shot flow (unchanged)
3. Add slash command handling:
   - `/quit` - exit session
   - `/clear` - clear history
4. Update `print_help()` to document interactive mode

**Tests:**
- `test_interactive_mode_start`
- `test_interactive_quit_command`
- `test_interactive_clear_command`

**Verification:**
```bash
pytest tests/test_debug_mode.py -v  # existing CLI tests
# Manual: python main.py (enter interactive mode)
```

---

### Step 4: Add integration tests

**Files to modify:**
- `tests/test_integration.py`

**Changes:**
1. Add `test_multi_turn_conversation` integration test
2. Add `test_session_mcp_persistence` integration test
3. Mark with `@pytest.mark.integration`

**Verification:**
```bash
pytest tests/test_integration.py -v -m integration
```

---

## File Summary

| File | Action | Lines Changed (est.) |
|------|--------|---------------------|
| `src/agent/react.py` | Modify | +40 |
| `src/agent/factory.py` | Modify | +3 |
| `src/session/__init__.py` | Create | +2 |
| `src/session/session.py` | Create | +120 |
| `main.py` | Modify | +50 |
| `tests/agent/test_react.py` | Modify | +60 |
| `tests/session/__init__.py` | Create | +0 |
| `tests/session/test_session.py` | Create | +150 |
| `tests/test_integration.py` | Modify | +40 |

**Total estimated lines:** ~465

## Rollback Plan

1. Each step is independent and can be reverted individually
2. Step 1 changes are backward compatible - existing tests pass
3. Steps 2-3 add new code without modifying existing behavior
4. If issues found, can disable interactive mode and use single-shot mode

## Success Criteria

- [ ] All existing tests pass
- [ ] New session tests pass
- [ ] Interactive mode works with `/quit` and `/clear`
- [ ] Multi-turn conversation maintains context
- [ ] Single-shot mode still works unchanged
- [ ] MCP connections persist across turns in a session
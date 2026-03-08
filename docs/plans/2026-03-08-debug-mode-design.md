# Debug Mode Design

**Date:** 2026-03-08
**Author:** Claude Code
**Status:** Approved

## Overview

Add a `--debug` command-line flag to control output verbosity. When enabled, show all logs and intermediate steps. When disabled, show only the final result.

## Problem Statement

Currently, the AI agent outputs extensive logging and iteration information during execution, which can be overwhelming for end users who only care about the final answer. Users should have the option to run the agent in a "silent mode" that only displays the final result.

## Requirements

### Functional Requirements

1. **Without `--debug` flag**: Show only the final result box
2. **With `--debug` flag**: Show all current output (logs, iterations, LLM responses, actions, observations)
3. **Errors must always be visible** regardless of debug mode
4. **User-essential feedback** (prompts, cancellation messages) always shows

### Non-Functional Requirements

1. Minimal code changes
2. Follow Python logging best practices
3. Backward compatible (existing behavior preserved with `--debug`)

## Design

### CLI Argument Parsing

Add `argparse` to `main.py`:

```python
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="AI Agent - MCP-Powered Assistant")
    parser.add_argument("question", nargs="?", help="Question to process")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with verbose output")
    return parser.parse_args()
```

### Logging Configuration

Set logging level based on debug flag:

```python
debug_mode = args.debug
log_level = logging.DEBUG if debug_mode else logging.WARNING

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

This automatically suppresses all `logger.info()` calls throughout the codebase when not in debug mode, while keeping errors visible.

### Component Integration

1. **`main.py`**:
   - Remove/condition `"Processing your question...\n"` print
   - Pass `verbose=debug_mode` to `run_agent()`
   - Condition banner on debug mode

2. **`src/app.py`**:
   - Update signature: `async def run_agent(question: str, config_path: str = "config.yaml", verbose: bool = False) -> str`
   - Pass `verbose` to agent factory

3. **`src/agent/react.py`**:
   - Wire `verbose` parameter through to existing `run()` method
   - The `verbose` parameter already exists and controls iteration output

### Error Handling

The following always show regardless of debug mode:
- Error messages (logger level WARNING/ERROR)
- Exception output
- "Operation cancelled" on Ctrl+C
- Empty question error message

## Implementation Changes

### Files to Modify

| File | Changes |
|------|---------|
| `main.py` | Add argparse, conditional prints, pass verbose flag |
| `src/app.py` | Add `verbose` parameter to `run_agent()` |
| `src/agent/factory.py` | Pass `verbose` to agent constructor |
| `src/agent/react.py` | Wire `verbose` through `__init__` to `run()` |

### Example Output

**Without `--debug`:**
```
============================================================
RESULT
============================================================
The current weather in Tokyo is rainy with a temperature of 10°C and humidity of 79%.
============================================================
```

**With `--debug`:**
```
2026-03-08 20:13:15,502 - __main__ - INFO - Question from command line: What's the weather in Tokyo?...
2026-03-08 20:13:15,502 - src.app - INFO - Loading configuration from config.yaml
...

=== Iteration 1 ===
LLM Response: ...
Action: get_weather
...

=== Iteration 2 ===
...
============================================================
RESULT
============================================================
The current weather in Tokyo is rainy...
============================================================
```

## Testing Strategy

### Manual Test Cases

1. **Silent mode** (no flag):
   ```bash
   python main.py "What's the capital of France?"
   # Expect: Only final result box
   ```

2. **Debug mode** (with flag):
   ```bash
   python main.py --debug "What's the capital of France?"
   # Expect: All current output
   ```

3. **Error handling** (no flag):
   ```bash
   python main.py ""
   # Expect: Error message still shows
   ```

4. **Interactive mode** (no flag):
   ```bash
   python main.py
   # Expect: No banner, just prompt
   ```

## Trade-offs

### Chosen Approach: Logging Level Control

**Advantages:**
- Clean separation using standard Python logging
- Minimal code changes
- Errors automatically still show
- Follows Python best practices

**Disadvantages:**
- Need to ensure all info logs are at INFO level (currently true)

## Alternatives Considered

1. **Explicit verbose passing**: More control but more code changes
2. **Output redirection**: Hacky and may suppress errors

## Success Criteria

- [ ] `python main.py "question"` shows only final result
- [ ] `python main.py --debug "question"` shows all output
- [ ] Errors always visible
- [ ] No regressions in existing functionality

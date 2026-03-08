# Multi-Turn Conversation Support Design

Date: 2026-03-08

## Overview

Add support for multi-turn conversations where the agent maintains context across questions. This enables both interactive CLI chat mode and programmatic session-based usage.

## Goals

- Persistent conversation history across multiple questions
- Persistent MCP server connections for session lifetime
- Interactive CLI chat mode with slash commands
- Backward compatibility with existing single-shot mode

## Non-Goals

- Persistence to disk (in-memory only for now)
- Session management API (future decision)
- Multi-user session support

## Architecture

### Component Overview

```
src/
├── session/
│   ├── __init__.py       # Export Session
│   └── session.py        # Session class
├── agent/
│   └── react.py          # Modified: add message_history
└── main.py               # Modified: interactive chat loop
```

### Session Pattern

The `Session` class owns all resources for a conversation's lifetime:

```
Session
├── llm_provider (persistent)
├── mcp_loader (persistent connections)
├── agent (persistent, holds message_history)
└── methods: ask(), close(), clear_history()
```

**Flow:**
1. `Session.create()` → loads config, initializes LLM, MCP, agent
2. `session.ask(question)` → sends question, returns answer, updates history
3. `session.close()` → shuts down MCP, releases resources

### Resource Lifecycle

| Phase | Action | Resources |
|-------|--------|-----------|
| Create | One-time init | LLM client, MCP connections, Agent instance |
| Ask | Reuse resources | Same LLM/MCP/Agent, append to history |
| Close | One-time cleanup | Close MCP connections, release references |

## Interface Design

### Session Class

```python
class Session:
    """Manages a conversation session with persistent resources and history."""

    @classmethod
    async def create(cls, config_path: str = "config.yaml", verbose: bool = False) -> "Session":
        """Factory method to create and initialize a session."""

    async def ask(self, question: str) -> str:
        """Ask a question and get a response, maintaining conversation history."""

    async def close(self) -> None:
        """Close the session and release all resources."""

    def clear_history(self) -> None:
        """Clear conversation history while keeping resources alive."""

    @property
    def history_length(self) -> int:
        """Number of message exchanges in the conversation."""
```

### Agent Modifications

The `ReActAgent` gets minimal changes:

```python
class ReActAgent(Agent):
    def __init__(self, ...):
        # Existing attributes...
        self.message_history: list = []  # NEW

    def _build_messages(self, question: str) -> list:
        """Build full message list from history + new question."""
        return [
            {"role": "system", "content": self._get_system_prompt()},
            *self.message_history,
            {"role": "user", "content": f"Question: {question}"}
        ]

    async def run(self, question: str, verbose: Optional[bool] = None) -> str:
        # Use _build_messages() instead of inline list
        # After final answer, append to message_history

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.message_history = []
```

**History contents:**
- User questions: `{"role": "user", "content": "Question: ..."}`
- Final answers: `{"role": "assistant", "content": "..."}`

**Not stored:** Internal Thought/Action/Observation steps (transient within single `run()`)

### CLI Interactive Mode

```python
async def interactive_session(debug: bool = False):
    """Run an interactive chat session."""
    session = await Session.create(verbose=debug)

    print("Chat started. Type /quit to exit, /clear to reset history.\n")

    try:
        while True:
            question = input("You: ").strip()

            if question.lower() == '/quit':
                break
            elif question.lower() == '/clear':
                session.clear_history()
                print("History cleared.\n")
                continue
            elif not question:
                continue

            answer = await session.ask(question)
            print(f"\nAgent: {answer}\n")

    finally:
        await session.close()
        print("Goodbye!")
```

**Slash commands:**
- `/quit` → End session
- `/clear` → Clear history, start fresh

**CLI modes:**
- `python main.py` → Interactive chat (uses Session)
- `python main.py "question"` → Single-shot (existing `run_agent()`)

## Error Handling

### Session Lifecycle Errors

| Scenario | Behavior |
|----------|----------|
| Config load fails | Raise exception, session not created |
| MCP server fails to start | Log warning, continue with available tools |
| LLM API error during `ask()` | Raise exception, session remains usable for retry |
| MCP connection lost mid-session | Log error, attempt reconnect on next `ask()` |
| `close()` called multiple times | No-op, safe to call |

### Agent-Level Errors

| Scenario | Behavior |
|----------|----------|
| Max iterations reached | Return error message, history preserved |
| Tool execution fails | Error as observation, agent can retry |
| Unparseable LLM response | Prompt reformat, continue loop |

**Principle:** Errors during one turn should not corrupt the session.

## Testing Strategy

### Unit Tests

| Test | Description |
|------|-------------|
| `test_session_create` | Session initializes with all resources |
| `test_session_ask_single` | Single question returns answer |
| `test_session_ask_multi_turn` | Second question sees first question's context |
| `test_session_close` | Resources cleaned up properly |
| `test_clear_history` | History cleared, resources remain active |
| `test_history_length` | Property returns correct count |

### Integration Tests

| Test | Description |
|------|-------------|
| `test_interactive_session` | Simulate CLI input/output |
| `test_mcp_persists_across_turns` | MCP server stays connected between questions |

### Test Approach

- Mock LLM responses for deterministic unit tests
- Use fake MCP server for integration tests
- Verify message history content after multi-turn conversations

## Implementation Plan

1. Add `message_history` and `clear_history()` to `ReActAgent`
2. Create `src/session/` with `Session` class
3. Update `main.py` with interactive chat loop
4. Add unit and integration tests

## Backward Compatibility

- Single-shot mode (`python main.py "question"`) unchanged via `run_agent()`
- No breaking changes to configuration or MCP server setup
- Existing tests continue to pass
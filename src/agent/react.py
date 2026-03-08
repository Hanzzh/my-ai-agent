"""ReAct (Reasoning + Acting) Agent implementation."""

import re
import json
from typing import Dict, Tuple, Optional, Any
from .factory import Agent
from ..llm.base import LLMProvider
from ..mcp.loader import MCPLoader


class ReActAgent(Agent):
    """
    ReAct Agent that implements the Thought-Action-Observation loop.

    The agent reasons about what to do (Thought), takes action (Action),
    and observes the result (Observation) in an iterative loop.
    """

    def __init__(
        self,
        llm: LLMProvider,
        mcp_loader: MCPLoader,
        max_iterations: int = 10
    ):
        """
        Initialize ReAct Agent.

        Args:
            llm: LLM provider for generating responses
            mcp_loader: MCP loader for accessing tools
            max_iterations: Maximum number of Thought-Action-Observation cycles
        """
        self.llm = llm
        self.mcp_loader = mcp_loader
        self.max_iterations = max_iterations
        self.tools: Dict[str, Tuple] = {}  # tool_name -> (client, tool)

    async def initialize(self):
        """Load tools from MCP servers."""
        await self.mcp_loader.load_all()
        self.tools = self.mcp_loader.get_all_tools()

    def _get_system_prompt(self) -> str:
        """
        Generate the system prompt with available tools.

        Returns:
            Formatted system prompt string
        """
        tools_desc = self._format_tools_description()

        prompt = f"""You are a helpful assistant that can use tools to answer questions.

Available tools:
{tools_desc}

You should follow this format in each step:

Thought: your reasoning about what to do next
Action: the action to take, should be one of: [{', '.join(self.tools.keys())}] or "Final Answer"
Action Input: the input to the action (if applicable)

When you have enough information to answer the question, use:
Action: Final Answer
Action Input: your final answer

Example:
Thought: I need to search for information about X
Action: search
Action Input: {{"query": "X"}}

Thought: The search results show that Y is relevant
Action: Final Answer
Action Input: Based on the search, Y is the answer...

Important:
- Always think before acting
- Use tools when needed to gather information
- Provide clear and concise reasoning
- When using Final Answer, provide a complete response to the original question
- Action Input should be a JSON object for tool calls, or plain text for Final Answer
"""
        return prompt

    def _format_tools_description(self) -> str:
        """
        Format available tools as a string.

        Returns:
            Formatted tools description
        """
        if not self.tools:
            return "No tools available."

        descriptions = []
        for tool_name, (_, tool) in self.tools.items():
            desc = f"- {tool_name}: {tool.description}"
            if tool.inputSchema:
                desc += f" (input schema: {json.dumps(tool.inputSchema)})"
            descriptions.append(desc)

        return "\n".join(descriptions)

    def _parse_action(self, response: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Parse action and action input from LLM response.

        Args:
            response: LLM response text

        Returns:
            Tuple of (action_name, action_input_dict)
            Returns (None, None) if parsing fails
        """
        # Try to match Action: and Action Input: patterns
        action_match = re.search(r'Action:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
        input_match = re.search(r'Action Input:\s*(.+?)(?:\n\n|\nThought:|\nAction:|$)', response, re.IGNORECASE | re.DOTALL)

        if not action_match:
            return None, None

        action = action_match.group(1).strip()

        # Handle Final Answer case
        if action.lower() == "final answer":
            return "final_answer", None

        # Parse action input as JSON
        action_input = None
        if input_match:
            input_str = input_match.group(1).strip()
            try:
                action_input = json.loads(input_str)
            except json.JSONDecodeError:
                # If not valid JSON, try to use as-is
                action_input = {"raw_input": input_str}

        return action, action_input

    def _parse_answer(self, response: str) -> Optional[str]:
        """
        Parse final answer from LLM response.

        Args:
            response: LLM response text

        Returns:
            Final answer string or None if not found
        """
        # Look for "Action: Final Answer" followed by "Action Input:"
        final_answer_match = re.search(
            r'Action:\s*Final Answer\s*\n\s*Action Input:\s*(.+?)(?:\n\n|$)',
            response,
            re.IGNORECASE | re.DOTALL
        )

        if final_answer_match:
            return final_answer_match.group(1).strip()

        return None

    async def run(self, question: str, verbose: bool = True) -> str:
        """
        Run the ReAct loop to answer the question.

        Args:
            question: The user's question
            verbose: Whether to print intermediate steps

        Returns:
            The final answer
        """
        # Build conversation history
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": f"Question: {question}"}
        ]

        for iteration in range(self.max_iterations):
            # Get LLM response
            response = self.llm.chat(messages)

            if verbose:
                print(f"\n=== Iteration {iteration + 1} ===")
                print(f"LLM Response:\n{response}")

            # Check if agent provided final answer
            final_answer = self._parse_answer(response)
            if final_answer:
                if verbose:
                    print(f"\nFinal Answer: {final_answer}")
                return final_answer

            # Parse action
            action, action_input = self._parse_action(response)

            if action is None:
                if verbose:
                    print("\nCould not parse action, asking LLM to clarify...")
                # Add assistant response before error message
                messages.append({
                    "role": "assistant",
                    "content": response
                })
                messages.append({
                    "role": "user",
                    "content": "Please follow the required format with Action: and Action Input:"
                })
                continue

            if verbose:
                print(f"\nAction: {action}")
                print(f"Action Input: {action_input}")

            # Handle Final Answer
            if action == "final_answer":
                # The response should contain the answer
                if action_input and "raw_input" in action_input:
                    return action_input["raw_input"]
                # Try to extract from response
                answer = self._parse_answer(response)
                if answer:
                    return answer
                # Last resort: use the last part of response
                return response.split("Action Input:")[-1].strip()

            # Execute tool action
            if action in self.tools:
                try:
                    client, tool = self.tools[action]
                    result = await client.call_tool(action, action_input or {})

                    observation = f"Observation: {result}"

                    if verbose:
                        print(f"\n{observation}")

                    # Add to conversation history
                    messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    messages.append({
                        "role": "user",
                        "content": observation
                    })

                except Exception as e:
                    error_msg = f"Error executing tool {action}: {str(e)}"
                    if verbose:
                        print(f"\n{error_msg}")

                    # Add assistant response before error message
                    messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    messages.append({
                        "role": "user",
                        "content": error_msg
                    })
            else:
                error_msg = f"Unknown tool: {action}. Available tools: {', '.join(self.tools.keys())}"
                if verbose:
                    print(f"\n{error_msg}")

                # Add assistant response before error message
                messages.append({
                    "role": "assistant",
                    "content": response
                })
                messages.append({
                    "role": "user",
                    "content": error_msg
                })

        # Max iterations reached
        return f"Reached maximum iterations ({self.max_iterations}) without finding a final answer."

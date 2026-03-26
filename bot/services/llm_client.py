"""LLM API client service for intent routing.

Uses JSON-based tool calling with proper function schemas.
"""

import json
import sys
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ToolCall:
    """Represents a tool call from LLM."""

    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """Response from LLM API."""

    content: str | None
    tool_calls: list[ToolCall]


class LLMClient:
    """Client for LLM API with JSON-based tool calling."""

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/inno-se-toolkit",
                    "X-Title": "LMS Telegram Bot",
                },
                timeout=60.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _get_tool_schemas(self) -> list[dict[str, Any]]:
        """Get tool schemas as JSON function definitions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_items",
                    "description": "Get list of available items (labs, tasks). Use item_type='lab' to get only labs.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_type": {
                                "type": "string",
                                "description": "Type of items to retrieve. Use 'lab' for labs only.",
                                "enum": ["lab", "task", None],
                            }
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_learners",
                    "description": "Get enrolled students and their groups.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_scores",
                    "description": "Get score distribution (4 buckets) for a specific lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_pass_rates",
                    "description": "Get per-task average scores and attempt counts for a lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_timeline",
                    "description": "Get submissions per day timeline for a lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_groups",
                    "description": "Get per-group scores and student counts for a lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_top_learners",
                    "description": "Get top N learners by score for a lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of top learners to return. Default is 10.",
                                "default": 10,
                            },
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_completion_rate",
                    "description": "Get completion rate percentage for a lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "trigger_sync",
                    "description": "Trigger data sync from autochecker to refresh data.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
        ]

    def _build_system_prompt(self) -> str:
        """Build system prompt for the LLM."""
        return """You are a helpful assistant for a Learning Management System (LMS).
You have access to backend tools that provide data about labs, students, scores, and pass rates.

Your job is to:
1. Understand the user's question
2. Call the appropriate tools to get data
3. Analyze the results
4. Provide a clear, helpful answer based on the actual data

Important rules:
- Always call tools to get real data before answering questions about labs, scores, or students
- If the user asks about "worst" or "lowest" or "best" - compare data across labs
- If the user asks about a specific lab, use the lab identifier like "lab-01", "lab-02", etc.
- When comparing labs, get data for ALL labs first, then compare
- Be specific - include actual numbers and percentages from the data
- If you don't have enough information, ask clarifying questions

Available tools:
- get_items: List labs and tasks. Use item_type="lab" to get only labs.
- get_learners: Get enrolled students and groups.
- get_scores: Get score distribution for a lab (4 buckets).
- get_pass_rates: Get per-task pass rates and attempts for a lab.
- get_timeline: Get submission timeline for a lab.
- get_groups: Get per-group scores for a lab.
- get_top_learners: Get top N learners for a lab.
- get_completion_rate: Get completion rate for a lab.
- trigger_sync: Refresh data from autochecker.

When you need to call a tool, respond with a tool_call in the format specified.
After receiving tool results, analyze them and provide a helpful answer.
"""

    async def _call_llm(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Call the LLM API."""
        client = await self._get_client()
        
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": self._get_tool_schemas(),
            "tool_choice": "auto",
        }
        
        print(f"[llm] Calling {self.base_url} with model {self.model}", file=sys.stderr)
        response = await client.post("/chat/completions", json=payload)
        print(f"[llm] Response status: {response.status_code}", file=sys.stderr)
        response.raise_for_status()
        return response.json()

    def _parse_tool_calls(self, response: dict[str, Any]) -> list[ToolCall]:
        """Parse tool calls from LLM response."""
        tool_calls = []
        choices = response.get("choices", [])
        if not choices:
            return tool_calls
        
        message = choices[0].get("message", {})
        raw_tool_calls = message.get("tool_calls", [])
        
        for tc in raw_tool_calls:
            func = tc.get("function", {})
            name = func.get("name", "")
            arguments_str = func.get("arguments", "{}")
            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError:
                arguments = {}
            
            if name:
                tool_calls.append(ToolCall(name=name, arguments=arguments))
        
        return tool_calls

    def _get_content(self, response: dict[str, Any]) -> str | None:
        """Get text content from LLM response."""
        choices = response.get("choices", [])
        if not choices:
            return None
        message = choices[0].get("message", {})
        return message.get("content")

    async def _execute_tool(self, tool_call: ToolCall, lms_client: Any) -> Any:
        """Execute a tool call and return the result."""
        name = tool_call.name
        args = tool_call.arguments
        
        print(f"[tool] LLM called: {name}({args})", file=sys.stderr)
        
        if name == "get_items":
            item_type = args.get("item_type")
            result, error = await lms_client.get_items(item_type)
        elif name == "get_learners":
            result, error = await lms_client.get_learners()
        elif name == "get_scores":
            lab = args.get("lab", "")
            result, error = await lms_client.get_scores(lab)
        elif name == "get_pass_rates":
            lab = args.get("lab", "")
            result, error = await lms_client.get_pass_rates(lab)
        elif name == "get_timeline":
            lab = args.get("lab", "")
            result, error = await lms_client.get_timeline(lab)
        elif name == "get_groups":
            lab = args.get("lab", "")
            result, error = await lms_client.get_groups(lab)
        elif name == "get_top_learners":
            lab = args.get("lab", "")
            limit = args.get("limit", 10)
            result, error = await lms_client.get_top_learners(lab, limit)
        elif name == "get_completion_rate":
            lab = args.get("lab", "")
            result, error = await lms_client.get_completion_rate(lab)
        elif name == "trigger_sync":
            result, error = await lms_client.trigger_sync()
        else:
            result = None
            error = type("Error", (), {"message": f"Unknown tool: {name}"})()
        
        if error:
            print(f"[tool] Error: {error.message}", file=sys.stderr)
            return {"error": error.message}
        
        print(f"[tool] Result: {len(result) if isinstance(result, (list, dict)) else 'ok'}", file=sys.stderr)
        return result

    async def chat_with_tools(
        self,
        user_message: str,
        lms_client: Any,
        max_iterations: int = 3,
    ) -> str:
        """Chat with LLM using tool calling.

        Args:
            user_message: User's message text
            lms_client: LMS API client for executing tools
            max_iterations: Maximum tool calling iterations

        Returns:
            Final response text
        """
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_message},
        ]

        for iteration in range(max_iterations):
            # Call LLM
            response = await self._call_llm(messages)
            
            # Get content and tool calls
            content = self._get_content(response)
            tool_calls = self._parse_tool_calls(response)

            # If no tool calls and has content - return the answer
            if not tool_calls:
                if content:
                    return content
                return "I'm not sure how to help with that. Try asking about labs, scores, or students."

            # Execute tool calls
            tool_results = []
            for tc in tool_calls:
                result = await self._execute_tool(tc, lms_client)
                tool_results.append({
                    "tool_call_id": tc.name,
                    "name": tc.name,
                    "result": result,
                })

            # Add tool calls and results to messages
            messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": [
                    {
                        "id": tc.name,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in tool_calls
                ],
            })

            # Add tool results
            for tr in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tr["tool_call_id"],
                    "name": tr["name"],
                    "content": json.dumps(tr["result"], ensure_ascii=False),
                })

            print(f"[summary] Feeding {len(tool_results)} tool result(s) back to LLM", file=sys.stderr)

        # If we exhausted iterations, try to get a final answer
        messages.append({
            "role": "user",
            "content": "Please provide a final answer based on the data you've collected.",
        })

        response = await self._call_llm(messages)
        content = self._get_content(response)
        
        if content:
            return content
        
        return "I collected the data but couldn't formulate a response. Please try rephrasing your question."

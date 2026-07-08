"""DSPy module and helpers for Tool Description Optimization.

Exposes ToolSelectionModule where the instructions block houses the formatted
tool schemas mutated by GEPA/MIPROv2.
"""

import re
from typing import Any

import dspy


def format_baseline_descriptions(builtin_tools: list) -> str:
    """Format baseline tool schemas into a marked text block for DSPy instructions."""
    lines = [
        "You are an orchestrator selecting the correct tool for the user's task.",
        "Choose the single most appropriate tool from the schemas below.",
        "",
    ]
    for tool in builtin_tools:
        lines.append(f"[TOOL {tool.name}]")
        lines.append(tool.description)
        # Include parameter hints
        if "properties" in tool.input_schema:
            lines.append("Parameters:")
            for param, prop in tool.input_schema["properties"].items():
                desc = prop.get("description", "")
                required = " (required)" if param in tool.input_schema.get("required", []) else ""
                lines.append(f"  - {param}: {desc}{required}")
        lines.append("")

    lines.append("Output the predicted correct tool name and its arguments.")
    return "\n".join(lines)


def parse_evolved_descriptions(instructions_text: str) -> dict[str, dict[str, Any]]:
    """Parse evolved instructions text block back into individual tool descriptions."""
    pattern = r"\[TOOL\s+([\w\-]+)\](.*?)(?=\[TOOL|\Z)"
    matches = re.finditer(pattern, instructions_text, re.DOTALL)
    result = {}
    for match in matches:
        tool_name = match.group(1).strip()
        body = match.group(2).strip()

        # Extract descriptions
        lines = []
        param_desc = {}
        in_params = False
        current_param = None

        for line in body.split("\n"):
            line_str = line.strip()
            if not line_str:
                continue

            if line_str.startswith("Parameters:"):
                in_params = True
                continue

            if in_params:
                # E.g. "  - query: The search term"
                param_match = re.match(r"^-\s+(\w+):\s*(.*)$", line_str)
                if param_match:
                    current_param = param_match.group(1).strip()
                    desc = param_match.group(2).strip()
                    # Remove trailing (required) label
                    desc = re.sub(r"\s*\(required\)\s*$", "", desc)
                    param_desc[current_param] = desc
                else:
                    # Multi-line param desc or unrelated
                    pass
            else:
                lines.append(line_str)

        tool_desc = " ".join(lines).strip()
        result[tool_name] = {
            "description": tool_desc,
        }
        if param_desc:
            result[tool_name]["parameters"] = param_desc

    return result


class ToolSelectionModule(dspy.Module):
    """A DSPy module that wraps the tool selection task for optimization."""

    class PredictTool(dspy.Signature):
        """Select the correct tool to execute the task from the available tools.

        Output the predicted tool name and arguments.
        """

        task_input: str = dspy.InputField(desc="The user's query or task description")
        predicted_tool: str = dspy.OutputField(desc="The predicted correct tool name")
        predicted_args: str = dspy.OutputField(desc="JSON block containing arguments for the tool")

    def __init__(self, formatted_descriptions: str):
        super().__init__()
        self.predictor = dspy.ChainOfThought(self.PredictTool)
        # Seed the signature instructions with the tool descriptions text
        p = self.predictor.predictors()[0]
        p.signature = p.signature.with_instructions(formatted_descriptions)

    @property
    def formatted_descriptions(self) -> str:
        """Get the current formatted descriptions from instructions."""
        return self.predictor.predictors()[0].signature.instructions

    def forward(self, task_input: str) -> dspy.Prediction:
        result = self.predictor(task_input=task_input)
        return dspy.Prediction(
            predicted_tool=result.predicted_tool,
            predicted_args=result.predicted_args,
        )

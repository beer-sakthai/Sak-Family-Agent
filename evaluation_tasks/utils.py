import json
import re
from functools import wraps


def get_intro_line(persona_text):
    """
    Extracts the required introductory line from the persona text.
    It looks for the line that follows the 'For me that line is:' directive.
    """
    match = re.search(r"For me that line is:\s*\n\s*\*\*(.*?)\*\*", persona_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def check_intro_line(predictions, references, docs):
    """
    Metric that checks if the prediction starts with the correct intro line
    extracted from the persona in the corresponding doc.
    """
    intro_line = get_intro_line(docs[0]["persona"])
    if not intro_line:
        return 0.0  # Cannot score if the persona doesn't specify an intro line.

    return 1.0 if predictions[0].strip().startswith(intro_line) else 0.0


def _parse_prediction_as_json(prediction_string):
    """
    Helper to safely parse a string into a JSON object.
    Returns the parsed data or None if parsing fails.
    """
    try:
        return json.loads(prediction_string.strip())
    except (json.JSONDecodeError, AttributeError):
        return None


def make_json_metric(validator_fn):
    """
    A higher-order function that creates a metric for evaluating JSON output.
    It handles the boilerplate of parsing the prediction string and allows
    a simple validator function to define the actual check.

    :param validator_fn: A function that takes (parsed_json, doc) and returns a float score.
    :return: A complete metric function compatible with lm-evaluation-harness.
    """

    @wraps(validator_fn)
    def metric_fn(predictions, references, docs):
        prediction_str = predictions[0]
        doc = docs[0]

        data = _parse_prediction_as_json(prediction_str)
        if data is None:
            return 0.0  # Fail if the prediction is not valid JSON.

        return validator_fn(data, doc)

    return metric_fn


@make_json_metric
def check_json_validity(data, doc):
    """Metric: Checks if the prediction is a valid JSON object."""
    return 1.0  # If we got here, _parse_prediction_as_json succeeded.


@make_yaml_metric
def check_yaml_key(data, doc):
    """Metric: Checks if the YAML contains a specific key from the doc."""
    key_to_check = doc.get("key_to_check")
    if not key_to_check or not isinstance(data, dict):
        return 0.0
    return 1.0 if key_to_check in data else 0.0


@make_json_metric
def check_json_key(data, doc):
    """Metric: Checks if the JSON contains a specific key from the doc."""
    key_to_check = doc.get("key_to_check")
    if not key_to_check or not isinstance(data, dict):
        return 0.0
    return 1.0 if key_to_check in data else 0.0


@make_json_metric
def check_json_key_value_pattern(data, doc):
    """Metric: Checks if a value for a specific key matches a regex pattern from the doc."""
    key_to_check = doc.get("key_to_check")
    value_pattern = doc.get("value_pattern")
    if (
        not key_to_check
        or not value_pattern
        or not isinstance(data, dict)
        or key_to_check not in data
    ):
        return 0.0

    value = data[key_to_check]
    return 1.0 if re.match(value_pattern, str(value)) else 0.0


@make_json_metric
def check_json_numerical_range(data, doc):
    """Metric: Checks if a JSON value for a specific key is within a numerical range."""
    key_to_check = doc.get("key_to_check")
    min_value = doc.get("min_value")
    max_value = doc.get("max_value")

    if (
        key_to_check is None
        or min_value is None
        or max_value is None
        or not isinstance(data, dict)
        or key_to_check not in data
    ):
        return 0.0  # Cannot score if range/key are not specified or key is missing.

    value = data[key_to_check]
    if not isinstance(value, (int, float)):
        return 0.0  # Value is not a number.

    return 1.0 if min_value <= value <= max_value else 0.0

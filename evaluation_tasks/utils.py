import json
import re
from functools import wraps

import yaml


def get_intro_line(persona_text):
    """
    Extracts the required introductory line from the persona text.
    It looks for the line that follows the 'For me that line is:' directive.
    """
    match = re.search(r"For me that line is:\s*\n\s*\*\*(.*?)\*\*", persona_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def process_results_soul_following(doc, results):
    """
    process_results hook (doc, results) -> {metric_name: score}: checks if the
    prediction starts with the correct intro line extracted from the doc's persona.
    """
    prediction = results[0]
    intro_line = get_intro_line(doc["persona"])
    if not intro_line:
        return {"score": 0.0}  # Cannot score if the persona doesn't specify an intro line.

    return {"score": 1.0 if prediction.strip().startswith(intro_line) else 0.0}


def _parse_prediction_as_json(prediction_string):
    """
    Helper to safely parse a string into a JSON object.
    Returns the parsed data or None if parsing fails.
    """
    try:
        return json.loads(prediction_string.strip())
    except (json.JSONDecodeError, AttributeError):
        return None


def _parse_prediction_as_yaml(prediction_string):
    """
    Helper to safely parse a string into a YAML object.
    Returns the parsed data or None if parsing fails.
    """
    try:
        return yaml.safe_load(prediction_string.strip())
    except (yaml.YAMLError, AttributeError):
        return None


def _make_process_results(parse_fn, validator_fn):
    """
    A higher-order function that builds an lm-evaluation-harness
    `process_results(doc, results)` hook. It handles the boilerplate of
    parsing the model's raw completion and allows a simple validator function
    to define the actual check against the source doc.

    :param parse_fn: Parses the raw prediction string, returning None on failure.
    :param validator_fn: A function that takes (parsed_data, doc) and returns a float score.
    :return: A `process_results(doc, results)` callable returning {"score": float}.
    """

    @wraps(validator_fn)
    def process_results(doc, results):
        data = parse_fn(results[0])
        if data is None:
            return {"score": 0.0}  # Fail if the prediction doesn't parse.

        return {"score": validator_fn(data, doc)}

    return process_results


def _check_json_validity(data, doc):
    """Validator: the prediction is a valid JSON object."""
    return 1.0  # If we got here, _parse_prediction_as_json succeeded.


def _check_json_key(data, doc):
    """Validator: the JSON contains a specific required key from the doc."""
    key_to_check = doc.get("key_to_check")
    if not key_to_check or not isinstance(data, dict):
        return 0.0
    return 1.0 if key_to_check in data else 0.0


def _check_json_key_value_pattern(data, doc):
    """Validator: a value for a specific key matches a regex pattern from the doc."""
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


def _check_json_numerical_range(data, doc):
    """Validator: a JSON value for a specific key is within a numerical range."""
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


def _check_yaml_validity(data, doc):
    """Validator: the prediction is a valid YAML document."""
    return 1.0  # If we got here, _parse_prediction_as_yaml succeeded.


def _check_yaml_key(data, doc):
    """Validator: the YAML contains a specific required key from the doc."""
    key_to_check = doc.get("key_to_check")
    if not key_to_check or not isinstance(data, dict):
        return 0.0
    return 1.0 if key_to_check in data else 0.0


process_results_json_validity = _make_process_results(_parse_prediction_as_json, _check_json_validity)
process_results_json_key_check = _make_process_results(_parse_prediction_as_json, _check_json_key)
process_results_json_key_value_pattern_check = _make_process_results(
    _parse_prediction_as_json, _check_json_key_value_pattern
)
process_results_json_numerical_range_check = _make_process_results(
    _parse_prediction_as_json, _check_json_numerical_range
)
process_results_yaml_validity = _make_process_results(_parse_prediction_as_yaml, _check_yaml_validity)
process_results_yaml_key_check = _make_process_results(_parse_prediction_as_yaml, _check_yaml_key)

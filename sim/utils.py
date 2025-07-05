"""Utility functions for the simulation engine."""

from __future__ import annotations

import json
import yaml
import pandas as pd
import simpy
from uuid import uuid4

from .constants import ALL_MONTHS


def get_current_month(start_month: str = "apr", month: int = 0) -> str:
    """Get the current month name based on elapsed months from start."""
    elapsed_months_adjusted = month
    current_month_index = (3 + elapsed_months_adjusted) % len(ALL_MONTHS)
    return ALL_MONTHS[current_month_index]


def printtimestamp(env: simpy.Environment):
    """Print a formatted timestamp for the simulation environment."""
    month = get_current_month("apr", env.now - 1)
    print(f"\nMonth: {env.now} ({month})")


def pivotbudget(db: pd.DataFrame) -> pd.DataFrame:
    """Pivot budget data for reporting."""
    df = db.pivot_table(index=["item"], columns=["step"], values="budget", aggfunc="sum", fill_value=0)
    lookup_dict_description = {row["item"]: row.get("description", "") for _, row in db.iterrows()}
    lookup_dict_type = {row["item"]: row.get("type", "") for _, row in db.iterrows()}
    df["description"] = df.index.map(lookup_dict_description).fillna("")
    df["type"] = df.index.map(lookup_dict_type).fillna("")
    columns_except_extra = [col for col in df.columns if col not in ["description", "type"]]
    new_column_order = ["description", "type"] + columns_except_extra
    df = df[new_column_order]
    pf = df.iloc[::-1]
    pf = pf.sort_values(by="type", ascending=True)
    return pf


def parseYAML(yamltext: str, variables: dict = None):
    """Parse YAML text and convert class strings to objects.

    Supports both root-level dictionary format (recommended) and legacy list format.
    Also handles mathematical expressions in curly braces {} and variable substitution.

    Root-level dictionary format (recommended):
    ```yaml
    variables:
      var1: value1
      var2: value2
    events:
      - event1...
      - event2...
    ```

    Legacy list format (still supported):
    ```yaml
    - variables:
        var1: value1
        var2: value2
    - event1...
    - event2...
    ```

    Args:
        yamltext: The YAML text to parse
        variables: Optional dictionary of variables to use in expressions
    """
    import re
    import ast
    import operator

    # Default variables that can be used in expressions
    default_variables = {
        "pi": 3.14159,
        "e": 2.71828,
    }

    # Merge with provided variables
    if variables:
        default_variables.update(variables)

    def safe_eval(expr: str, variables: dict = None) -> float:
        """Safely evaluate mathematical expressions."""
        if variables is None:
            variables = {}

        # Define safe operators
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }

        def eval_node(node):
            if isinstance(node, ast.Num):  # Numbers
                return node.n
            elif isinstance(node, ast.Constant):  # Constants (Python 3.8+)
                return node.value
            elif isinstance(node, ast.Name):  # Variables
                if node.id in variables:
                    return variables[node.id]
                else:
                    raise ValueError(f"Unknown variable: {node.id}")
            elif isinstance(node, ast.BinOp):  # Binary operations
                left = eval_node(node.left)
                right = eval_node(node.right)
                return operators[type(node.op)](left, right)
            elif isinstance(node, ast.UnaryOp):  # Unary operations
                operand = eval_node(node.operand)
                return operators[type(node.op)](operand)
            else:
                raise ValueError(f"Unsupported expression type: {type(node)}")

        try:
            # Parse the expression
            tree = ast.parse(expr, mode="eval")
            return eval_node(tree.body)
        except Exception as e:
            raise ValueError(f"Cannot evaluate expression '{expr}': {e}")

    def process_expressions(data, variables):
        """Process mathematical expressions in curly braces and substitute variables."""
        if isinstance(data, dict):
            processed = {}
            for key, value in data.items():
                processed[key] = process_expressions(value, variables)
            return processed
        elif isinstance(data, list):
            return [process_expressions(item, variables) for item in data]
        elif isinstance(data, str):
            # Look for expressions in curly braces
            expr_pattern = r"\{([^}]+)\}"
            matches = re.findall(expr_pattern, data)

            if matches:
                result = data
                for match in matches:
                    try:
                        # Evaluate the expression
                        value = safe_eval(match, variables)
                        
                        # Handle NaN values
                        import math
                        if isinstance(value, float) and math.isnan(value):
                            print(f"Warning: Expression '{match}' resulted in NaN, using 0 instead")
                            value = 0
                        elif isinstance(value, float) and math.isinf(value):
                            print(f"Warning: Expression '{match}' resulted in infinity, using 0 instead")
                            value = 0
                            
                        # Replace the expression with the calculated value
                        result = result.replace(f"{{{match}}}", str(value))
                    except Exception as e:
                        # If evaluation fails, leave the expression as is
                        print(f"Warning: Could not evaluate expression '{match}': {e}")
                        continue

                # Try to convert to number if the entire string is now numeric
                try:
                    if "." in result:
                        final_value = float(result)
                        # Check for NaN in the final result
                        import math
                        if math.isnan(final_value):
                            print(f"Warning: Final result is NaN, using 0 instead")
                            return 0
                        elif math.isinf(final_value):
                            print(f"Warning: Final result is infinity, using 0 instead")
                            return 0
                        return final_value
                    else:
                        return int(result)
                except ValueError:
                    return result

            return data
        else:
            return data

    def map_cls_strings_to_objects(data):
        if isinstance(data, list):
            for index, item in enumerate(data):
                data[index] = map_cls_strings_to_objects(item)
        elif isinstance(data, dict):
            for key, value in data.items():
                if key == "cls" and isinstance(value, str):
                    data[key] = globals().get(value, value)
                else:
                    data[key] = map_cls_strings_to_objects(value)
        return data

    # Parse the YAML
    try:
        data = yaml.safe_load(yamltext)
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML: {e}")

    if data is None:
        return []

    # Handle root-level dictionary format (recommended approach)
    if isinstance(data, dict):
        # Extract variables if they exist
        if "variables" in data:
            yaml_variables = data.pop("variables")
            default_variables.update(yaml_variables)
            print(f"Debug: Loaded variables from root-level dict: {yaml_variables}")
        
        # Return the events or projects section, or the entire dict if no specific section
        if "events" in data:
            data = data["events"]
        elif "projects" in data:
            data = data["projects"]
        else:
            # Return all remaining data (excluding variables which was already extracted)
            data = list(data.values())[0] if len(data) == 1 else data

    # Handle legacy list format (backward compatibility)
    elif isinstance(data, list):
        # Check if first item is a variables definition
        if data and isinstance(data[0], dict) and "variables" in data[0]:
            # Extract variables from the first list item
            variables_item = data.pop(0)
            yaml_variables = variables_item["variables"]
            default_variables.update(yaml_variables)
            print(f"Debug: Loaded variables from legacy list format: {yaml_variables}")

    # Process mathematical expressions and variable substitution
    data = process_expressions(data, default_variables)

    # Then handle class strings
    return map_cls_strings_to_objects(data)


def yaml_to_react_flow_json(yaml_file_path: str, json_file_path: str | None = None):
    """Convert YAML file to React Flow JSON format."""
    with open(yaml_file_path, "r") as file:
        yaml_data = yaml.safe_load(file)

    def yaml_to_react_flow(yaml_data):
        nodes = []
        edges = []
        for index, phase in enumerate(yaml_data):
            parent_node_id = str(uuid4())
            attributes = []
            for key, value in phase.items():
                if not isinstance(value, list):
                    attributes.append(f"{key}: {value}")
                else:
                    for item in value:
                        subattribute = [f"{subkey}: {item[subkey]}" for subkey in item]
                        child_node_id = str(uuid4())
                        child_node = {
                            "id": child_node_id,
                            "type": "UMLClassNode",
                            "position": {"x": 250 * index + 100, "y": 200},
                            "data": {"name": f"{key}", "attributes": subattribute},
                        }
                        nodes.append(child_node)
                        edges.append({"id": str(uuid4()), "source": parent_node_id, "target": child_node_id})
            node = {
                "id": parent_node_id,
                "type": "UMLClassNode",
                "position": {"x": 250 * index, "y": 100},
                "data": {"name": phase["name"], "attributes": attributes},
            }
            nodes.append(node)
        return {"nodes": nodes, "edges": edges}

    react_flow_data = yaml_to_react_flow(yaml_data)
    if json_file_path:
        with open(json_file_path, "w") as file:
            json.dump(react_flow_data, file, indent=4)
    return react_flow_data


def react_flow_to_yaml(json_file_path: str, yaml_file_path: str | None = None):
    """Convert React Flow JSON back to YAML format."""
    with open(json_file_path, "r") as json_file:
        react_flow_data = json.load(json_file)

    nodes = react_flow_data["nodes"]
    edges = react_flow_data["edges"]
    node_data_map = {node["id"]: node for node in nodes}
    yaml_data = []
    parent_ids = set(node_data_map.keys()) - set(edge["target"] for edge in edges)

    for parent_id in parent_ids:
        parent_node = node_data_map[parent_id]
        phase_data = {}
        for attr in parent_node["data"]["attributes"]:
            key, value = attr.split(": ", 1)
            try:
                if value.isdigit():
                    value = int(value)
                else:
                    value = eval(value)
            except Exception:
                pass
            phase_data[key] = value
        child_edges = [edge for edge in edges if edge["source"] == parent_id]
        for edge in child_edges:
            child_node = node_data_map[edge["target"]]
            category = child_node["data"]["name"]
            child_attrs = {}
            for attr in child_node["data"]["attributes"]:
                if ": " in attr:
                    key, value = attr.split(": ", 1)
                    try:
                        if value.isdigit():
                            value = int(value)
                        elif value.startswith("{") and value.endswith("}"):
                            value = value
                        else:
                            value = str(value)
                    except Exception:
                        pass
                else:
                    key = "unknown"
                    value = attr
                child_attrs[key] = value
            if category not in phase_data:
                phase_data[category] = []
            phase_data[category].append(child_attrs)
        yaml_data.append(phase_data)

    yaml_output = yaml.dump(yaml_data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    if yaml_file_path:
        with open(yaml_file_path, "w", encoding="utf-8") as yaml_file:
            yaml_file.write(yaml_output)
    return yaml_output

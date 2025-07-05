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
    df = db.pivot_table(index=['item'], columns=['step'], values='budget', aggfunc='sum', fill_value=0)
    lookup_dict_description = {row['item']: row.get('description', '') for _, row in db.iterrows()}
    lookup_dict_type = {row['item']: row.get('type', '') for _, row in db.iterrows()}
    df['description'] = df.index.map(lookup_dict_description).fillna('')
    df['type'] = df.index.map(lookup_dict_type).fillna('')
    columns_except_extra = [col for col in df.columns if col not in ['description', 'type']]
    new_column_order = ['description', 'type'] + columns_except_extra
    df = df[new_column_order]
    pf = df.iloc[::-1]
    pf = pf.sort_values(by='type', ascending=True)
    return pf


def parseYAML(yamltext: str):
    """Parse YAML text and convert class strings to objects."""
    def map_cls_strings_to_objects(data):
        if isinstance(data, list):
            for index, item in enumerate(data):
                data[index] = map_cls_strings_to_objects(item)
        elif isinstance(data, dict):
            for key, value in data.items():
                if key == 'cls' and isinstance(value, str):
                    data[key] = globals().get(value, value)
                else:
                    data[key] = map_cls_strings_to_objects(value)
        return data

    data = yaml.safe_load(yamltext)
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
    with open(json_file_path, 'r') as json_file:
        react_flow_data = json.load(json_file)

    nodes = react_flow_data['nodes']
    edges = react_flow_data['edges']
    node_data_map = {node['id']: node for node in nodes}
    yaml_data = []
    parent_ids = set(node_data_map.keys()) - set(edge['target'] for edge in edges)

    for parent_id in parent_ids:
        parent_node = node_data_map[parent_id]
        phase_data = {}
        for attr in parent_node['data']['attributes']:
            key, value = attr.split(': ', 1)
            try:
                if value.isdigit():
                    value = int(value)
                else:
                    value = eval(value)
            except Exception:
                pass
            phase_data[key] = value
        child_edges = [edge for edge in edges if edge['source'] == parent_id]
        for edge in child_edges:
            child_node = node_data_map[edge['target']]
            category = child_node['data']['name']
            child_attrs = {}
            for attr in child_node['data']['attributes']:
                if ': ' in attr:
                    key, value = attr.split(': ', 1)
                    try:
                        if value.isdigit():
                            value = int(value)
                        elif value.startswith('{') and value.endswith('}'):
                            value = value
                        else:
                            value = str(value)
                    except Exception:
                        pass
                else:
                    key = 'unknown'
                    value = attr
                child_attrs[key] = value
            if category not in phase_data:
                phase_data[category] = []
            phase_data[category].append(child_attrs)
        yaml_data.append(phase_data)

    yaml_output = yaml.dump(yaml_data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    if yaml_file_path:
        with open(yaml_file_path, 'w', encoding='utf-8') as yaml_file:
            yaml_file.write(yaml_output)
    return yaml_output

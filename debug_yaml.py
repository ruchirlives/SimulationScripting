#!/usr/bin/env python3

from sim.utils import parseYAML
import yaml

# Test with your project.yaml file
with open('project.yaml', 'r') as f:
    content = f.read()

print('=== RAW YAML ===')
print(content[:300])

print('\n=== PARSED RESULT ===')
result = parseYAML(content)
print('Type:', type(result))
print('Length:', len(result) if isinstance(result, list) else 'Not a list')

if isinstance(result, list) and len(result) > 0:
    first_event = result[0]
    print('\n=== FIRST EVENT ===')
    print('Keys:', list(first_event.keys()))
    if 'directcosts' in first_event:
        print('\n=== DIRECT COSTS ===')
        for i, cost in enumerate(first_event['directcosts']):
            print(f'Cost {i}: {cost}')
            cost_value = cost.get('cost', 'missing')
            print(f'Cost type: {type(cost_value)}')
            if 'cost' in cost:
                print(f'Cost value: {cost["cost"]}')

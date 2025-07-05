#!/usr/bin/env python3

from sim.utils import parseYAML
import math

# Test the expressions from Support.yaml to see if any produce NaN
test_expressions = [
    "2/7",
    "28/7", 
    "21/7",
    "49/7",
    "3.5/7"
]

print("Testing mathematical expressions...")
for expr in test_expressions:
    try:
        # Test evaluation
        result = eval(expr)
        print(f"{expr} = {result}")
        if isinstance(result, float):
            if math.isnan(result):
                print(f"  -> NaN detected!")
            elif math.isinf(result):
                print(f"  -> Infinity detected!")
    except Exception as e:
        print(f"{expr} -> Error: {e}")

# Test with Support.yaml file
print("\nTesting Support.yaml parsing...")
with open('Support.yaml', 'r') as f:
    content = f.read()
    
print(f"Content preview: {content[:200]}...")

try:
    result = parseYAML(content)
    print(f"Parse successful, got {len(result)} items")
    
    # Check first item
    if result:
        first_item = result[0]
        print(f"First item: {first_item}")
        daysperunit = first_item.get('daysperunit', 'missing')
        print(f"daysperunit: {daysperunit} (type: {type(daysperunit)})")
        
        if isinstance(daysperunit, float):
            if math.isnan(daysperunit):
                print("  -> NaN detected in daysperunit!")
            elif math.isinf(daysperunit):
                print("  -> Infinity detected in daysperunit!")
                
except Exception as e:
    print(f"Parse error: {e}")

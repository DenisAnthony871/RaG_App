"""Quick test to verify greeting detection works in nodes.py"""
import sys
sys.path.insert(0, '.')

# Test the GREETINGS set directly
from nodes import GREETINGS, validate_input
from langchain_core.messages import HumanMessage

print("=== GREETING SET TEST ===")
print(f"'hello' in GREETINGS: {'hello' in GREETINGS}")
print(f"'hi' in GREETINGS: {'hi' in GREETINGS}")
print(f"'hey' in GREETINGS: {'hey' in GREETINGS}")
print(f"GREETINGS contains {len(GREETINGS)} items")
print()

# Test validate_input directly  
print("=== VALIDATE_INPUT TEST ===")
test_state = {"messages": [HumanMessage(content="hello")]}
result = validate_input(test_state)
print(f"Input: 'hello'")
msgs = result.get('messages', [])
if msgs:
    print(f"Result messages: {msgs}")
    print(f"Result content: {msgs[0].content}")
    print(f"Result type: {msgs[0].type}")
else:
    print("No messages returned")

print("=== TEST COMPLETE ===")

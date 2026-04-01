"""
Auto-run repair script
"""
import asyncio
import sys

# Mock input to always return 'yes'
def mock_input(prompt):
    print(prompt)
    print("yes")
    return "yes"

# Replace input function
__builtins__.input = mock_input

# Import and run the repair function
from repair_semantic_index import repair_semantic_index

if __name__ == "__main__":
    asyncio.run(repair_semantic_index())

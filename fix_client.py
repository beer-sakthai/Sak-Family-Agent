import sys

with open('sakthai/mcp/client.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'return item' in line and i > 280:
        lines[i] = line.replace('return item', 'return cast(str, item)')
        break

with open('sakthai/mcp/client.py', 'w') as f:
    f.writelines(lines)

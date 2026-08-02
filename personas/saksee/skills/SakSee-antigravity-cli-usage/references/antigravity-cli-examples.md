# Antigravity CLI Usage Examples

## Example 1: Basic Installation and Usage

```bash
# Install the CLI
curl -fsSL https://antigravity.google/cli/install.sh | bash

# Verify installation
agy --version

# Basic usage
agy --print "Explain how React hooks work"
```

## Example 2: Interactive Session

```bash
# Start an interactive session for debugging
agy --prompt-interactive "I'm having trouble with this React component that's not updating state correctly. Here's the code:

import React, { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);
  
  const increment = () => {
    setCount(count + 1);
  };
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={increment}>Increment</button>
    </div>
  );
}

export default Counter;
"
```

## Example 3: Headless Usage with Python SDK

```python
# Install the Python SDK
# uv pip install google-antigravity

# Use with GEMINI_API_KEY
import asyncio
import os
os.environ["GEMINI_API_KEY"] = "your-api-key-here"

from google.antigravity.agent import Agent
from google.antigravity.connections.local.local_connection_config import LocalAgentConfig

async def debug_code():
    async with Agent(config=LocalAgentConfig()) as agent:
        result = await agent.chat("""
        I'm having trouble with this Python function that's supposed to calculate 
        the factorial of a number but it's not working correctly. Can you help?
        
        def factorial(n):
            if n == 0:
                return 1
            else:
                return n * factorial(n)
        """)
        text = await result.text()
        print(text)

asyncio.run(debug_code())
```

## Example 4: Working with Specific Models

```bash
# Use a specific model for code analysis
agy --model gemini-1.5-pro --print "Analyze this Python code for potential security vulnerabilities:

import os

def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()

user_input = input('Enter filename: ')
content = read_file(user_input)
print(content)
"
```

## Example 5: Project Analysis

```bash
# Add a project directory and analyze it
agy --add-dir /path/to/your/project \
    --print "Analyze this project structure and suggest improvements for code organization"
```

## Example 6: Complex Task with Timeout

```bash
# Set a longer timeout for complex analysis
agy --print-timeout 15m \
    --print "Perform a comprehensive code review of this React application, 
             including performance optimization suggestions, security considerations, 
             and best practices recommendations"
```

## Example 7: Sandbox Mode for Safe Exploration

```bash
# Use sandbox mode to limit tool access
agy --sandbox \
    --print "Show me how to list files in a directory using Python"
```

## Key Learning Points

1. **Installation is straightforward** but requires a large download (~172MB)
2. **Authentication is required** for interactive use but can be bypassed with the Python SDK
3. **Headless environments** should use the Python SDK with GEMINI_API_KEY
4. **Different models** can be selected for specific tasks
5. **Project context** can be added with --add-dir for more relevant responses
6. **Timeouts can be adjusted** for complex tasks that need more time
7. **Sandbox mode** provides a safe environment for exploration without system access

## Best Practices

1. Always verify installation with `agy --version`
2. Use the Python SDK for headless or automated environments
3. Set appropriate timeouts for complex tasks
4. Use specific models when you need particular capabilities
5. Add project context when analyzing codebases
6. Use sandbox mode when exploring potentially unsafe operations
7. Keep the CLI updated with `agy update`
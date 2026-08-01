#!/bin/bash
# SakThai 1.5B Benchmark v2 — correct tool format
MODEL="/opt/data/models/sakthai-1.5b/gguf/sakthai-1.5b-Q4_K_M.gguf"
LLAMA="/opt/data/llama-bin/build/bin/llama-cli"
LIBDIR="/opt/data/llama-bin/build/bin"
SCORE=0
TOTAL=5

run_test() {
    local name="$1"
    local system="$2"
    local tools_xml="$3"
    local user="$4"
    local expect_tool="$5"
    
    echo "  Running: $name..."
    PROMPT="<|im_start|>system
$system

# Tools

You may call functions to assist with the user query.
You are provided with function signatures within <tools></tools> XML tags:
<tools>
$tools_xml
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> tags:
<tool_call>
{\"name\": <function-name>, \"arguments\": <args-json-object>}
</tool_call><|im_end|>
<|im_start|>user
$user<|im_end|>
<|im_start|>assistant
"
    OUT=$(LD_LIBRARY_PATH="$LIBDIR" "$LLAMA" -m "$MODEL" -no-cnv -p "$PROMPT" -n 96 -t 4 --temp 0.1 --no-display-prompt 2>/dev/null)
    
    if [ "$expect_tool" = "yes" ]; then
        if echo "$OUT" | grep -qiE "tool_call|get_weather|search_web|python_repl"; then
            echo "    ✅ PASS — tool called"
            SCORE=$((SCORE + 1))
        else
            echo "    ❌ FAIL — no tool call"
        fi
    else
        if echo "$OUT" | grep -qiE "tool_call|get_weather|search_web|python_repl"; then
            echo "    FAIL"
        else
            echo "    ✅ PASS — direct answer"
            SCORE=$((SCORE + 1))
        fi
    fi
    echo "${OUT:0:120}"
    echo ""
}

echo "=== SakThai 1.5B Benchmark v2 ==="
echo "Model: Q4_K_M GGUF (934MB)"
echo "Correct tool format: <tools> XML + <tool_call> JSON"
echo ""

# 1. Simple: get_weather
run_test "simple/get_weather" \
    "You are SakThai-Agent, a helpful assistant with tool access." \
    '{"type": "function", "function": {"name": "get_weather", "description": "Get current weather for a city", "parameters": {"type": "object", "properties": {"location": {"type": "string", "description": "City name"}}, "required": ["location"]}}}' \
    "What is the weather in Paris?" \
    "yes"

# 2. Simple: search_web
run_test "simple/search_web" \
    "You are SakThai-Agent, a helpful assistant with tool access." \
    '{"type": "function", "function": {"name": "search_web", "description": "Search the web for information", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}' \
    "Search for the latest news about AI" \
    "yes"

# 3. Irrelevance: literature
run_test "irrelevance/literature" \
    "You are SakThai-Agent. You have access to tools but should NOT call them for general knowledge questions." \
    '{"type": "function", "function": {"name": "get_weather", "description": "Get weather for a city", "parameters": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}}}' \
    "Who wrote Romeo and Juliet?" \
    "no"

echo "=== Results: $SCORE/$TOTAL ==="

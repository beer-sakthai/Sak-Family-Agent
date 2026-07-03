import { GoogleGenAI, Content } from '@google/genai';
import { getAllSkills, getSkill } from './skills/registry';

const MAX_AGENT_TURNS = 10;

export async function runAgentLoop(ai: GoogleGenAI, model: string, prompt: string): Promise<string> {
  const skills = getAllSkills();
  const tools = skills.length > 0 ? [
    {
      functionDeclarations: skills.map(skill => ({
        name: skill.name,
        description: skill.description,
        parameters: skill.parameters
      }))
    }
  ] : undefined;

  let contents: Content[] = [
    {
      role: 'user',
      parts: [{ text: prompt }]
    }
  ];

<<<<<<< HEAD
  const systemInstruction =
    "You are a helpful and intelligent agent. Your goal is to assist the user with their request.\n\nBefore calling a tool, you MUST first explain your reasoning and plan in a 'thought' block. First, think about the user's request and your plan to address it. Then, output your thought process. Finally, call the necessary tool(s).\n\nExample:\nThought: The user wants to know the sum of two numbers. I should use the 'calculate' tool with the 'add' operation to find the result.\nTool Call: calculate(operation: 'add', a: 5, b: 3)";
=======
  const systemInstruction = {
    role: 'system',
    parts: [{
      text: "You are a helpful and intelligent agent. Your goal is to assist the user with their request.\n\nBefore calling a tool, you MUST first explain your reasoning and plan in a 'thought' block. First, think about the user's request and your plan to address it. Then, output your thought process. Finally, call the necessary tool(s).\n\nExample:\nThought: The user wants to know the sum of two numbers. I should use the 'calculate' tool with the 'add' operation to find the result.\nTool Call: calculate(operation: 'add', a: 5, b: 3)"
    }]
  };
>>>>>>> 858045420f64b1617246e98fd657d158bc7109cd

  console.log(`[Agent] Starting loop for prompt: "${prompt}"`);

  for (let i = 0; i < MAX_AGENT_TURNS; i++) {
    console.log(`[Agent] Turn ${i + 1}/${MAX_AGENT_TURNS}`);
    const response = await ai.models.generateContent({
      model,
      contents: [...contents],
      systemInstruction,
      config: {
        systemInstruction,
        tools,
        automaticFunctionCalling: { disable: true }
      }
    });

    const candidate = response.candidates?.[0];
    const messageContent = candidate?.content;

    if (messageContent) {
      contents.push(messageContent);
    }

    const parts = messageContent?.parts ?? [];
    const toolCalls = parts.filter(part => !!part.functionCall);
    const thought = parts.find(part => part.text)?.text;

    if (!toolCalls.length) {
      const finalText = thought || '';
      console.log(`[Agent] Final answer: "${finalText}"`);
      // Return final text response
      return finalText;
    }

    // If we are here, there are tool calls. Check for an accompanying thought.
    if (thought) {
      // The model provided a "thought" before its action.
      console.log(`[Agent] Thought: ${thought}`);
    }

    // Process all predicted tool calls in parallel
    const toolResponses = await Promise.all(
      toolCalls.map(async part => {
        const { name, args } = part.functionCall!;
        const skill = getSkill(name || '');
        let result: Record<string, any>;

        console.log(
          `[Agent] Model requested tool call: ${name}(${JSON.stringify(args)})`
        );

        try {
          if (!skill) {
            throw new Error(`Skill ${name} not found`);
          }
          const output = await skill.execute(args);
          result = { output };
          console.log(`[Agent] Tool call success: ${name} -> ${JSON.stringify(output)}`);
        } catch (error: any) {
          result = { error: error.message || String(error) };
          console.log(`[Agent] Tool call error: ${name} -> ${error.message || String(error)}`);
        }

        return {
          functionResponse: {
            name,
            response: result
          }
        };
      })
    );

    // Gemini expects function responses under the 'user' role
    contents.push({
      role: 'user',
      parts: toolResponses
    });
  }

  const timeoutMessage = "The agent could not reach a final answer after multiple steps. Please try again with a more specific prompt.";
  console.log(`[Agent] Reached max turns. Returning fallback message.`);
  return timeoutMessage;
}

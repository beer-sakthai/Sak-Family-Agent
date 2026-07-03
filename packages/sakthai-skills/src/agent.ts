import { GoogleGenAI, Content } from '@google/genai';
import { getAllSkills, getSkill } from './skills/registry';

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

  while (true) {
    const response = await ai.models.generateContent({
      model,
      contents: [...contents],
      config: {
        tools,
        automaticFunctionCalling: { disable: true }
      }
    });

    const candidate = response.candidates?.[0];
    const messageContent = candidate?.content;

    if (messageContent) {
      contents.push(messageContent);
    }

    const parts = messageContent?.parts || [];
    const toolCalls = parts.filter(part => part.functionCall);

    if (toolCalls.length === 0) {
      // Return final text response
      return parts.find(part => part.text)?.text || '';
    }

    // Process all predicted tool calls in parallel
    const toolResponses = await Promise.all(
      toolCalls.map(async part => {
        const { name, args } = part.functionCall!;
        const skill = getSkill(name || '');
        let result: Record<string, any>;

        try {
          if (!skill) {
            throw new Error(`Skill ${name} not found`);
          }
          const output = await skill.execute(args);
          result = { output };
        } catch (error: any) {
          result = { error: error.message || String(error) };
        }

        return {
          functionResponse: {
            name,
            response: result
          }
        };
      })
    );

    contents.push({
      role: 'tool',
      parts: toolResponses
    });
  }
}

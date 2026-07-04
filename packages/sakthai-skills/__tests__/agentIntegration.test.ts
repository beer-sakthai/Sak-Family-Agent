import { GoogleGenAI } from '@google/genai';
import { runAgentLoop } from '../src/agent';
import { clearSkills, registerSkill } from '../src/skills/registry';
import { calculateSkill } from '../src/skills/sampleSkill';

// Mock the GoogleGenAI SDK client
jest.mock('@google/genai', () => {
  return {
    GoogleGenAI: jest.fn().mockImplementation(() => {
      return {
        models: {
          generateContent: jest.fn()
        }
      };
    })
  };
});

describe('Agent Skill Integration', () => {
  let mockAi: jest.Mocked<any>;

  beforeEach(() => {
    clearSkills();
    registerSkill(calculateSkill);
    mockAi = new GoogleGenAI({ apiKey: 'test' }) as any;
  });

  test('should successfully run execution loop with tool calls and return final text', async () => {
    // 1st call predicts tool call
    mockAi.models.generateContent.mockResolvedValueOnce({
      candidates: [
        {
          content: {
            role: 'model',
            parts: [
              {
                functionCall: {
                  name: 'calculate',
                  args: { operation: 'add', a: 5, b: 3 }
                }
              }
            ]
          }
        }
      ]
    });

    // 2nd call provides final text response based on tool response
    mockAi.models.generateContent.mockResolvedValueOnce({
      candidates: [
        {
          content: {
            role: 'model',
            parts: [
              {
                text: 'The answer is 8.'
              }
            ]
          }
        }
      ]
    });

    const result = await runAgentLoop(mockAi, 'gemini-2.0-flash', 'Calculate 5 + 3');

    expect(result).toBe('The answer is 8.');

    // We expect generateContent to have been called twice
    expect(mockAi.models.generateContent).toHaveBeenCalledTimes(2);

    // Verify 1st call parameters
    const firstCallArgs = mockAi.models.generateContent.mock.calls[0][0];
    expect(firstCallArgs.model).toBe('gemini-2.0-flash');
    expect(firstCallArgs.contents[0].parts[0].text).toBe('Calculate 5 + 3');
    expect(firstCallArgs.config?.tools).toBeDefined();

    // Verify 2nd call parameters contain tool response
    const secondCallArgs = mockAi.models.generateContent.mock.calls[1][0];
    expect(secondCallArgs.contents).toHaveLength(3); // User prompt, Model prediction, Tool response
    expect(secondCallArgs.contents[2].role).toBe('user');
    expect(secondCallArgs.contents[2].parts[0].functionResponse).toEqual({
      name: 'calculate',
      response: { output: { result: 8 } }
    });
  });

  test('should catch skill errors and return details to the agent in functionResponse', async () => {
    // 1st call predicts tool call with division by zero
    mockAi.models.generateContent.mockResolvedValueOnce({
      candidates: [
        {
          content: {
            role: 'model',
            parts: [
              {
                functionCall: {
                  name: 'calculate',
                  args: { operation: 'divide', a: 5, b: 0 }
                }
              }
            ]
          }
        }
      ]
    });

    // 2nd call provides final text response explaining the error
    mockAi.models.generateContent.mockResolvedValueOnce({
      candidates: [
        {
          content: {
            role: 'model',
            parts: [
              {
                text: 'Cannot perform calculation: Cannot divide by zero.'
              }
            ]
          }
        }
      ]
    });

    const result = await runAgentLoop(mockAi, 'gemini-2.0-flash', 'Calculate 5 / 0');

    expect(result).toBe('Cannot perform calculation: Cannot divide by zero.');
    expect(mockAi.models.generateContent).toHaveBeenCalledTimes(2);

    // Verify 2nd call parameters contain error response
    const secondCallArgs = mockAi.models.generateContent.mock.calls[1][0];
    expect(secondCallArgs.contents[2].role).toBe('user');
    expect(secondCallArgs.contents[2].parts[0].functionResponse).toEqual({
      name: 'calculate',
      response: { error: 'Cannot divide by zero' }
    });
  });
});

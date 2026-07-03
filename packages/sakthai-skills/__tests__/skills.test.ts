import { Skill, registerSkill, getSkill, getAllSkills, clearSkills } from '../src/skills/registry';

describe('Skill Registry', () => {
  beforeEach(() => {
    clearSkills();
  });

  const mockSkill: Skill<{ input: string }, string> = {
    name: 'test_skill',
    description: 'A mock skill for testing registry',
    parameters: {
      type: 'OBJECT',
      properties: {
        input: { type: 'STRING', description: 'Test input' }
      },
      required: ['input']
    },
    execute: async (args: { input: string }) => {
      return `Processed: ${args.input}`;
    }
  };

  test('should register and retrieve a skill', () => {
    registerSkill(mockSkill);
    const retrieved = getSkill('test_skill');
    expect(retrieved).toBe(mockSkill);
  });

  test('should return undefined if skill is not registered', () => {
    const retrieved = getSkill('non_existent');
    expect(retrieved).toBeUndefined();
  });

  test('should retrieve all registered skills', () => {
    registerSkill(mockSkill);
    const all = getAllSkills();
    expect(all).toHaveLength(1);
    expect(all[0]).toBe(mockSkill);
  });
});

import { getSkill, registerSkill } from '../src/skills/registry';
import { calculateSkill } from '../src/skills/sampleSkill';

describe('Sample Skill: Calculate', () => {
  test('should be adhering to the Skill interface and statically registered', () => {
    // We register the imported skill in the test setup or source
    registerSkill(calculateSkill);
    const skill = getSkill('calculate');
    expect(skill).toBeDefined();
    expect(skill?.name).toBe('calculate');
    expect(skill?.description).toBeDefined();
  });

  test('should correctly perform addition', async () => {
    const result = await calculateSkill.execute({ operation: 'add', a: 5, b: 3 });
    expect(result).toEqual({ result: 8 });
  });

  test('should correctly perform division', async () => {
    const result = await calculateSkill.execute({ operation: 'divide', a: 6, b: 2 });
    expect(result).toEqual({ result: 3 });
  });

  test('should throw an error when dividing by zero', async () => {
    await expect(calculateSkill.execute({ operation: 'divide', a: 5, b: 0 }))
      .rejects.toThrow('Cannot divide by zero');
  });

  test('should throw an error for unsupported operation', async () => {
    await expect(calculateSkill.execute({ operation: 'modulo', a: 5, b: 3 }))
      .rejects.toThrow('Unsupported operation: modulo');
  });
});

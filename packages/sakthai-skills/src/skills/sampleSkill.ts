import { Skill, registerSkill } from './registry';

export const calculateSkill: Skill<{ operation: string; a: number; b: number }, { result: number }> = {
  name: 'calculate',
  description: 'Performs basic arithmetic operations: add, subtract, multiply, and divide.',
  parameters: {
    type: 'OBJECT',
    properties: {
      operation: {
        type: 'STRING',
        enum: ['add', 'subtract', 'multiply', 'divide'],
        description: 'The math operation to perform'
      },
      a: {
        type: 'NUMBER',
        description: 'The first operand'
      },
      b: {
        type: 'NUMBER',
        description: 'The second operand'
      }
    },
    required: ['operation', 'a', 'b']
  },
  async execute(args: { operation: string; a: number; b: number }): Promise<{ result: number }> {
    const { operation, a, b } = args;
    switch (operation) {
      case 'add':
        return { result: a + b };
      case 'subtract':
        return { result: a - b };
      case 'multiply':
        return { result: a * b };
      case 'divide':
        if (b === 0) {
          throw new Error('Cannot divide by zero');
        }
        return { result: a / b };
      default:
        throw new Error(`Unsupported operation: ${operation}`);
    }
  }
};

// Statically register the skill
registerSkill(calculateSkill);

export interface Skill<T = unknown, R = unknown> {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  execute(args: T): Promise<R>;
}

const registry = new Map<string, Skill>();

export function registerSkill(skill: Skill): void {
  registry.set(skill.name, skill);
}

export function getSkill(name: string): Skill | undefined {
  return registry.get(name);
}

export function getAllSkills(): Skill[] {
  return Array.from(registry.values());
}

export function clearSkills(): void {
  registry.clear();
}

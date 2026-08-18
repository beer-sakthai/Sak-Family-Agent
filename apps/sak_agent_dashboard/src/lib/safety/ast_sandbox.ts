import { ASTValidationResult } from '../types';

export const DANGEROUS_PATTERNS = [
  { pattern: /rm\s+-rf\s+(\/|~|\$HOME|\.\*)/i, reason: 'Recursive root/home filesystem deletion', severity: 'dangerous' as const },
  { pattern: /mkfs|dd\s+if=/i, reason: 'Raw disk overwrite / filesystem format', severity: 'dangerous' as const },
  { pattern: /: *\( *\) *{ *: *\| *: *& *} *; *:/, reason: 'Bash fork-bomb detected', severity: 'dangerous' as const },
  { pattern: /(curl|wget)\s+.*\|\s*(bash|sh|zsh)/i, reason: 'Unverified remote script execution via pipe', severity: 'dangerous' as const },
  { pattern: /(base64\s+-d|openssl\s+enc)\s*\|\s*(bash|sh|zsh)/i, reason: 'Obfuscated base64 decoded execution pipe', severity: 'dangerous' as const },
  { pattern: /nc(\.traditional)?\s+.*-e\s+\/(bin\/)?(bash|sh)|bash\s+-i\s+>&?\s*\/dev\/tcp\//i, reason: 'Reverse shell connection pattern', severity: 'dangerous' as const },
  { pattern: /os\.system\s*\(|subprocess\.(Popen|run|call)\s*\(.*shell\s*=\s*True/i, reason: 'Unsanitized subshell execution in Python', severity: 'warning' as const },
  { pattern: /eval\s*\(|exec\s*\(|new\s+Function\s*\(|Function\s*\(/i, reason: 'Dynamic code execution (eval/exec/Function)', severity: 'warning' as const },
  { pattern: /__import__\s*\(|importlib\.import_module\s*\(/i, reason: 'Dynamic unverified module loading', severity: 'warning' as const },
  { pattern: /shutil\.rmtree\s*\(\s*["'](\/|~|\.)["']\s*\)|fs\.(rmSync|rmdirSync|rm)\s*\(\s*["'](\/|~|\.)["']/i, reason: 'Destructive directory tree removal', severity: 'dangerous' as const },
  { pattern: /git\s+push\s+.*--force/i, reason: 'Git force-push to remote', severity: 'warning' as const },
  { pattern: /DROP\s+DATABASE|DROP\s+TABLE\s+users/i, reason: 'Destructive SQL DROP operation', severity: 'dangerous' as const },
];

/**
 * Validates bash commands or Python scripts against AST safety rules and security heuristics.
 */
export function validateToolExecutionAST(toolName: string, codeOrCommand: string): ASTValidationResult {
  const violations: string[] = [];
  let severity: 'safe' | 'warning' | 'dangerous' = 'safe';

  if (!codeOrCommand || typeof codeOrCommand !== 'string') {
    return {
      isSafe: true,
      score: 100,
      violations: [],
      requiresApproval: false,
      severity: 'safe',
    };
  }

  for (const item of DANGEROUS_PATTERNS) {
    if (item.pattern.test(codeOrCommand)) {
      violations.push(`[${item.severity.toUpperCase()}] ${item.reason}`);
      if (item.severity === 'dangerous') {
        severity = 'dangerous';
      } else if (severity !== 'dangerous') {
        severity = 'warning';
      }
    }
  }

  // Calculate AST Safety Score
  let score = 100;
  if (severity === 'dangerous') {
    score = 15;
  } else if (severity === 'warning') {
    score = 65;
  }

  const isSafe = severity === 'safe';
  const requiresApproval = severity !== 'safe';

  return {
    isSafe,
    score,
    violations,
    requiresApproval,
    severity,
  };
}

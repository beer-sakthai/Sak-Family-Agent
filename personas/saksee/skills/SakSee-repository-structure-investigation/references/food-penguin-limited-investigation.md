# Food Penguin Limited Repository Investigation - July 7, 2026

## Repository Overview

Food Penguin Limited is a comprehensive corporate dashboard for restaurant management built with:
- React 19 + TypeScript + Vite frontend
- Express/tsx backend
- Tailwind CSS for styling
- Recharts for data visualization
- Google AI (Gemini 1.5 Flash) for AI integrations

## Key Modules Identified

1. **Overview (Strategic Center)** - Real-time production status, calendar-scoped throughput tracking
2. **Branch Product Module** - POS sales tracking
3. **Resource Allocation Module** - Inventory transfers
4. **Production Module** - Kitchen throughput monitoring with AI Culinary Auditor
5. **Menu Engineering Module** - Profitability analytics with AI suggestions
6. **Waste Module** - Financial leakage tracking with AI Action Strategy generator
7. **Hours, Target, Energy, Suppliers, Finance, and Studio modules**

## Repository Structure

```
Food-Penguin-Limited/
├── src/
│   ├── App.tsx (main orchestration)
│   ├── components/ (modular tab components)
│   ├── data.ts (local data engines)
│   ├── types.ts (TypeScript interfaces)
│   ├── index.css (global styling)
│   └── firebase.ts (backend services)
├── package.json (dependencies and scripts)
├── server.ts (Express backend entrypoint)
├── vite.config.ts (Vite configuration)
└── AGENTS.md (repository guidelines)
```

## Investigation Commands Used

```bash
# Clone and explore repository
git clone https://github.com/beer-sakthai/Food-Penguin-Limited.git
cd Food-Penguin-Limited

# Check project structure
ls -la
find . -name "*.md" | head -10

# Check dependencies
cat package.json

# Check source structure
ls -la src/
ls -la src/components/
```

## Key Learning Points

1. **Complex Dashboard Structure**: The repository contains a sophisticated dashboard with multiple interconnected modules
2. **AI Integration**: Heavy use of Google AI (Jules) throughout various modules for analytics and recommendations
3. **Modular Architecture**: Clean separation of concerns with tab-based components
4. **Modern Tech Stack**: Uses cutting-edge React 19, Vite, and TypeScript
5. **Comprehensive Documentation**: Well-documented with AGENTS.md, README.md, and other guidance files

## Best Practices for Future Repository Investigations

1. Always check README.md and other documentation files first for project overview
2. Examine package.json to understand dependencies and available scripts
3. Look at the source structure to understand the architecture
4. Identify key modules and their relationships
5. Note any AI or external service integrations
6. Document the repository structure for future reference
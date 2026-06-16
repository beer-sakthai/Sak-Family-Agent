# SakThai Agent Dashboard

A modern, cyberpunk-themed web dashboard for visualizing SakThai Agent's memory, observations, and activity metrics. Built with React 19, Tailwind CSS 4, and Recharts.

## Features

- **Memory Visualization**: Track cumulative growth of facts and observations over time
- **KPI Cards**: Real-time metrics showing total facts, observations, and week-over-week deltas
- **Category Breakdown**: Visual breakdown of memory by category with animated bars
- **Facts & Observations**: Scrollable tables displaying recent facts and top observations
- **Live Data Loading**: Automatically loads from `data.json` exported by SakThai CLI
- **Cyberpunk Aesthetic**: Dark theme with cyan/magenta accents and glowing effects
- **Responsive Design**: Mobile-friendly layout that adapts to all screen sizes

## Design Philosophy

The dashboard follows a **Dark Cyberpunk Control Room** aesthetic:

- **Deep navy backgrounds** (`#0a0e27`) for immersion
- **Cyan glowing accents** (`#00d9ff`) for futuristic feel
- **Magenta secondary accents** (`#d946ef`) for data contrast
- **Monospace headers** (IBM Plex Mono) for technical credibility
- **Smooth animations** (100-300ms) for responsive interactions
- **Information-dense layout** with geometric precision

## Tech Stack

- **Frontend**: React 19 + TypeScript
- **Styling**: Tailwind CSS 4 + custom CSS components
- **Charts**: Recharts for data visualization
- **Icons**: Lucide React
- **Build**: Vite + esbuild
- **UI Components**: shadcn/ui

## Getting Started

### Installation

```bash
pnpm install
```

### Development

```bash
pnpm dev
```

The dashboard will be available at `http://localhost:3000`.

### Data Source

The dashboard expects a `data.json` file in the `client/public/` directory with the following structure:

```json
{
  "generated_at": "2026-06-15T00:00:00Z",
  "source": "live",
  "kpis": {
    "total_facts": 3,
    "total_facts_delta": 3,
    "total_observations": 0,
    "total_observations_delta": 0
  },
  "growth": {
    "labels": ["2026-05-16", "2026-05-17", ...],
    "facts": [0, 0, 0, ..., 3],
    "observations": [0, 0, 0, ..., 0]
  },
  "categories": [
    { "name": "Pref", "count": 2, "color": "#a855f7" },
    { "name": "Profile", "count": 1, "color": "#34d399" }
  ],
  "recent_facts": [
    { "id": 3, "kind": "profile", "key": "timezone", "value": "Asia/Bangkok", "created": "2026-06-15" }
  ],
  "top_observations": [
    { "summary": "Prefers concise replies", "weight": 0.9 }
  ]
}
```

### Exporting Data from SakThai

To generate the `data.json` file from your SakThai Agent:

```bash
sakthai dashboard --export path/to/data.json
```

Then copy it to `client/public/data.json`.

## Project Structure

```
client/
  public/
    data.json              # Dashboard data (exported from SakThai)
  src/
    components/
      DashboardHeader.tsx  # Header with logo and status
      KPICard.tsx          # KPI metric card
      GrowthChart.tsx      # Cumulative growth line chart
      CategoryChart.tsx    # Category breakdown bar chart
      FactsTable.tsx       # Recent facts table
      ObservationsTable.tsx # Top observations table
    hooks/
      useDashboardData.ts  # Data fetching hook
    pages/
      Home.tsx             # Main dashboard page
    index.css              # Global styles with cyberpunk theme
```

## Customization

### Colors

Edit the CSS variables in `client/src/index.css`:

```css
:root {
  --primary: #00d9ff;           /* Cyan accent */
  --chart-2: #d946ef;           /* Magenta accent */
  --background: #0a0e27;        /* Deep navy */
  --card: #141d3a;              /* Card background */
  --foreground: #e6e9f0;        /* Text color */
}
```

### Fonts

The dashboard uses IBM Plex Mono for headers and Inter for body text. Update the Google Fonts link in `client/index.html` to change fonts.

## Building for Production

```bash
pnpm build
```

The optimized build will be output to `dist/`.

## License

MIT

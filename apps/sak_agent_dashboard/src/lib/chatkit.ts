import {
  ChatKitCapability,
  ChatKitData,
  ChatKitPrerequisite,
  ChatKitSample,
} from "./types";

const CAPABILITY_LABELS: Record<ChatKitCapability, string> = {
  "server-tools": "Server tool calls",
  "client-state": "Client state mutation",
  widgets: "Custom widgets",
  "widget-actions": "Widget interaction actions",
  attachments: "File attachments",
  "speech-input": "Speech-to-text input",
  "entity-tagging": "@-mention entity tagging",
  "dynamic-thread-titles": "Dynamic thread titles",
  "image-generation": "Image generation",
  "route-visualization": "React Flow route visualization",
};

const SAMPLES: ChatKitSample[] = [
  {
    id: "cat-lounge",
    name: "cat-lounge",
    displayName: "Cat Lounge",
    description:
      "Virtual pet caretaker: the agent manages a cat's energy, happiness, and cleanliness by calling server tools that mutate persistent state, with widgets rendering the live stats in the chat surface.",
    domain: "Interactive game / stateful agent",
    port: 5170,
    runCommandFromRoot: "npm run cat-lounge",
    runCommandStandalone: "cd cat-lounge && npm install && npm run start",
    frontend: "Vite + React + TypeScript",
    backend: "FastAPI (Python) + uv",
    capabilities: [
      "server-tools",
      "widgets",
      "widget-actions",
      "client-state",
    ],
    highlights: [
      "Widgets rendered inline with dynamic stat displays",
      "Server tools mutate a persistent pet state store",
      "Widget action buttons feed back into the agent loop",
    ],
  },
  {
    id: "customer-support",
    name: "customer-support",
    displayName: "Customer Support",
    description:
      "Airline concierge agent with real itinerary data, booking-lookup and booking-modification tools, and structured widget cards for boarding passes and change proposals.",
    domain: "Support / operations agent",
    port: 5171,
    runCommandFromRoot: "npm run customer-support",
    runCommandStandalone:
      "cd customer-support && npm install && npm run start",
    frontend: "Vite + React + TypeScript",
    backend: "FastAPI (Python) + uv",
    capabilities: [
      "server-tools",
      "widgets",
      "widget-actions",
      "attachments",
    ],
    highlights: [
      "Itinerary lookup, seat change, and rebooking tools",
      "Rich boarding-pass widget rendered from tool output",
      "Attachment upload path for e-ticket receipts",
    ],
  },
  {
    id: "news-guide",
    name: "news-guide",
    displayName: "News Guide",
    description:
      "Newsroom research assistant that searches an article corpus and lets the user @-mention specific articles or authors as entities the agent then grounds its answers in.",
    domain: "Research / knowledge worker",
    port: 5172,
    runCommandFromRoot: "npm run news-guide",
    runCommandStandalone: "cd news-guide && npm install && npm run start",
    frontend: "Vite + React + TypeScript",
    backend: "FastAPI (Python) + uv",
    capabilities: [
      "server-tools",
      "entity-tagging",
      "dynamic-thread-titles",
      "widgets",
    ],
    highlights: [
      "@-mention picker over an article corpus",
      "Article-card widgets with source attribution",
      "Threads auto-retitled to reflect current focus",
    ],
  },
  {
    id: "metro-map",
    name: "metro-map",
    displayName: "Metro Map",
    description:
      "Transit planner that computes routes across a metro graph and streams a React Flow visualization back into the chat surface, updating the map as the user negotiates the plan.",
    domain: "Planning / spatial reasoning",
    port: 5173,
    runCommandFromRoot: "npm run metro-map",
    runCommandStandalone: "cd metro-map && npm install && npm run start",
    frontend: "Vite + React + TypeScript + React Flow",
    backend: "FastAPI (Python) + uv",
    capabilities: [
      "server-tools",
      "route-visualization",
      "widgets",
      "widget-actions",
    ],
    highlights: [
      "React Flow graph rendered as a first-class widget",
      "Route re-computed on client-side widget interactions",
      "Multiple constraints (time, transfers, price) as tool inputs",
    ],
  },
];

const PREREQUISITES: ChatKitPrerequisite[] = [
  {
    label: "OpenAI API key",
    detail:
      "Set OPENAI_API_KEY in the shell that runs the backend — required by every sample.",
    envVar: "OPENAI_API_KEY",
  },
  {
    label: "uv (Python)",
    detail:
      "Used by each sample's FastAPI backend to resolve and run its Python dependencies.",
    installCommand: "curl -LsSf https://astral.sh/uv/install.sh | sh",
  },
  {
    label: "Node.js ≥ 18 + npm",
    detail: "Required by the Vite + React frontends and the root workspace scripts.",
  },
];

export function getChatKitData(): ChatKitData {
  return {
    overview: {
      title: "OpenAI ChatKit — Advanced Samples",
      description:
        "Four production-shaped example apps demonstrating ChatKit, OpenAI's SDK for conversational UIs. Each pairs a Vite/React frontend with a FastAPI backend and showcases a different combination of ChatKit primitives: server tool calls, widgets, widget actions, attachments, speech input, @-mention entity tagging, and dynamic thread titles.",
      repoUrl: "https://github.com/openai/openai-chatkit-advanced-samples",
    },
    prerequisites: PREREQUISITES,
    samples: SAMPLES,
    capabilityLabels: CAPABILITY_LABELS,
  };
}

export const CHATKIT_CAPABILITY_KEYS: ChatKitCapability[] = Object.keys(
  CAPABILITY_LABELS
) as ChatKitCapability[];

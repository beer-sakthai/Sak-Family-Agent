import {
  GcpLearningData,
  GcpLearningResource,
  GcpLearningTag,
} from "./types";

const BASE = "https://github.com/GoogleCloudPlatform/training-data-analyst/tree/master";

const RESOURCES: GcpLearningResource[] = [
  {
    id: "courses",
    path: "courses/",
    title: "Full GCP courses",
    description:
      "The main training tree — per-course subdirectories mirroring Google Cloud's official curricula (data engineering, ML, MLOps, Gen AI).",
    tags: ["agents", "ml", "labs"],
    url: `${BASE}/courses`,
  },
  {
    id: "quests",
    path: "quests/",
    title: "Structured quests",
    description:
      "Guided learning paths that chain multiple labs together. Good starting point when the topic is unfamiliar rather than the individual lab.",
    tags: ["labs"],
    url: `${BASE}/quests`,
  },
  {
    id: "self-paced-labs",
    path: "self-paced-labs/",
    title: "Self-paced labs",
    description:
      "Standalone, self-contained lab exercises. Each folder is a discrete task you can run without following a course sequence.",
    tags: ["labs"],
    url: `${BASE}/self-paced-labs`,
  },
  {
    id: "bootcamps",
    path: "bootcamps/",
    title: "Bootcamps",
    description:
      "Intensive multi-day programs, often covering newer material end-to-end. Includes recent Gen AI + agent content.",
    tags: ["agents", "ml"],
    url: `${BASE}/bootcamps`,
  },
  {
    id: "datalab",
    path: "datalab/",
    title: "Datalab notebooks",
    description:
      "Jupyter notebooks for data-analysis flows. Uses older Datalab conventions but still useful for BigQuery + ML pipelines.",
    tags: ["data", "notebooks"],
    url: `${BASE}/datalab`,
  },
  {
    id: "blogs",
    path: "blogs/",
    title: "Blog-post code",
    description:
      "Companion code for GCP blog posts. Search this directory when a Google-published article references a repo path.",
    tags: ["docs", "data", "ml"],
    url: `${BASE}/blogs`,
  },
  {
    id: "cpb100",
    path: "CPB100/",
    title: "CPB100 (foundations)",
    description:
      "Legacy 'Cloud Platform Big Data 100' bootcamp material — pre-Gemini, still a good primer on BigQuery + Dataflow fundamentals.",
    tags: ["data"],
    url: `${BASE}/CPB100`,
  },
  {
    id: "doc",
    path: "doc/",
    title: "Repo docs",
    description:
      "Repo-level reference — layout, contribution guide, and pointers into the course tree.",
    tags: ["docs"],
    url: `${BASE}/doc`,
  },
];

const TAG_LABELS: Record<GcpLearningTag, string> = {
  agents: "Agents & Gen AI",
  ml: "ML / MLOps",
  data: "Data engineering",
  notebooks: "Notebooks",
  labs: "Labs / Quests",
  docs: "Docs",
};

export function getGcpLearningData(): GcpLearningData {
  return {
    overview: {
      title: "GCP Training — training-data-analyst",
      description:
        "GoogleCloudPlatform/training-data-analyst is the official repo behind cloud.google.com/training — 8.6k stars, ~8k commits. This tab curates the sub-directories most relevant when the persona work touches Gemini, Vertex, or GCP data infra. It doesn't copy notebooks in-tree; it points at them.",
      repoUrl: "https://github.com/GoogleCloudPlatform/training-data-analyst",
      stars: "8.6k",
      license: "Apache 2.0",
    },
    resources: RESOURCES,
    tagLabels: TAG_LABELS,
  };
}

export const GCP_LEARNING_TAG_KEYS: GcpLearningTag[] = Object.keys(
  TAG_LABELS
) as GcpLearningTag[];

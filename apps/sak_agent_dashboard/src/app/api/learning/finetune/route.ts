import { NextRequest, NextResponse } from "next/server";
import {
  generateDatasetCardSpec,
  listLoraJobs,
  spawnLoraTrainingJob,
  validateLoraHyperparameters,
} from "@/lib/learning/lora_engine";
import { readStagedEntries } from "@/lib/learning/dataset_staging";
import { LoraTrainingConfig } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const datasetCard = generateDatasetCardSpec();
    const stagedEntries = readStagedEntries(50);
    const jobs = listLoraJobs();
    return NextResponse.json({
      datasetCard,
      stagedCount: stagedEntries.length,
      stagedEntries,
      jobs,
    });
  } catch (error) {
    console.error("Secure Log [GET /api/learning/finetune]:", error);
    return NextResponse.json(
      { error: "An unexpected error occurred" },
      { status: 500 },
    );
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const modelName = (body.modelName as LoraTrainingConfig["modelName"]) || "sakthai-7b";
    const config: LoraTrainingConfig = {
      jobId: `job_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      modelName,
      datasetPath: String(body.datasetPath ?? "~/.sakthai/learning/dataset-staging/staging.jsonl"),
      r: Number(body.r) || 16,
      loraAlpha: Number(body.loraAlpha) || 32,
      loraDropout: Number(body.loraDropout) || 0.05,
      learningRate: Number(body.learningRate) || 2e-4,
      numEpochs: Number(body.numEpochs) || 3,
      batchSize: Number(body.batchSize) || 4,
      targetModules: Array.isArray(body.targetModules) ? (body.targetModules as string[]) : ["q_proj", "v_proj"],
      outputDir: String(body.outputDir ?? `checkpoints/${modelName}_lora`),
    };

    const validation = validateLoraHyperparameters(config);
    if (!validation.isValid) {
      return NextResponse.json({ error: "Validation failed", details: validation.errors }, { status: 400 });
    }

    const job = spawnLoraTrainingJob(config);
    return NextResponse.json({ success: true, job }, { status: 201 });
  } catch (error) {
    console.error("Secure Log [POST /api/learning/finetune]:", error);
    return NextResponse.json(
      { error: "An unexpected error occurred" },
      { status: 500 },
    );
  }
}

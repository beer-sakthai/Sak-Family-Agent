import { ApiError, createApiHandler, createMutationHandler } from "@/lib/api/handler";
import {
  generateAdkPythonCode,
  generateCloudDeploymentManifest,
  getAgentRegistryStatus,
  getAllAdkSpecs,
  runQualityFlywheelEvaluation,
} from "@/lib/adk/adk_engine";
import { DeploymentTarget } from "@/lib/types";

export const dynamic = "force-dynamic";

export const GET = createApiHandler("/api/adk/bridge", async () => ({
  agents: getAllAdkSpecs(),
  manifest: generateCloudDeploymentManifest("cloud_run"),
  evalResult: runQualityFlywheelEvaluation(),
  registryStatus: getAgentRegistryStatus(),
}));

export const POST = createMutationHandler("/api/adk/bridge", async (body) => {
  const action = String(body.action ?? "generate_manifest");

  if (action === "generate_code") {
    return { code: generateAdkPythonCode(String(body.personaSlug ?? "sakthai")) };
  }

  if (action === "generate_manifest") {
    const target = (body.target === "gke" ? "gke" : "cloud_run") as DeploymentTarget;
    return {
      manifest: generateCloudDeploymentManifest(
        target,
        String(body.serviceName ?? "sak-family-adk-service"),
        String(body.region ?? "us-central1"),
      ),
    };
  }

  if (action === "run_eval") {
    return { evalResult: runQualityFlywheelEvaluation() };
  }

  throw new ApiError(400, `Unknown action: ${action}`);
});

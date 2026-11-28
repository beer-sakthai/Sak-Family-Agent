# Agent Platform Model Garden Deployment & Lifecycle Commands Reference

This reference documents the detailed gcloud CLI commands, parameters, endpoint life-cycle steps, and safety confirmation gates for deploying models to Agent Platform endpoints.

---

## 1. Safety & Confirmation Tiers

| Tier | Actions | Confirmation Requirement |
|:---|:---|:---|
| **Tier R (Read-Only)** | `list`, `describe`, `list-deployment-config` | No confirmation required. Execute immediately. |
| **Tier M (Mutating)** | `deploy`, `undeploy-model` | Explicit user confirmation required. Verify model exists first. |
| **Tier D (Destructive)** | `delete` (endpoints or models) | Explicit typed confirmation required ("I confirm" / "Yes, delete"). |

---

## 2. Model Deployment Lifecycle Workflow

### A. List Available Deployment Configurations
```bash
gcloud alpha ai model-garden models list-deployment-config \
  --model=projects/$PROJECT_ID/locations/$LOCATION_ID/publishers/google/models/gemma-2-9b \
  --location=$LOCATION_ID
```

### B. Create Endpoint
```bash
gcloud ai endpoints create \
  --display-name="gemma-2-9b-endpoint" \
  --region=$LOCATION_ID \
  --project=$PROJECT_ID
```

### C. Deploy Model to Endpoint
```bash
gcloud ai endpoints deploy-model $ENDPOINT_ID \
  --model=$MODEL_ID \
  --display-name="gemma-2-9b-deployed" \
  --machine-type="g2-standard-8" \
  --accelerator="type=nvidia-l4,count=1" \
  --region=$LOCATION_ID \
  --project=$PROJECT_ID
```

### D. Check Operation Status
```bash
gcloud ai operations describe $OPERATION_ID \
  --region=$LOCATION_ID \
  --project=$PROJECT_ID
```

### E. Undeploy Model & Clean Up
```bash
# Undeploy
gcloud ai endpoints undeploy-model $ENDPOINT_ID \
  --deployed-model-id=$DEPLOYED_MODEL_ID \
  --region=$LOCATION_ID \
  --project=$PROJECT_ID

# Delete Endpoint (Tier D Confirmation required)
gcloud ai endpoints delete $ENDPOINT_ID \
  --region=$LOCATION_ID \
  --project=$PROJECT_ID
```

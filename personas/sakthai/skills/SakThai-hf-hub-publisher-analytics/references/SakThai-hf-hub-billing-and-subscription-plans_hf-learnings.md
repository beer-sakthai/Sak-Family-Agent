# HF Learnings: Billing and Subscription Plans

## Topic
`hf-hub-billing-and-subscription-plans`

## Date
2026-07-26

## Sources
- https://huggingface.co/docs/hub/en/billing — "Billing & Subscription"
- https://huggingface.co/subscribe/pro — "PRO Subscription Benefits"
- https://huggingface.co/pricing — Pricing page
- https://huggingface.co/docs/hub/en/storage-limits — "Storage Limits"

---

## Summary

Comprehensive reference on Hugging Face Hub's subscription plans (PRO, Team, Enterprise) — covering features, pricing, storage allocation, inference credits, ZeroGPU tiers, and compute services billing. This is essential knowledge for navigating the HF ecosystem and understanding what's available at each tier.

---

## 1. Plan Overview

Hugging Face offers four tiers of service:

| Tier | Audience | Billing | Key Benefit |
|------|----------|---------|-------------|
| **Free** | All users | None | Access to 2M+ open models, 1.5M datasets, 1.5M Spaces |
| **PRO** | Individual power users | Monthly subscription (credit card) | 1TB private storage, 10× storage boost, 20× inference credits |
| **Team** | Organizations | Monthly per-seat subscription (credit card or AWS) | Team management, shared private repos, org-level billing |
| **Enterprise** | Large organizations | Annual contract | SSO, audit logs, storage regions, resource groups, advanced security |

---

## 2. PRO Plan

### Cost
Monthly subscription paid via credit card. Billed separately from any pay-as-you-go compute usage.

### Storage Benefits

| Metric | Free | PRO | Multiplier |
|--------|------|-----|------------|
| Private storage | 100 GB (across all private repos) | **1 TB** | 10× |
| Public storage | 5 TB (across all public repos) | **10 TB** | 2× |
| Private storage per repo | 50 GB | 50 GB (same; more private repos allowed) | — |

### Inference Credits

| Benefit | Free | PRO |
|---------|------|-----|
| Inference credits | Limited free tier | **20× included credits** across all Inference Providers |
| Priority | Standard queue | Higher priority queue |

### ZeroGPU

| Tier | Free | PRO |
|------|------|-----|
| Daily quota | Standard allocation | **8× daily quota** with highest priority |
| Pay-as-you-go | Not available | Available to extend quota |
| Max Spaces | 1-2 ZeroGPU Spaces | Up to **10 ZeroGPU Spaces** |

### Spaces Compute

PRO unlocks the ability to run **Gradio and Docker Spaces on paid compute** (GPU instances).

### Dev Mode

SSH/VS Code support for Spaces — faster iteration cycles with direct access to running Space environments.

### Additional PRO Features

- Use Data Studio on **private datasets**
- Publish **Social Posts and Community Blog** articles on your HF profile
- Exclusive **early access** to upcoming features
- PRO badge on profile

---

## 3. Team Plan

### Cost
- Monthly subscription billed per seat
- Payment via credit card or AWS account
- Number of seats updates automatically at renewal to match org member count

### Features

| Feature | Description |
|---------|-------------|
| **Shared repository ownership** | Repos belong to the org, not individuals |
| **Role-based access** | Admin/write/read member roles |
| **Private repos** | Org-owned private models, datasets, Spaces |
| **Per-user egress breakdown** | Org admins can see each member's bandwidth usage |
| **Storage** | 1 TB private storage per seat |
| **All PRO features** | Each member gets PRO-level benefits within the org context |

### Team vs. Free Org

| Capability | Free Org | Team Plan |
|-----------|----------|-----------|
| Private repos | Limited | Full (1TB/seat) |
| Member management | Basic | Role-based with granular control |
| Billing | None | Per-seat subscription |
| Storage regions | US only | Configurable (see Enterprise for EU/other) |

---

## 4. Enterprise Plan

Enterprise is a custom annual contract with everything in Team plus:

### Security & Compliance

| Feature | Description |
|---------|-------------|
| **Single Sign-On (SSO)** | SAML/OIDC integration with identity providers |
| **Audit Logs** | Track all org actions (membership, settings, billing changes) with per-event granularity |
| **Storage Regions** | Choose data residency (US, EU, etc.) for GDPR and regulatory compliance |
| **Network Security** | IP access restriction, authentication enforcement |
| **Advanced Security** | Token approval system, default repo visibility controls, 2FA enforcement |
| **Resource Groups** | Fine-grained access control within org |

### Compute & Infrastructure

| Feature | Description |
|---------|-------------|
| **Data Studio for Private datasets** | Visual data exploration on private data |
| **Advanced Compute Options** | Reserved instances, custom contracts |
| **Dedicated Support** | Enterprise-grade SLAs and account management |

### Storage Regions Detail

- **Default:** US (all repositories stored in US data centers for non-Team/Enterprise users)
- **Configurable for Enterprise:** Choose regions (US, EU) for data residency compliance
- **Performance impact:** EU users storing in EU region see ~4-5× faster upload/download vs US storage
- **Spaces:** Both storage and runtime use the chosen region; hardware availability varies by region
- **Tag visibility:** Repositories in non-default regions display a region tag for easy identification
- **Limitations:** Some features (e.g., ZeroGPU) may not be available in all regions

---

## 5. Storage Overage Pricing

### Private Storage Overage

Above the included 1 TB (PRO/Team) or negotiated Enterprise allocation:

- Billed in **1 TB increments**
- Base price per 1 TB increment (precise pricing shown in billing settings)
- Charged in **pay-as-you-go** mode to the payment method on file
- Additional discounts available for large-scale volumes through account executives

### Storage Billing Flow

```
Storage Usage → 1 TB included (free) → Overage threshold → 1 TB increment
                                                                    ↓
Next renewal → aggregated with subscription → charged to payment method
```

**Note:** PRO benefits are also included in Team/Enterprise plans (each seat gets PRO-level storage).

---

## 6. Compute Services Billing

### Separate from Subscription

Compute services (Inference Providers, Inference Endpoints, GPU Spaces, ZeroGPU pay-as-you-go) are **billed separately** from subscription plans:

| Service | Billing Model | Free Tier |
|---------|---------------|-----------|
| **Inference Providers** (serverless) | Pay-per-token via credits | Yes (rate-limited, free models) |
| **Inference Endpoints** (dedicated) | Per-hour instance pricing | No (paid GPU instances) |
| **GPU Spaces** | Per-hour compute usage | Limited free ZeroGPU |
| **ZeroGPU pay-as-you-go** | Beyond daily quota | Daily free quota |

### Invoice Cycle

- Compute usage invoices are issued at the **beginning of each month**
- Credits/deposits must be added before using pay-as-you-go services
- Payment via credit card (Stripe for secure processing)
- Cloud provider partnerships (AWS, Azure, GCP) available for Enterprise

### Credits System

Users add credits to their account to use pay-as-you-go services:

```
Add Credits → Used for → Inference Providers (per-token)
                          Inference Endpoints (per-hour)
                          GPU Spaces (per-hour)
                          ZeroGPU extra quota
```

---

## 7. Free Tier Limits

For users on the free tier (like Beer's use case — no income):

### Storage

| Resource | Limit |
|----------|-------|
| Private repos total | 100 GB |
| Per private repo | 50 GB |
| Public repos total | 5 TB |
| Per public repo | 50 GB (same) |

### Inference

| Service | Limit |
|---------|-------|
| Serverless Inference | Rate-limited, free for open models |
| Inference Endpoints | Not available (paid only) |
| ZeroGPU Spaces | 1-2 Spaces, daily quota |
| GPU Spaces | Not available (paid only) |

### Features Not Available on Free

- Private datasets in Data Studio
- Social Posts / Community Blogs
- Dev Mode (SSH/VS Code)
- SSO, Audit Logs, Storage Regions
- Resource Groups
- Per-user egress breakdown

### What IS Available on Free

✅ Access to all **public models, datasets, and Spaces** (2M+ models, 1.5M datasets)
✅ **Download models** with hf_xet acceleration
✅ **Stream datasets** with Datasets library
✅ **Create public repos** (models, datasets, Spaces)
✅ **Inference API** with rate limits (Serverless Inference Providers)
✅ **ZeroGPU** for Gradio demos (limited quota)
✅ **Webhooks** for automation
✅ **Discussions, PRs, and notifications**
✅ **Collections** to organize repos
✅ **OAuth / Sign in with HF** integration
✅ **Agent Skills** and CLI agent mode

---

## 8. Plan Comparison Matrix

| Feature | Free | PRO | Team | Enterprise |
|---------|:----:|:---:|:----:|:----------:|
| Public repos | Unlimited | Unlimited | Unlimited | Unlimited |
| Private storage | 100 GB | **1 TB** | 1 TB/seat | Custom |
| Public storage | 5 TB | **10 TB** | 10 TB/seat | Custom |
| Inference credits | Limited | **20×** | 20× per member | Custom |
| ZeroGPU quota | Standard | **8×** | 8× per member | Custom |
| ZeroGPU Spaces | 1-2 | **10** | 10 per member | Custom |
| GPU Spaces | ❌ | ✅ | ✅ | ✅ |
| Dev Mode | ❌ | ✅ | ✅ | ✅ |
| Private Data Studio | ❌ | ✅ | ✅ | ✅ |
| Social Posts/Blogs | ❌ | ✅ | ✅ | ✅ |
| Org management | Basic | — | ✅ | ✅ |
| Role-based access | ❌ | ❌ | ✅ | ✅ |
| Per-user egress | ❌ | ❌ | ✅ | ✅ |
| SSO | ❌ | ❌ | ❌ | ✅ |
| Audit Logs | ❌ | ❌ | ❌ | ✅ |
| Storage Regions | ❌ | ❌ | ❌ | ✅ |
| Resource Groups | ❌ | ❌ | ❌ | ✅ |
| Network Security | ❌ | ❌ | ❌ | ✅ |
| Advanced Security | ❌ | ❌ | ❌ | ✅ |
| Dedicated Support | ❌ | ❌ | ❌ | ✅ |
| Annual contract | ❌ | ❌ | ❌ | ✅ |

---

## 9. Common Questions

### Q: Can I pay for PRO with something other than a credit card?
A: PRO subscriptions require a credit card via Stripe. Team subscriptions also support AWS billing. Enterprise uses annual contracts with flexible payment options.

### Q: What happens when I exceed my storage limit?
A: For private storage, overage is billed in 1 TB increments. Public storage limits are higher; exceeding them may result in rate limiting or outreach from HF.

### Q: Are PRO benefits included in Team/Enterprise?
A: Yes. Each seat in a Team/Enterprise plan gets the equivalent of PRO-level storage, inference credits, and ZeroGPU allocation.

### Q: Can I try PRO before subscribing?
A: HF does not publicly advertise a free trial for PRO. Check the PRO subscription page for current promotions.

### Q: How do inference credits work?
A: Credits are consumed per-token when using Inference Providers (serverless API). Different models have different per-token credit costs. Free tier has a limited daily/monthly allowance; PRO gets 20× more.

### Q: Is there a student or academic discount?
A: HF does not publicly advertise academic pricing. Enterprise plans may negotiate educational discounts via account executives.

---

## 10. Key Insights

1. **Free tier is genuinely usable** — For individual developers and researchers, the free tier provides substantial access to open models, inference, and Spaces. The main limitation is private storage (100 GB) and ZeroGPU quota.

2. **PRO is best for serious hobbyists** — The 1 TB private storage, 20× inference credits, and 10 ZeroGPU Spaces make PRO attractive for power users who need private repos and more compute time.

3. **Team plan = PRO per seat** — Team plan effectively gives each member PRO-level benefits within an org context, plus shared repo ownership and member management.

4. **Enterprise fills compliance gaps** — SSO, audit logs, and storage regions are the key differentiators for regulated industries.

5. **Compute is always separate** — Subscription plans cover storage and platform features; compute (inference, GPU Spaces) is always pay-as-you-go on top.

6. **Storage overage costs add up** — At 1 TB increments, heavy private storage users should plan carefully. Public storage (5-10 TB) is more generous.

7. **ZeroGPU is the free-tier compute path** — For free-tier users wanting GPU compute for demos, ZeroGPU (with its daily quota) is the only option.

8. **No income = free tier is sufficient** — For Beer's use case (tool-calling training data, open models, GGUF inference on local hardware), the free tier covers all needs. PRO becomes relevant only if private repos or significantly more inference credits are needed.

---

## Skill Created
`hf-hub-billing-and-subscription-plans/` with:
- `SKILL.md` — topic overview and metadata (author: SakThai, license: MIT)
- `references/hf-learnings.md` — this full reference

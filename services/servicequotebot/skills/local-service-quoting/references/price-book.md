# Local Service Price Book — 2026/2027

> **Reference pricing for ServiceQuoteBot.** All quotes must strictly adhere to the prices, packages, and terms defined in this catalog. Never invent prices or offer discounts exceeding 15% without Beer's written approval.

---

## 1. On-Demand & Diagnostic Services

| Service Item | Description | Rate | Minimum Billing |
|---|---|---|---|
| **Diagnostic Assessment** | On-site / remote systems inspection, electrical/automation diagnostics | $150 / visit | 1 visit (credited toward project if hired) |
| **Standard Service Hourly** | Normal business hours (M-F 8am - 6pm) maintenance and installation | $120 / hour | 1 hour |
| **Emergency / After-Hours** | Nights, weekends, and holidays urgent dispatch | $195 / hour | 2 hours |

---

## 2. Fixed Project Packages

### Package A: Essential Smart Facility Automation
- **Base Price:** $1,450
- **Scope:**
  - Up to 8 IoT / automation control points (lighting, climate, sensors).
  - Central gateway setup and local controller integration.
  - Fail-safe configuration with local persistence.
  - 30 days post-installation calibration and support.

### Package B: Complete Commercial Optimization
- **Base Price:** $3,800
- **Scope:**
  - Up to 24 automation and monitoring points.
  - Multi-zone HVAC, energy monitoring, and automated scheduling.
  - Custom reporting dashboard and alert rules.
  - 90 days priority warranty and tuning.

### Package C: Enterprise Infrastructure Overhaul
- **Base Price:** $7,500+ (custom scope assessed via diagnostic)
- **Scope:**
  - Full-building automation, redundant controllers, backup power integration.
  - Full local-first private deployment with audit logs.
  - Dedicated technician onboarding and training.

---

## 3. Recurring Maintenance & Retainers (Monthly Recurring Revenue - MRR)

| Plan | Monthly Fee | Included Service | SLA / Response Time |
|---|---|---|---|
| **Essential Retainer** | $299 / month | 2 hours included maintenance, quarterly system checkup, remote firmware updates | Next business day |
| **Proactive Care** | $599 / month | 5 hours included maintenance, monthly physical audit, sensor calibration, priority queue | Within 4 hours |
| **Mission-Critical 24/7** | $1,299 / month | 12 hours included maintenance, weekly audits, spare parts stock on-site, 24/7 emergency dispatch | Within 1 hour |

*Note: Unused included hours roll over for up to 60 days on Proactive and Mission-Critical plans.*

---

## 4. Discount & Promotional Policy

1. **Standard Promotional Cap:** Maximum 15% discount on labor or package base price for first-time customers or upfront annual subscription prepayment.
2. **Prepayment Discount:** 10% discount on total annual cost if an MRR retainer is paid upfront (12 months).
3. **Hardware / Pass-Through Costs:** Zero discount permitted on third-party hardware, sensors, or materials.
4. **Exceptions:** Any request exceeding 15% discount requires escalating the lead to Beer via `SakThai` or `SakTan`.

---

## 5. Quote Handoff Checklist

When presenting a quote:
1. List individual package or hourly items clearly.
2. If recurring maintenance is relevant, present the matching MRR plan.
3. State the total estimated price ($ USD) and validity period (quotes valid for 30 calendar days).
4. Capture client Name, Phone, and Email.
5. Record quote in lead database using `capture_lead` with `status: QUOTED` and `deal_value` set to quote total.

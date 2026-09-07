---
name: SakSee-production-management-planner
description: "Plan and optimize House of Sak service delivery for QA, AI, and API projects."
---

# Production Management Planner

A comprehensive skill for creating production plans, analyzing performance, tracking costs, and generating reports specifically for AI and development services. This skill helps manage service delivery workflows for QA automation, AI dataset publishing, and API prototyping from initial planning through execution and reporting.

This skill implements the House of Sak's systematic 4-phase delivery approach: Plan → Execute → Measure → Improve. See `references/systematic-approach.md` for detailed framework.

When updating website content to reflect this systematic approach, refer to `references/website-content-strategy.md` for implementation guidelines and content strategy.

## When to Use
- When asked to "create a production plan" or "develop a service delivery schedule" for QA automation, AI datasets, or API prototypes
- When needing to "analyze service delivery costs" or "optimize project timeline" for technical services
- When requesting to "generate a client project report" or "track performance metrics" for development work
- When asked to "evaluate service efficiency" or "assess resource usage" for AI/development projects
- When needing to "forecast project outcomes" or "measure service KPIs" for technical deliverables
- When planning "QA automation projects" ($200–$500 per project + $50–$150/month retainer)
- When scoping "Hugging Face dataset publishing" projects ($300–$800 per dataset + ~$100/month)
- When estimating "Local API prototyping" work ($150–$400 prototype + $40–$102/month)
- When implementing systematic 4-phase delivery approach: Plan → Execute → Measure → Improve

## Prerequisites
- Basic understanding of the House of Sak service offerings (QA Automation, AI Dataset Publishing, API Prototyping)
- Access to project data (costs, timelines, client requirements, service scope)
- Spreadsheet or database access for data storage and analysis
- Calculator or computational tool for financial calculations
- Familiarity with the Sak agent system and zero-cost operational model

## How to Run
Invoke through the `terminal` tool with appropriate commands for data analysis, use `execute_code` for Python-based calculations with the house-of-sak-calculator.py script, or use the provided templates for planning and reporting. For client projects, follow the House of Sak service plan template and generate reports using the service metrics calculator.

When implementing website updates or other content changes:
1. Apply changes to the local repository
2. Commit with clear, descriptive messages
3. When direct push to GitHub fails due to authentication issues, create patch files using `git format-patch`
4. Generate README documentation explaining the changes and how to apply them
5. Test changes locally before creating patches
6. Maintain consistent branch naming conventions and use feature branches for significant changes

Implement the systematic 4-phase delivery approach:
1. **Plan** - Use the appropriate service plan template to define scope and objectives
2. **Execute** - Deploy Sak agents to implement the service delivery plan
3. **Measure** - Track KPIs using the House of Sak calculator and monitoring tools
4. **Improve** - Analyze outcomes and document lessons learned for future projects

Use the systematic-approach-helper.py script to generate phase-specific checklists for any service type.

## Quick Reference
- Service Plan Template: Define scope, resources, timeline, costs for QA, AI, or API services
- Cost Analysis: Material (cloud) + Labor (agents) + Overhead (zero) + Equipment (zero)
- Timeline Metrics: Start date, end date, milestones, critical path aligned with Sak Cycle
- Performance Metrics: Efficiency, quality rates, client satisfaction, on-time delivery
- Usage Metrics: Resource utilization, capacity planning, Sak agent workload
- Service Types: QA Automation (€200-500), AI Dataset Publishing (€300-800), API Prototyping (€150-400)
- Reporting Format: Executive summary, KPI dashboard, client value metrics, recommendations
- Systematic Approach: Plan → Execute → Measure → Improve framework for all service deliveries

## Procedure
1. **Plan** - Define service scope and client objectives using the House of Sak service plan template. Identify required resources (Sak agents, cloud services, tools) for the specific service type. Create detailed timeline with milestones aligned to the 6-stage Sak Cycle (Dream → Hope → Care → Joy → Trust → Growth).
2. **Execute** - Implement the service delivery plan with the appropriate Sak agents. Coordinate resources and ensure all team members understand their roles and responsibilities.
3. **Measure** - Track performance and usage metrics specific to the service type (QA, AI, or API). Calculate all associated costs including cloud service buffers and zero-cost agent labor. Generate real-time status updates and progress reports.
4. **Improve** - Analyze outcomes and provide recommendations for continuous improvement. Document lessons learned and update processes for future projects. Develop monitoring and reporting framework using the House of Sak calculator.
5. **Document and Version Control** - Maintain detailed documentation for each phase of every project. Use version control for all client deliverables and internal documentation. Create patch files when direct repository pushes encounter authentication issues. Document changes in README files for easy offline application.

## Pitfalls
- Underestimating cloud service costs when exceeding free tiers (Hugging Face, GitHub Actions, Vercel)
- Overlooking the need for clear service boundaries to prevent scope creep
- Failing to account for dependencies between Sak agents and single points of failure (Beer's wellbeing)
- Not establishing clear metrics that align with client value rather than just technical outputs
- Ignoring seasonality or market demand fluctuations for specific service types
- Neglecting the crisis protocol and async workflows needed for business continuity
- Underpricing services due to undervaluing the unique value proposition of agent-powered delivery
- Overpromising on delivery times without accounting for the 2x time estimate buffer
- Skipping the "Measure" phase and not tracking key performance indicators throughout the project
- Failing to document lessons learned during the "Improve" phase for future projects
- Not properly coordinating between Sak agents during parallel execution phases
- Encountering GitHub authentication issues when pushing website updates directly
- Failing to create patch files for offline application when direct repository access is unavailable

## Verification
Run a sample calculation using the house-of-sak-calculator.py script with known data points to verify accuracy of cost calculations and timeline estimates. Confirm that all metrics are measurable and aligned with client value. Test the service plan template with a real project scenario to ensure all necessary elements are covered.
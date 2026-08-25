"""Pre-defined standard multi-agent workflows for the Sak Family."""

from __future__ import annotations

from .models import PipelineDefinition, PipelineStep

FEATURE_DELIVERY = PipelineDefinition(
    name="feature-delivery",
    description="End-to-end feature delivery: Architect (SakThai) -> Dev (SakKing) -> Review (SakSee) -> CI/Verification (SakJules)",
    steps=(
        PipelineStep(
            name="plan",
            persona="sakthai",
            prompt_template=(
                "You are SakThai, Lead Architect. Formulate an architectural specification "
                "and concrete implementation plan for the following task:\n\n{task}"
            ),
            output_key="plan",
            max_iterations=8,
        ),
        PipelineStep(
            name="implementation",
            persona="sakking",
            prompt_template=(
                "You are SakKing, Senior Developer. Implement the code changes required "
                "to fulfill this plan.\n\nTask:\n{task}\n\nArchitectural Plan:\n{plan}"
            ),
            output_key="code",
            max_iterations=10,
        ),
        PipelineStep(
            name="review",
            persona="saksee",
            prompt_template=(
                "You are SakSee, Quality & Security Reviewer. Perform a rigorous code and "
                "design review of the plan and implementation.\n\nPlan:\n{plan}\n\n"
                "Implementation Result:\n{code}"
            ),
            output_key="review",
            max_iterations=8,
        ),
        PipelineStep(
            name="verification",
            persona="sakjules",
            prompt_template=(
                "You are SakJules, Master of Automation & CI/CD. Review the implementation "
                "and code review feedback, then formulate test & verification coverage.\n\n"
                "Review Feedback:\n{review}\n\nImplementation:\n{code}"
            ),
            output_key="verification",
            max_iterations=8,
        ),
    ),
)

CODE_REVIEW = PipelineDefinition(
    name="code-review",
    description="Multi-agent review: Scoping (SakThai) -> In-depth Security/Quality Review (SakSee) -> CI Testing (SakJules)",
    steps=(
        PipelineStep(
            name="scope",
            persona="sakthai",
            prompt_template="Scope review requirements and risks for:\n\n{task}",
            output_key="scope",
            max_iterations=6,
        ),
        PipelineStep(
            name="review",
            persona="saksee",
            prompt_template=(
                "Conduct deep code review and security inspection based on the scope.\n\n"
                "Task:\n{task}\n\nScope:\n{scope}"
            ),
            output_key="review",
            max_iterations=8,
        ),
        PipelineStep(
            name="verification",
            persona="sakjules",
            prompt_template="Assess verification and test coverage recommendations for:\n\n{review}",
            output_key="verification",
            max_iterations=6,
        ),
    ),
)

RESEARCH_BRIEF = PipelineDefinition(
    name="research-brief",
    description="Collaborative research: Framing (SakThai) -> Market/Domain Investigation (SakSit) -> Critique & Synthesis (SakSee)",
    steps=(
        PipelineStep(
            name="framing",
            persona="sakthai",
            prompt_template="Frame key hypotheses, questions, and goals for:\n\n{task}",
            output_key="framing",
            max_iterations=6,
        ),
        PipelineStep(
            name="investigation",
            persona="saksit",
            prompt_template=(
                "Perform domain research and structured analysis addressing:\n\n{framing}"
            ),
            output_key="research",
            max_iterations=8,
        ),
        PipelineStep(
            name="synthesis",
            persona="saksee",
            prompt_template=(
                "Synthesize and critique research findings into actionable recommendations:\n\n{research}"
            ),
            output_key="synthesis",
            max_iterations=6,
        ),
    ),
)

DAILY_SYNC = PipelineDefinition(
    name="daily-sync",
    description="Cross-persona observation consolidation and sync report across all family memory shards",
    steps=(
        PipelineStep(
            name="sync",
            persona="sakthai",
            prompt_template=(
                "Query family memories and synthesize high-level progress, recent observations, "
                "and outstanding blockers across all personas. Goal: {task}"
            ),
            output_key="sync_report",
            max_iterations=8,
        ),
    ),
)

BUILTIN_PIPELINES: dict[str, PipelineDefinition] = {
    FEATURE_DELIVERY.name: FEATURE_DELIVERY,
    CODE_REVIEW.name: CODE_REVIEW,
    RESEARCH_BRIEF.name: RESEARCH_BRIEF,
    DAILY_SYNC.name: DAILY_SYNC,
}

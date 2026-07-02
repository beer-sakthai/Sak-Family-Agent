---
name: generate-pitch-deck
description: "Generate a 5-slide pitch deck from a one-sentence idea."
version: 1.1.0
author: Hermes Agent (inspired by powerpoint and sketch)
license: MIT
platforms: [linux, macos, windows]
metadata:
  sakthai:
    tags: [pitch-deck, presentation, powerpoint, startup, business, ideation]
    related_skills: [powerpoint, sketch, economic-moat-diagnosis-and-strengthening]
---

# Generate 5-Slide Pitch Deck

Transform a one-sentence idea into a compelling 5-slide pitch deck, perfect for initial validation and sharing.

**Core principle:** A great pitch tells a simple, powerful story. We structure this story across five core slides: The Problem, The Solution, The Business Model, The Team, and The Opportunity.

## When to Use

Trigger this skill when the user provides a single-sentence idea and asks to create a presentation, for example:

- "Make a pitch deck for 'an app that uses AI to create personalized bedtime stories for kids'."
- "Generate a 3-slide pitch for 'a subscription box for rare indoor plants'."
- "/pitch 'a service that connects local farmers directly with restaurants'."

## The Process

### Phase 1 — Deconstruct the Idea

First, take the user's one-sentence idea and expand it. Use your own reasoning to brainstorm and outline the core components.

**Input:** "An app that uses AI to create personalized bedtime stories for kids."

**Internal Monologue / Scratchpad:**
>
> - **Product:** AI-powered mobile app.
> - **Target User:** Parents of young children (ages 3-8).
> - **Problem to Solve:** Parents are busy, run out of stories, or want more engaging, personalized content for their kids. Generic stories can be boring.
> - **Core Feature:** Generates unique stories based on child's name, interests (e.g., dinosaurs, space), and desired themes (e.g., bravery, friendship).
> - **Why Now?:** Generative AI is now powerful and accessible enough to create high-quality, safe content on the fly. Parents are more tech-savvy and looking for custom experiences.
> - **Potential Market:** Digital parenting tools, educational apps, entertainment.

This expanded context is crucial for the next phase.

### Phase 2 — Delegate Slide Content Generation (Parallel)

Like the `sketch` skill generates multiple designs, we will generate the content for each of the five slides in parallel using `delegate_task` in batch mode. Each sub-agent is a specialist focused on a single slide.

Give each sub-agent the original idea and the expanded context from Phase 1. Instruct them to return only the content for their slide in a structured format (Title, Body, Visual Idea).

**Slide 1 Agent — The Problem Specialist**
> **Goal:** Define the problem. Your slide must grab the audience's attention by highlighting a relatable pain point.
>
> - **Title:** A short, punchy headline stating the problem.
> - **Body:** 2-3 bullet points explaining who has the problem, why it's frustrating, and what current solutions are lacking. Keep it concise.
> - **Visual Idea:** Suggest a simple, evocative image or icon that represents the problem (e.g., "A tired parent yawning," "A bookshelf overflowing with the same few books").

**Slide 2 Agent — The Solution Specialist**
> **Goal:** Introduce the solution. Your slide must clearly and simply explain what the product is and how it solves the problem from Slide 1.
>
> - **Title:** The name of the product, with a clear one-line benefit statement.
> - **Body:** 2-3 bullet points detailing the key features and how they directly address the user's pain points.
> - **Visual Idea:** Suggest a visual that shows the product in action (e.g., "A mockup of the app interface showing a story being generated," "An icon of a magic wand creating a book").

**Slide 3 Agent — The Business Model Specialist**
> **Goal:** Explain how this idea makes money. Your slide must be simple and clear.
>
> - **Title:** A clear headline like "Our Business Model" or "Simple, Sustainable Revenue".
> - **Body:** 2-3 bullet points explaining the revenue model. Examples: "Freemium model with a \$5/month Pro tier," "One-time purchase of \$29.99," "Transaction fee of 2% on all sales."
> - **Visual Idea:** Suggest a simple diagram showing the revenue flow (e.g., "Icons for different subscription tiers with prices," "A simple flowchart showing user -> service -> revenue").

**Slide 4 Agent — The Team Specialist**
> **Goal:** Introduce the founding team. Since you don't know the real team, create plausible archetypes based on the idea.
>
> - **Title:** "The Right Team to Win" or "Our Founding Team".
> - **Body:** Create 2-3 placeholder team members with relevant, fictional experience. For an AI app, this might be an AI expert and a product designer. Example: "Jane Doe, CEO: 10+ years in product leadership at top tech firms." and "John Smith, CTO: PhD in AI with a focus on generative models."
> - **Visual Idea:** "Placeholder headshots for 2-3 team members."

**Slide 5 Agent — The Opportunity Specialist**
> **Goal:** Describe the opportunity and vision. Your slide must inspire confidence and create a sense of urgency or excitement.
>
> - **Title:** A forward-looking headline about the market or vision (e.g., "The Future of Storytime," "A Massive, Untapped Market").
> - **Body:** 2-3 bullet points on why this idea is timely, the potential market size, or the long-term vision. Include a clear call to action.
> - **Visual Idea:** Suggest a visual that represents growth or the future (e.g., "A simple chart showing market growth," "An illustration of a happy family reading together").

### Phase 3 — Assemble and Create the Presentation

1. **Aggregate Content:** Wait for the three sub-agents to return their structured content.
2. **Review and Refine:** As the primary agent, quickly review the content for consistency and clarity. Ensure the narrative flows logically through all five slides. Make minor edits if needed.
3. **Generate the `.pptx` file:** Use the `powerpoint` skill or a similar tool to create the presentation.

    - **Command:** `powerpoint create --file "pitch-deck.pptx" --template "minimalist"`
    - For each slide, pass the generated content:

    ```bash
    # Slide 1
    powerpoint add_slide --file "pitch-deck.pptx" \
      --title "Bedtime is a Battle for Uninspired Stories" \
      --body "Parents struggle to find new stories.\nKids lose interest in repetitive tales.\nExisting apps lack personalization." \
      --notes "Visual: Icon of a tired parent."

    # Slide 2
    powerpoint add_slide --file "pitch-deck.pptx" \
      --title "StoryWeaver: Infinite Stories, Uniquely Theirs" \
      --body "AI generates new stories on demand.\nPersonalize with your child's name and interests.\nChoose themes like courage, kindness, and adventure." \
      --notes "Visual: App mockup showing story creation."

    # Slide 3
    powerpoint add_slide --file "pitch-deck.pptx" \
      --title "Simple & Scalable Business Model" \
      --body "Freemium: 3 free stories per week.\nPro Tier: \$7/month for unlimited stories, new voices, and offline access.\nEnterprise: Licensing for schools and libraries." \
      --notes "Visual: Icons for Free, Pro, and Enterprise tiers."

    # Slide 4
    powerpoint add_slide --file "pitch-deck.pptx" \
      --title "The Perfect Team for the Job" \
      --body "Jane Doe, CEO: 10+ years in EdTech product leadership.\nJohn Smith, CTO: Ex-Google AI researcher specializing in generative text." \
      --notes "Visual: Two placeholder headshots side-by-side."

    # Slide 5
    powerpoint add_slide --file "pitch-deck.pptx" \
      --title "Redefining the $10B Digital Parenting Market" \
      --body "Generative AI makes this possible for the first time.\nOur vision is to become the go-to platform for personalized kids' content.\nCall to Action: Seeking feedback from 20 beta users." \
      --notes "Visual: A simple upward-trending graph."
    ```

4. **Deliver:** Inform the user that the 5-slide pitch deck has been created and provide them with the file `pitch-deck.pptx`.

## Pitfalls

- **Overcomplicating:** The goal is a *simple* 5-slide deck. Don't let the sub-agents add too much text. Enforce brevity.
- **Inconsistent Narrative:** The primary agent MUST review the aggregated content to ensure the story is coherent. The solution on slide 2 must directly solve the problem on slide 1.
- **Ignoring Design:** A good pitch is visual. The "Visual Idea" prompt for the sub-agents is critical. Ensure the final `.pptx` is clean, with minimal text and strong imagery, as guided by the `powerpoint` skill's design principles.

## Related

- **`powerpoint`:** The underlying skill for creating, editing, and formatting the final `.pptx` file.
- **`sketch`:** The inspiration for using parallel agents to explore different facets of a creative task.
- **`economic-moat-diagnosis-and-strengthening`:** For when the pitch progresses and needs a deeper strategic analysis.

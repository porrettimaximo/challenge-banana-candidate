---
name: feature-delivery
description: Develop Banana Bank requirements through implementation, independent verification and a reproducible submission package with original AI sessions.
---

# Deliver a Banana Bank feature
1. Intake: read docs/challenge.md and docs/contracts.md; record scope, acceptance criteria and candidate decisions in submission/requirements.md. Identify unknowns; proceed on independent work while awaiting answers.
2. Discovery: inspect UI, agent, bank integration, documents and tests. Distinguish static findings from reproduced defects. Treat simulator/ as external.
3. Design: map each acceptance criterion to observable tests. Define state transitions and evidence before implementing financial operations. Use server session identity and stable bank references.
4. Implement: use .agents/roles/implementer.md for bank changes and .agents/roles/agent-builder.md for support/agent changes. Delegate only disjoint files; coordinator integrates UI/API. Read installed Next.js guides first.
5. Verify: run public and new integration tests, typecheck, build and browser demonstration. Review using .agents/roles/reviewer.md. Fix material findings and repeat affected checks.
6. Release: use .agents/roles/release.md. Document actual changes, reproduction steps, test results, limitations and original session locations. Produce one ZIP excluding dependencies, build output, local databases, credentials and Git history. Extract to a fresh folder and validate the package. Upload/push or send email only with a known destination and human authorization; otherwise produce a locally reviewable package and exact submission instructions.
7. Handoff: append real execution evidence to submission/workflow-log.md. Refresh original session copies immediately before final packaging and provide a command to refresh after the final assistant turn.

Do not invent authorship, completed tests, screenshots, bank outcomes or deployment. The candidate designed and requested the workflow; generated artifacts were created with AI assistance. Role files are reusable prompts, not automatically registered native agents.


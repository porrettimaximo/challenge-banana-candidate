# Banana Bank development workflow

Read .agents/skills/feature-delivery/SKILL.md for application development. The candidate defines requirements and priorities; AI agents implement and verify with recorded evidence. Follow docs/contracts.md. Never change simulator behavior to fix application failures. Preserve original AI session exports.

## Delegation
Use role instructions in .agents/roles/. Assign disjoint files to implementation agents. The coordinator owns requirements, integration, release and submission. The reviewer must independently inspect implementation and tests before release. Record real results in submission/workflow-log.md; do not mark planned work completed.

## Next.js
Before changing Next.js code, read relevant installed guides in node_modules/next/dist/docs/. Preserve existing HTTP contracts or document equivalent adapters.

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->


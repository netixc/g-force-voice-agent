# Chief OS Product Direction

## Product Statement

Talk to one agent: Ava, the Chief of Staff. Ava can use tools, delegate work to specialized background Pi agents, show their progress, and let the user communicate directly with a Pi agent when an intermediary is unnecessary.

Chief OS is the product and repository name. Ava remains the working name for the Chief-of-Staff persona and may change later.

## Roles

### Ava — Chief of Staff

- Acts as the primary voice-and-text interface.
- Handles the user-facing conversation and delegates substantive work.
- Can use Chief-of-Staff tools directly as they are added.
- Does not need autonomous multi-step planning yet, but the architecture should allow it later.
- Presents delegated task status, progress, and results.

### Primary Pi agent

- Handles coding, research, files, terminal work, and general delegated tasks.
- Receives only the task context and files Ava or the user explicitly provides in the target architecture.
- Can delegate bounded work to specialized, temporary Pi workers.
- Can be opened for direct user communication without Ava relaying each message.

### Background Pi workers

- Are created temporarily for delegated tasks.
- May use specialized roles such as coder, researcher, or reviewer.
- Report progress and results through the task interface.

## Target User Experience

- Keep the main voice-and-text conversation with Ava.
- Show a task and activity panel with worker status and progress.
- Allow the user to open a delegated task and chat directly with its Pi agent.
- Provide a Pi workspace for starting a direct session without first asking Ava.
- Keep Ava and Pi context isolated by default; Pi receives explicit task context and file attachments rather than Ava's entire conversation.

## Deployment and Data

- Support a complete local deployment first.
- Add a hosted or hybrid deployment option later.
- Keep speech recognition and synthesis on the user's local GPU in either mode.
- Optimize for one user initially.
- Long-term personal memory is not a current priority.

## Authority and Approval

Ava may execute configured non-purchase actions without an approval prompt. Any future action that makes a purchase must require explicit user approval. The current prototype has no purchase tool or browser approval interface.

## Current Prototype Gaps

The current implementation is an earlier stage of this direction:

- Ava directly uses only delegation and cancellation tools.
- The Pi service exposes sanitized progress events, but the browser does not yet provide the task panel, worker activity interface, or direct Pi chat.
- One persistent primary Pi session serves each voice connection and may create ephemeral workers.
- Pi can access the configured `workspace/` mount according to its enabled tools; per-task file handoff is not implemented.
- Docker Compose provides the local GPU deployment. A hosted/local-GPU split is not implemented.

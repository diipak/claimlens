# ClaimLens — Brutal Review and Corrected Implementation Plan

## Brutal self-critique of the proposed plan

The original plan was **workable but not disciplined enough**. It had several good instincts, but it also contained the exact kinds of seductive mistakes that make AI-built hackathon projects look polished while being structurally weak.

### What was good
- React + TypeScript + Vite is a fast, sensible frontend choice for a mobile-first demo.
- Express + TypeScript is enough for a thin orchestration backend.
- Using Gemini through Google Cloud / Vertex AI is the correct direction for hackathon alignment and credit usage.[1][2]
- Elastic-backed retrieval is the right partner fit because this product is fundamentally an evidence retrieval and ranking system.[3][4]
- The three demo scenarios are the right scope anchor.

### What was weak or self-deceptive

#### 1. The UI language drifted into trendiness
Words like “premium,” “glassmorphic,” and “smooth animations” are not harmless. For this product they are a trap. Claim verification must look **credible, legible, and evidence-first**, not stylish in a way that weakens trust. The original UI language risked building a demo that looks like a fintech landing page instead of a serious verification tool.

**Correction:** Use a clean, high-contrast, mobile-first interface with restrained motion and strong typography. No glassmorphism.

#### 2. Gemini-as-OCR was framed too confidently
Using Gemini multimodal for screenshot reading can be practical, but the original plan treated it like a superior OCR replacement. That is risky. If the same model both reads the screenshot and verifies the claim, the system can collapse extraction errors into reasoning errors and make them look authoritative.

**Correction:** Screenshot ingestion is allowed, but the app must visibly show:
- raw extracted text,
- the final extracted claim,
- and a warning that screenshot extraction may be incomplete.

This is non-negotiable.

#### 3. The Elastic fallback was too comfortable
A local JSON/SQLite fallback is useful for development, but the original wording made it too easy for the final demo to run mostly without Elastic. That would weaken the entire partner-track story, because the hackathon requires meaningful use of the partner MCP server.[3]

**Correction:** Local fallback is for offline development and automated tests only. The final demo path must use a real Elastic Cloud Serverless setup with Agent Builder and MCP exposure.[3][5]

#### 4. Google Cloud Agent Builder was not explicit enough
The plan leaned heavily on a custom Express backend and direct Gemini SDK usage. That may work technically, but it risks sounding like a standard web app that happens to call Gemini. The hackathon expects a functional agent built with Gemini and Google Cloud Agent Builder, plus a partner MCP server.[6][7]

**Correction:** The architecture and demo narrative must explicitly include Google Cloud Agent Builder as part of the agent story, with Elastic MCP as the retrieval/tool layer.

#### 5. The stack boundaries were still underspecified
The original plan did not clearly lock deployment and service boundaries. That invites Antigravity to overbuild.

**Correction:** Explicitly constrain services: Cloud Run for backend, Vertex AI / Gemini for reasoning, Elastic Cloud Serverless for retrieval, optional Cloud Storage for temporary screenshot handling, and no unnecessary extra services unless approved.

### Bottom-line judgment
The original plan was approximately:
- **70% solid**
- **20% vague**
- **10% dangerous**

The dangerous parts were exactly the parts most likely to produce hackathon theater instead of a trustworthy product: trendy UI, overtrusted screenshot extraction, and a weakly enforced Elastic integration.

***

# Final corrected implementation plan — ClaimLens

Build a **mobile-first responsive web app** called **ClaimLens** for the Google Cloud Rapid Agent Hackathon. The app verifies **numeric, ranking, and temporal public claims** using a **Gemini-powered verification backend on Google Cloud** and a **real Elastic retrieval layer** exposed via Agent Builder / MCP-compatible tools.[6][3][5]

The product must be **evidence-first, transparent, and narrow in scope**. It checks **one claim at a time** and is designed for fast use on mobile.

***

## User Review Required

> [!IMPORTANT]
> **Proposed corrected tech stack & architecture**
> 1. **Frontend:** React + TypeScript + Vite.
> 2. **UI approach:** mobile-first, high-contrast, trust-first interface; no glassmorphism, no decorative noise, minimal motion.
> 3. **Backend:** Express + TypeScript, deployed on Cloud Run.
> 4. **Model layer:** `@google/genai` using Vertex AI configuration with explicit Google Cloud project and location.[1][2]
> 5. **Screenshot ingestion:** Gemini multimodal extraction is allowed, but raw extracted text must be shown to the user before/alongside verification.
> 6. **Retrieval layer:** Real Elastic Cloud Serverless project with Agent Builder enabled; primary demo path must use Elastic retrieval over indexed curated sources.[3][4]
> 7. **Partner integration:** Elastic MCP / Agent Builder retrieval must be materially important to the demo, not cosmetic.[3][5]
> 8. **Local fallback:** Local JSON fallback may exist for local development and tests only, but not as the primary demo path.

***

## Open questions that must be answered before build proceeds

> [!NOTE]
> 1. **Elastic environment:** Do you already have an Elastic Cloud Serverless project, or should setup be included as part of the initial implementation steps?[3]
> 2. **Google Cloud project:** Confirm the exact GCP project ID and region to use for Vertex AI / Cloud Run.
> 3. **Demo corpus:** Should we seed only the 3 required demo scenarios first, or also add 5–10 extra backup claims for testing?
> 4. **Screenshot handling:** Should uploaded screenshots be stored temporarily in Cloud Storage, or processed in-memory and discarded immediately?

***

## Product constraints

The implementation must obey these boundaries:
- Verify **one claim at a time**.
- Focus only on **numeric, ranking, and temporal claims** in MVP.
- Support screenshot upload only as a **text extraction + same verification pipeline** path.
- Do **not** attempt deepfake detection, image forensics, or identity verification from image alone.
- Do **not** attempt a general fake-news platform.
- Do **not** build accounts, feeds, community workflows, or social posting.

***

## Corrected project structure

```text
GeminiAgent_hackathon/
├── package.json
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── App.css
│   └── components/
│       ├── InputCard.tsx
│       ├── ResultCard.tsx
│       ├── SourceList.tsx
│       ├── WarningBlock.tsx
│       └── StepStatus.tsx
├── server/
│   ├── index.ts
│   ├── agent.ts
│   ├── search.ts
│   ├── schema.ts
│   └── prompts.ts
├── database/
│   └── curated_sources.json
├── scripts/
│   └── test-scenarios.ts
└── idea.md
```

Add `schema.ts` and `prompts.ts` so the output format and anti-hallucination instructions are not buried in one large file.

***

## Component 1 — dependencies and configuration

### [MODIFY] `package.json`

Use a simple workspace configuration with scripts for frontend and backend.

### Required dependencies
- `react`
- `react-dom`
- `typescript`
- `vite`
- `express`
- `cors`
- `dotenv`
- `@google/genai`
- `lucide-react`

### Dev dependencies
- `tsx`
- `concurrently`
- `@types/express`
- `@types/cors`
- `@types/node`

### Notes
- Do **not** add unnecessary state libraries, database ORMs, CSS frameworks, or animation libraries in MVP.
- Keep the dependency graph small to reduce Antigravity drift.

***

## Component 2 — backend orchestration (`server/`)

### [NEW] `server/index.ts`
Create an Express server running on port `3001`.

#### Endpoints
- `POST /api/verify`
  - Accepts either:
    - a text claim, or
    - a screenshot image payload.
  - Executes the flow:
    1. screenshot text extraction if needed,
    2. claim extraction,
    3. claim typing,
    4. evidence retrieval,
    5. verification reasoning,
    6. structured response.

- `GET /api/health`
  - Returns service health and basic environment readiness.

### [NEW] `server/schema.ts`
Define strict TypeScript response types.

#### Required response schema
```ts
{
  extractedText?: string,
  extractedClaim: string,
  claimType: 'Numeric' | 'Ranking' | 'Temporal' | 'Mixed',
  verdict: 'Supported' | 'Misleading' | 'Projected as current' | 'Outdated' | 'Unsupported' | 'Unresolved',
  why: string[],
  confidence: 'Low' | 'Medium' | 'High',
  warnings: string[],
  sources: Array<{
    title: string,
    domain: string,
    tier: 1 | 2 | 3,
    date: string,
    url: string,
    snippet: string
  }>
}
```

### [NEW] `server/prompts.ts`
Store all system instructions separately.

Prompt rules must enforce:
- one atomic claim only,
- controlled verdict vocabulary,
- no invented sources,
- downgrade to unresolved when evidence is weak,
- explicit checks for projection vs present, outdated vs current, ranking-basis mismatch, estimate vs final, missing timeframe.

### [NEW] `server/agent.ts`
Initialize Gemini using the Google Gen AI SDK with Vertex AI settings.[1][2]

Example direction:
```ts
import { GoogleGenAI } from '@google/genai';

const ai = new GoogleGenAI({
  vertexAI: true,
  project: process.env.GOOGLE_CLOUD_PROJECT,
  location: process.env.GOOGLE_CLOUD_LOCATION || 'us-central1'
});
```

#### Model guidance
- Use a fast Gemini model for extraction / orchestration.
- Use a stronger Gemini model only if needed for final reasoning.
- Keep token usage disciplined.

#### Important behavior
- If screenshot input is provided, first return/retain **raw extracted text**.
- The final response must distinguish between:
  - extracted text,
  - extracted claim,
  - verdict.

### [NEW] `server/search.ts`
Implement the retrieval layer.

#### Primary path
- Query a real Elastic-backed index of curated sources.
- Use Elastic Agent Builder / MCP-connected retrieval where possible for the demo path.[3][5]

#### Secondary path
- Local JSON search over `database/curated_sources.json`.
- This exists only for:
  - local development,
  - unit tests,
  - offline fallback.

#### Rule
If the app is being prepared for final demo submission, the Elastic path must be enabled and used.

***

## Component 3 — source corpus seed (`database/`)

### [NEW] `database/curated_sources.json`
Seed a **small but high-quality** dataset covering the core demo scenarios.

Include fields:
- `title`
- `domain`
- `tier`
- `date`
- `url`
- `content`
- `scenarioTag`

### Initial scenarios to seed
1. **Projection framed as current fact**
   - Example: a forecast or target year reworded as already achieved.

2. **Ranking ambiguity**
   - Example: ranking without basis, or PPP presented as nominal.

3. **Screenshot-extracted numeric claim**
   - Example: screenshot text containing a stat that must be checked against the indexed source.

### Recommendation
Seed at least:
- 3 primary-source records,
- 3 secondary-source records,
- 2 contextual records,
for each scenario if possible.

***

## Component 4 — frontend (`src/`)

### [MODIFY] `src/App.tsx`
Build a simple mobile-first single-page app.

#### Required states
1. **Input state**
   - claim text area
   - screenshot upload
   - sample scenario buttons
   - short explanation of what claim types are supported

2. **Checking state**
   - step-based progress:
     - Extracting text
     - Finding claim
     - Retrieving evidence
     - Comparing sources
     - Preparing verdict

3. **Result state**
   - extracted text (if screenshot)
   - extracted claim
   - verdict chip
   - confidence chip
   - why bullets
   - warnings
   - source cards grouped/listed with date and tier

### [MODIFY] `src/App.css`
Use:
- high contrast,
- clean spacing,
- readable typography,
- mobile-first layout,
- subtle motion only for loading/progress.

Do not use:
- glassmorphism,
- blur-heavy cards,
- noisy gradients,
- decorative animations that reduce seriousness.

***

## Elastic integration plan

This is the preferred hackathon path and should be treated as first-class.

### Step 1
Create an **Elastic Cloud Serverless** project in a Google Cloud region.[3]

### Step 2
Enable **Agent Builder** in Kibana.[3][4]

### Step 3
Create or import tools for retrieving curated source records.

### Step 4
Expose those tools through Elastic’s built-in MCP server endpoint.[5]

### Step 5
Connect the verification flow so the app’s evidence retrieval uses Elastic-backed tools for the real demo path.

### Security notes
- Use API keys with expiration.
- Restrict index access to only the source indices needed by ClaimLens.[5]

***

## Google Cloud usage plan

### Required services
- Vertex AI / Gemini for extraction + reasoning.
- Cloud Run for backend deployment.
- Optional Cloud Storage for temporary screenshot handling.

### Constraints
- Do not add BigQuery, Pub/Sub, Firestore, or extra services unless a concrete need emerges.
- Keep the backend stateless in MVP if possible.
- Pass project ID and location from environment variables.

***

## Verification plan

### Automated tests
Create `scripts/test-scenarios.ts` that checks:
- health endpoint works,
- text claim path returns schema-valid output,
- screenshot path returns extracted text,
- verdict is one of the controlled values,
- each seeded scenario returns the expected shape.

### Manual verification
- Verify mobile layout in browser device emulation.
- Verify at least one case returns **Projected as current**.
- Verify at least one case returns **Misleading** due to ranking basis mismatch.
- Verify at least one screenshot case surfaces raw extracted text and a screenshot warning.
- Verify at least one case returns **Unresolved** honestly.

***

## Final implementation instructions for Antigravity

Build ClaimLens as a **mobile-first responsive web app** with:
- React + TypeScript + Vite frontend,
- Express + TypeScript backend,
- Gemini via `@google/genai` configured for Vertex AI,
- Elastic-backed retrieval as the primary demo path,
- local JSON fallback for development only,
- strict structured output schema,
- raw screenshot text surfaced to the user,
- and a trust-first UI.

Do not expand beyond MVP.
Do not add chat-style assistant behavior.
Do not invent sources.
Do not let the local fallback replace the real Elastic demo path.
Do not use decorative visual patterns that reduce trust.
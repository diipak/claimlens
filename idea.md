# ClaimLens — Antigravity Build Artifact

## Product intent
Build a **mobile-first web app** for verifying **one claim at a time**.

The app focuses on **numeric, ranking, and temporal public claims**, plus **limited screenshot OCR support**. It must return an **evidence-backed verdict** with a transparent source list, not a generic AI opinion. The product is intended for social-media users who want to check a claim before believing or sharing it.

This project should be framed as a **functional agent** for the Google Cloud Rapid Agent Hackathon, which requires a real agent built with Gemini + Google Cloud Agent Builder and a meaningful partner MCP integration.[1][2]

## Core problem
Public misinformation often spreads by using:
- Future projections presented as current fact.
- Numeric claims without denominator, basis, or timeframe.
- Ranking claims without clarifying nominal vs PPP, old vs latest, estimate vs final.
- Screenshots that strip context, date, or original source.

The product should help users answer:

**“What exactly is this claim, what is the strongest available evidence, and is the wording supported or misleading?”**

## What the product is
ClaimLens is:
- A mobile-first verification agent.
- A single-claim checker.
- Evidence-first, not opinion-first.
- Transparent about sources and uncertainty.
- Strictly scoped to numeric/ranking/temporal claims in MVP.
- Able to ingest screenshot text through OCR and send it through the same claim-checking pipeline.

## What the product is not
ClaimLens is **not**:
- A general fake news detector.
- A “truth engine” for all politics.
- A deepfake detector.
- A video verification tool.
- A bot network detector.
- A social-media monitoring platform.
- A civic complaint app.
- A crowdsourced moderation system.
- A tool that posts back to social platforms.

Do not let the build drift into these directions.

## Primary users
- Mobile-first social media users.
- Gen Z / young audiences exposed to viral claims, screenshots, and “data-backed” narratives.
- Users who want a quick trust check before sharing a claim.

## User inputs in MVP
Support only:
- Pasted text claim.
- Short paragraph containing one main claim.
- Uploaded screenshot with text.
- Optional URL paste only if easy and stable.

Do **not** support in MVP:
- Video upload.
- Audio upload.
- Bulk claim analysis.
- User accounts as a dependency.
- Full multilingual promise.
- Social scraping from multiple platforms.

## Supported claim types
The app should work well only for these claim types:

### 1) Numeric claims
Examples:
- percentages
- counts
- totals
- budget numbers
- follower counts
- economic figures

### 2) Ranking claims
Examples:
- “5th largest economy”
- “number 1 state”
- “highest unemployment”
- “top-ranked”

### 3) Temporal/projection claims
Examples:
- forecast presented as achieved fact
- old data framed as current
- estimate framed as final
- outdated ranking presented as latest

### 4) Screenshot-extracted claims
- OCR the screenshot.
- Extract the text claim.
- Send it through the same pipeline.
- Add limited screenshot warnings such as missing source/date/context.

## Non-supported claim types in MVP
Do not support:
- identity verification from image alone
- deep image forgery detection
- deepfakes
- speech verification
- multi-claim debate threads
- sentiment, ideology, or intent analysis
- legal-defamation-sensitive identity rulings from weak evidence

## Required output schema
Every result must include these blocks:

### 1. Extracted claim
The exact claim the system is checking.

### 2. Claim type
One of:
- Numeric
- Ranking
- Temporal
- Mixed

### 3. Verdict
Use only this controlled vocabulary:
- Supported
- Misleading
- Projected as current
- Outdated
- Unsupported
- Unresolved

Never use loose labels like “true” or “fake”.

### 4. Why
- 2 to 4 evidence bullets.
- Plain language.
- No fake chain-of-thought.

### 5. Sources
Show every source with:
- title
- domain / publisher
- source tier
- date
- clickable link

### 6. Confidence
Only:
- Low
- Medium
- High

No fake numerical confidence like 92%.

### 7. Warnings
Examples:
- Original source not found.
- Only secondary sources found.
- Claim wording is broader than source wording.
- Ranking basis is ambiguous.
- Screenshot context incomplete.

## Verification workflow
The app should follow this exact flow:

1. Accept text or screenshot input.
2. OCR if screenshot.
3. Extract one atomic claim.
4. Classify claim type.
5. Generate retrieval query.
6. Retrieve evidence from curated sources.
7. Compare claim wording to evidence.
8. Check for manipulation patterns.
9. Produce verdict.
10. Show evidence, sources, confidence, and warnings.

If the system cannot reliably complete steps 3, 6, or 7, return **Unresolved**.

## Manipulation patterns to detect in MVP
The reasoning layer should explicitly check for:
- projection vs present fact
- outdated vs latest
- estimate vs final value
- nominal vs PPP / basis mismatch
- missing denominator or timeframe
- source overstatement
- ranking category mismatch
- screenshot with missing context

## Source transparency policy
The app must use a **curated source policy**, not arbitrary open-web trust.

### Tier 1 — Primary
- official reports
- court documents
- regulator releases
- international institution reports
- primary datasets
- original published methodology/report source

### Tier 2 — Reputable secondary
- established journalism
- recognized fact-checkers
- policy/academic explainers that cite primary material

### Tier 3 — Context
- archived pages
- prior discussions
- contextual references

Rules:
- Prefer Tier 1 whenever available.
- Never give a strong verdict from Tier 3 alone.
- If only Tier 2 exists, label that clearly.
- If evidence conflicts, downgrade to Unresolved or explain the conflict.
- Always show source dates.

## MCP partner requirement
Use **Elastic** as the partner MCP integration.

Reason:
The product’s core value is transparent evidence retrieval and ranking. Elastic’s MCP server connects agents to Elasticsearch indices and supports search, mappings, and ES|QL queries over indexed evidence, making retrieval central rather than cosmetic.[3][4][5]

### MCP design requirement
- Elastic MCP must be materially important to the product.
- The app should retrieve evidence from indexed sources via Elastic-backed search.
- Gemini should reason over retrieved evidence, not replace the evidence layer.
- The demo should make it obvious that the verification agent relies on retrieval over a curated corpus.

## Platform requirement
Build as a **mobile-first responsive web app**.

Rationale:
The target audience is mobile/social-first, while the hackathon accepts web apps and requires a functional public demo.[1][2]

### Device priority
1. Mobile web first.
2. Desktop web second.

## UX requirements
The UI should be:
- clean
- fast
- trustable
- slightly attractive
- serious enough to feel credible
- simple enough for quick checking

### Required screens
1. Home / input screen.
2. Checking state.
3. Result screen.
4. Expandable source detail view.

### Trust cues
Include:
- verdict chip
- confidence chip
- source tier badges
- source dates
- “how this was checked” microcopy
- visible warning state when evidence is weak

Do not include:
- mascot/avatar assistant
- chatty AI persona
- heavy animations
- excessive gamification
- decorative noise that weakens trust

## Failure behavior
The app must **gracefully refuse** when confidence is weak.

Return **Unresolved** or **Unsupported** when:
- no reliable source exists
- OCR is incomplete
- claim is too broad
- ranking basis is ambiguous
- source dates conflict
- the evidence only partially matches the wording

In those cases, explain what is missing.

## Anti-hallucination rules
These rules are mandatory:
- Never invent sources.
- Never invent report titles.
- Never give a verdict without evidence objects.
- Never hide weak evidence.
- Never verify more than one atomic claim at a time.
- Never merge two separate claims silently.
- Never overstate certainty.
- Never say “true” / “false” as the main product language.
- Never pretend screenshot OCR is perfectly reliable.
- Never use arbitrary web results without source-tier labeling.

## MVP exclusions
Explicitly exclude from first version:
- deepfake detection
- image forensics
- bot detection
- account authenticity scoring
- social graph analysis
- crowdsourced reports/community feed
- multilingual expansion beyond basic capability
- auto-post/share-back into social media networks
- admin dashboard unless absolutely necessary for demo setup

## Demo requirements
The demo should show only 3 clear scenarios:

### Scenario 1
A future projection or possibility presented as already true.

### Scenario 2
A ranking claim with ambiguous or manipulated basis.

### Scenario 3
A screenshot claim that is OCR’d and checked through the same pipeline.

If these 3 scenarios do not work cleanly, do not add more features.

## Acceptance criteria
The MVP is acceptable only if:
- a user can paste a claim and get a structured result
- a user can upload a screenshot and the OCR path works
- sources are visible, dated, and tiered
- the verdict uses only controlled vocabulary
- at least one example correctly identifies “projection presented as current”
- at least one example correctly identifies ranking/context ambiguity
- at least one example returns Unresolved honestly
- the full flow is usable on mobile

## Build instruction for Antigravity
Build a **mobile-first responsive web app** called ClaimLens that verifies **one numeric/ranking/temporal claim at a time** from pasted text or screenshot OCR, retrieves evidence from a curated source corpus using **Elastic MCP-backed retrieval**, and returns a structured result with:
- extracted claim
- claim type
- verdict
- why
- sources
- confidence
- warnings

The app must be transparent, evidence-first, constrained, and resistant to hallucination. Do not expand beyond the MVP exclusions.
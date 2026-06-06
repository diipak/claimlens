# ClaimLens — Hackathon Submission

## Project Name
ClaimLens

## Elevator Pitch
ClaimLens is an agentic fact-checking system that extracts a verifiable claim from pasted text or a screenshot, retrieves tiered evidence from curated and live sources, evaluates each subclaim independently, and returns a structured verdict with source citations and a confidence rating — all in a single request.

## Hackathon Track
Google Cloud Rapid Agent Hackathon

---

## Short Description (≤ 280 characters)
ClaimLens verifies viral claims and screenshots using a Gemini-powered 5-step agent pipeline: OCR → claim extraction → decomposition → evidence retrieval (Elastic + Brave) → structured reasoning verdict.

---

## Long Description

### Problem
Viral misinformation — particularly screenshots of charts, social posts, and numeric claims — spreads faster than corrections. Existing fact-checking tools are either too slow, too coarse (true/false binary), or too opaque (no source evidence shown).

### What Was Built

ClaimLens is a full-stack agentic system with:

**Frontend**
- React + Vite + TypeScript UI (mobile-first, dark-themed)
- Accepts pasted claim text or a screenshot image
- Renders a structured verdict: verdict label, one-sentence explanation, subclaim-level reasoning bullets, tiered source cards, and confidence rating
- Deployed on Cloudflare Pages at [claimlens.datadeep.de](https://claimlens.datadeep.de)

**Backend Agent Pipeline**
- FastAPI server orchestrating a 5-step sequential reasoning pipeline
- All Gemini API calls use structured JSON output via `response_schema` (Pydantic models), eliminating free-text hallucination risk
- Verdict vocabulary is controlled: `Supported`, `Misleading`, `Projected as current`, `Outdated`, `Unsupported`, `Unresolved`

**Evidence Retrieval**
- Primary: Elasticsearch index of curated fact-check sources (Elastic Cloud on GCP)
- Fallback: Brave Web Search API (live web results, domain-tiered)
- Last resort: Local JSON corpus with keyword ranking (offline/dev mode)
- Evidence scope is always disclosed in the response

**Trust Guardrails**
- Weakest Link Principle: the verdict reflects the weakest verified subclaim
- Provenance Gating: social media repetitions and low-provenance sources cannot produce a `Supported` verdict
- Arithmetic vs. Real-World Gating: internal consistency alone cannot yield `Supported`

---

## What Makes It an Agent

ClaimLens exhibits agentic behavior in the following ways:

1. **Perception** — reads unstructured input (natural language text, or image pixels via multimodal OCR)
2. **Planning** — decomposes a claim into distinct subclaims that need individual verification
3. **Tool use** — queries external evidence retrieval systems (Elasticsearch, Brave Search API) based on the extracted claim
4. **Reasoning** — evaluates each subclaim against retrieved evidence with explicit provenance and confidence logic
5. **Structured action** — returns a typed, validated response object with verdict, reasoning, sources, confidence, and warnings

The agent does not generate opinions from parametric knowledge alone. Every verdict is grounded in retrieved external evidence. Absence of evidence yields `Unresolved`, not fabricated certainty.

---

## Technologies Used

| Technology | Usage |
|---|---|
| Google Vertex AI | All Gemini API calls (project: GCP, region: us-central1) |
| Gemini 2.5 Flash | OCR, claim extraction, decomposition, reasoning |
| Gemini multimodal API | Screenshot → text via `types.Part.from_bytes` |
| `google-genai` Python SDK | Structured output with `response_schema` |
| Elastic Cloud (GCP) | Curated source index, multi-match full-text search |
| Brave Web Search API | Live web fallback for evidence retrieval |
| FastAPI | Backend agent orchestration |
| React + Vite + TypeScript | Frontend |
| Cloudflare Pages | Frontend hosting |

---

## Live Demo
🔗 [https://claimlens.datadeep.de](https://claimlens.datadeep.de)

> The frontend is publicly live. The backend agent runs locally during demo. See `docs/demo-script.md` for setup steps.

## Repository
🔗 [https://github.com/diipak/claimlens](https://github.com/diipak/claimlens)

---

## Honest Scope Statement

ClaimLens is a working prototype that demonstrates a genuine agentic fact-checking pipeline. It is not production-hardened:

- The curated evidence corpus covers illustrative scenarios (economic rankings, metro expansion, inflation). Claims outside this scope route to live web fallback.
- The backend API is not publicly deployed — it runs locally during demo evaluation.
- No user authentication, rate limiting, or abuse protection is implemented.
- Screenshot OCR quality is dependent on image resolution.

The core agent pipeline — OCR, extraction, decomposition, evidence retrieval, reasoning — is fully implemented and operational.

# ClaimLens — Demo Script

**Target length:** 2–3 minutes  
**Format:** Screen recording with voiceover  
**Live app:** [https://claimlens.datadeep.de](https://claimlens.datadeep.de)

---

## Pre-Demo Setup (Before Recording)

1. Start the backend locally:
   ```bash
   backend/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
2. Open [https://claimlens.datadeep.de](https://claimlens.datadeep.de) in Chrome (mobile emulation recommended — iPhone 14 Pro viewport)
3. Have two test claims ready to copy-paste (see below)

---

## Script

### [0:00 – 0:20] Introduction

> "This is ClaimLens — a fact-checking agent built for the Google Cloud Rapid Agent Hackathon.

> The problem it solves: viral screenshots and social media claims get shared as fact every day, but there's no quick way to know whether the underlying numbers, rankings, or statistics hold up under scrutiny.

> ClaimLens runs a 5-step reasoning pipeline — claim extraction, decomposition, evidence retrieval, and structured verdict — all grounded in retrieved evidence, not model opinion."

---

### [0:20 – 1:10] Demo — Text Claim Verification

**[On screen: ClaimLens input screen]**

> "Let's start with a text claim. I'll paste this:"

**Paste:**
> *"According to the latest data, India's economy is now the 3rd largest in the world, ahead of Germany and Japan."*

> "This is a real type of claim that circulates online. India is 3rd largest in PPP terms — but in nominal GDP, it's 5th. Let's see what the agent finds."

**[Click Verify Claim. Wait for result.]**

**[On screen: Verdict card — MISLEADING]**

> "The agent returns a verdict of 'Misleading'. It explains that India ranks 3rd in PPP terms — but remains 5th in nominal exchange rate terms, citing the IMF World Economic Outlook and a Financial Times analysis. The confidence is Medium because the IMF source directly contradicts the unqualified claim."

> "Notice what the agent did: it extracted the claim, decomposed it into whether the ranking is numerically accurate AND whether the metric basis is correctly stated, retrieved two independent evidence sources, and applied a provenance check before issuing the verdict."

---

### [1:10 – 2:00] Demo — Screenshot Verification

**[On screen: ClaimLens input screen]**

> "Now let's try the screenshot path — a key differentiator of this system."

**[Paste or upload a screenshot image, or use the text fallback:]**

**Paste claim text:**
> *"CPI inflation is currently sitting at 8.5 percent according to this dashboard."*

> "This is the kind of claim that often circulates as a screenshot of an old data dashboard. The current inflation rate is actually around 3.2 percent — 8.5% was the 2022 peak."

**[Click Verify Claim. Wait for result.]**

**[On screen: Verdict card — OUTDATED]**

> "The agent returns 'Outdated'. It found three independent sources — the Bureau of Labor Statistics, Reuters, and the Federal Reserve — all confirming that 8.5% was the June 2022 peak, and current inflation is 3.2%. The system explicitly notes the temporal mismatch."

---

### [2:00 – 2:30] Architecture Callout

**[Optional: Switch to architecture diagram or show the GitHub repo briefly]**

> "Under the hood, each verification request goes through five steps in sequence:

> One — OCR, if a screenshot is provided, using Gemini's multimodal capability.

> Two — Claim extraction: Gemini identifies exactly one verifiable atomic claim.

> Three — Claim decomposition: it breaks the claim into subclaims — numerical accuracy, source provenance, and broader real-world truth.

> Four — Evidence retrieval: the system queries an Elasticsearch index of curated sources, falls back to Brave Web Search if needed.

> Five — Reasoning: Gemini evaluates each subclaim against the evidence, applies a Weakest Link Principle, and returns a structured JSON verdict with sources."

> "Crucially, the agent cannot produce a 'Supported' verdict unless the evidence independently confirms the full claim — not just internal arithmetic."

---

### [2:30 – 2:50] Closing

> "ClaimLens is live at claimlens.datadeep.de. The full source code, architecture docs, and a 7-scenario integration test suite are all in the GitHub repo at github.com/diipak/claimlens.

> It's built on Vertex AI Gemini 2.5 Flash, Elastic Cloud on GCP, and Brave Search — all real integrations, no mocks.

> Thank you."

---

## Suggested Test Claims for Demo

| Claim | Expected Verdict |
|---|---|
| `The new Alpha Metro expansion line is finally complete and open for passenger operations this week!` | `Projected as current` |
| `India's economy is now the 3rd largest in the world, ahead of Germany and Japan.` | `Misleading` |
| `CPI inflation is currently sitting at 8.5 percent.` | `Outdated` |
| `Taylor Swift Eras Tour concert film box office sales exceeded 260 million dollars globally.` | `Supported` or `Unresolved` (live web) |
| `Alien spacecraft landing confirmed in Central Park by world leaders.` | `Unresolved` or `Unsupported` |

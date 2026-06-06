from typing import List, Optional
from pydantic import BaseModel, Field

class Source(BaseModel):
    title: str = Field(..., description="Title of the source document or article")
    domain: str = Field(..., description="Domain or publisher name (e.g. WHO, BBC, IMF)")
    tier: int = Field(..., description="Source tier rating (1 = Primary, 2 = Secondary, 3 = Context)")
    date: str = Field(..., description="Publication date or timeline of the source document")
    url: str = Field(..., description="URL link to the source document")
    snippet: str = Field(..., description="Extracted relevant text snippet serving as evidence")

class VerificationResponse(BaseModel):
    extractedText: Optional[str] = Field(None, description="Raw extracted text if visual OCR path was used")
    extractedClaim: str = Field(..., description="The atomic claim identified and audited by the system")
    claimType: str = Field(..., description="Claim type classification: Numeric, Ranking, Temporal, or Mixed")
    verdict: str = Field(..., description="Audit verdict: Supported, Misleading, Projected as current, Outdated, Unsupported, or Unresolved")
    why: List[str] = Field(..., description="2 to 4 evidence bullets explaining the verdict in plain language")
    confidence: str = Field(..., description="System confidence: Low, Medium, or High")
    warnings: List[str] = Field(..., description="Methodological or context warnings (e.g. OCR limits, missing primary sources)")
    sources: List[Source] = Field(..., description="List of source evidence objects that directly substantiate the verdict")
    evidenceScope: str = Field("Curated", description="The scope of evidence sources used: Curated, Live Web, Hybrid, or None")

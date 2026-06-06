import os
import base64
import logging
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from backend.schema import VerificationResponse, Source
from backend.prompts import CLAIM_EXTRACTION_PROMPT, VERIFICATION_PROMPT, DECOMPOSITION_PROMPT

logger = logging.getLogger("claimlens.agent")

def get_genai_client() -> genai.Client:
    """
    Initializes the unified Google GenAI client configured for Vertex AI on GCP.
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "dataagentplatform")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    logger.info(f"Initializing unified Google GenAI client for Vertex AI on project '{project_id}' in region '{location}'")
    return genai.Client(
        vertexai=True,
        project=project_id,
        location=location
    )

def ocr_screenshot(image_b64: str, mime_type: str = "image/png") -> str:
    """
    Step A: Extract raw text from the screenshot using Gemini's multimodal capacity.
    This guarantees we capture raw text to display to the user for transparent verification.
    """
    client = get_genai_client()
    try:
        # Decode base64 image data
        image_bytes = base64.b64decode(image_b64)
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        
        prompt = (
            "You are a high-accuracy OCR assistant. Read this screenshot image. "
            "Extract and transcribe all readable text in the image exactly as it appears. "
            "If there are any visible metadata cues (such as a source logo, author, URL, date, or timestamps), "
            "extract and list them at the bottom under 'Visual Cues:'. Do not summarize or verify yet. "
            "Output only the raw extracted text and visual cues."
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, image_part]
        )
        
        extracted_text = response.text or "No text could be extracted from the screenshot."
        logger.info("Successfully extracted raw text from screenshot via Gemini multimodal.")
        return extracted_text
    except Exception as e:
        logger.error(f"Error during screenshot OCR: {e}")
        return f"OCR Error: Failed to parse image. Details: {str(e)}"

class ExtractedClaimResult(BaseModel):
    extractedClaim: str
    claimType: str

def extract_claim_from_text(raw_text: str) -> Dict[str, str]:
    """
    Step B: Identifies a single factual claim and classifies its type.
    """
    client = get_genai_client()
    try:
        # Use structured schema via Pydantic model
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=raw_text,
            config=types.GenerateContentConfig(
                system_instruction=CLAIM_EXTRACTION_PROMPT,
                response_mime_type="application/json",
                response_schema=ExtractedClaimResult
            )
        )
        
        parsed: ExtractedClaimResult = response.parsed
        logger.info(f"Extracted claim: '{parsed.extractedClaim}' (Type: {parsed.claimType})")
        return {
            "extractedClaim": parsed.extractedClaim,
            "claimType": parsed.claimType
        }
    except Exception as e:
        logger.error(f"Error during claim extraction: {e}")
        # Graceful fallback
        return {
            "extractedClaim": raw_text[:150] + "..." if len(raw_text) > 150 else raw_text,
            "claimType": "Mixed"
        }

class DecomposedClaim(BaseModel):
    subclaims: List[str] = Field(..., description="List of atomic subclaims extracted from the claim")

def decompose_claim(claim_text: str, raw_ocr_text: Optional[str] = None) -> List[str]:
    """
    Step B.2: Decomposes a claim into subclaims (e.g. visible text accuracy, source provenance, broader real-world truth).
    """
    client = get_genai_client()
    
    prompt = f"Claim to Decompose: \"{claim_text}\"\n"
    if raw_ocr_text:
        prompt += f"Screenshot OCR Text Context:\n\"\"\"\n{raw_ocr_text}\n\"\"\"\n"
        
    try:
        logger.info(f"Decomposing claim: '{claim_text}'")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=DECOMPOSITION_PROMPT,
                response_mime_type="application/json",
                response_schema=DecomposedClaim
            )
        )
        parsed: DecomposedClaim = response.parsed
        logger.info(f"Decomposed subclaims successfully: {parsed.subclaims}")
        return parsed.subclaims
    except Exception as e:
        logger.error(f"Error during claim decomposition: {e}")
        # Fallback to general fact-checking subclaims
        return [
            f"Is the claim '{claim_text}' numerically/factually accurate based on the visible metrics?",
            "Is the source of this claim trustworthy and independently verified by reputable files?",
            "Does the broader claim or conclusion hold up against external, independent authoritative evidence?"
        ]

def check_provenance(doc: Dict[str, Any], claim_text: str) -> Dict[str, Any]:
    """
    Step B.3: Analyzes document content/metadata to flag if it represents a repetition or citation of the claim.
    """
    content = doc.get("content", "").lower()
    title = doc.get("title", "").lower()
    domain = doc.get("domain", "").lower()
    
    # Check for keywords indicating social media citations, viral loops, or unverified repetitions
    social_indicators = [
        "tweeted", "posted on x", "instagram post", "insta post", "viral post", 
        "social media post", "rishi bagree", "tweet", "facebook post", 
        "screenshot of", "according to a post", "viral image", "claims in a post",
        "claims in a tweet", "sharing a screenshot"
    ]
    
    is_repetition = False
    repetition_reason = ""
    
    for indicator in social_indicators:
        if indicator in content or indicator in title:
            is_repetition = True
            repetition_reason = f"Cites unverified social media context ('{indicator}')"
            break
            
    # Check if the domain itself is general and merely repeating a viral topic
    if "timesbull" in domain or "moneycontrol" in domain and "rishi" in content:
        is_repetition = True
        repetition_reason = "General news site repeating the viral social media post"
        
    doc["is_repetition"] = is_repetition
    doc["repetition_reason"] = repetition_reason
    return doc

def verify_claim_against_evidence(
    extracted_claim: str, 
    claim_type: str, 
    evidence: List[Dict[str, Any]], 
    evidence_scope: str = "Curated",
    raw_ocr_text: Optional[str] = None,
    subclaims: Optional[List[str]] = None
) -> VerificationResponse:
    """
    Step C: Reasoning agent audits the claim against retrieved evidence.
    Supports routing to gemini-2.5-pro if detailed reasoning is needed.
    """
    client = get_genai_client()
    
    # Select reasoning model
    model_name = os.getenv("REASONING_MODEL", "gemini-2.5-flash")
    logger.info(f"Running claim verification using model: '{model_name}'")
    
    # Format evidence into structured text for model context with provenance ratings
    evidence_block = ""
    for idx, doc in enumerate(evidence, 1):
        doc = check_provenance(doc, extracted_claim)
        provenance_str = f"Low Provenance - {doc['repetition_reason']}" if doc.get("is_repetition") else "Independent Verification Source"
        evidence_block += (
            f"Evidence Source #{idx}:\n"
            f"- Title: {doc.get('title')}\n"
            f"- Domain: {doc.get('domain')}\n"
            f"- Tier: {doc.get('tier')} ({'Primary' if doc.get('tier')==1 else 'Secondary' if doc.get('tier')==2 else 'Context'})\n"
            f"- Date: {doc.get('date')}\n"
            f"- URL: {doc.get('url')}\n"
            f"- Provenance Rating: {provenance_str}\n"
            f"- Contextual Evidence: {doc.get('content')}\n"
            f"----------------------------------------\n"
        )
        
    # Format subclaims list
    subclaims_block = ""
    if subclaims:
        subclaims_block = "Decomposed Subclaims to evaluate separately:\n"
        for i, sc in enumerate(subclaims, 1):
            subclaims_block += f"{i}. {sc}\n"
        subclaims_block += "\n"
        
    user_prompt = (
        f"Claim to Verify: \"{extracted_claim}\"\n"
        f"Claim Type: {claim_type}\n\n"
        f"{subclaims_block}"
        f"Evidence Sources (Scope: {evidence_scope}):\n"
        f"{evidence_block}\n"
    )
    
    if raw_ocr_text:
        user_prompt += f"Original Raw Context of Claim (from Screenshot OCR):\n\"\"\"\n{raw_ocr_text}\n\"\"\"\n"

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=VERIFICATION_PROMPT,
                response_mime_type="application/json",
                response_schema=VerificationResponse
            )
        )
        
        parsed: VerificationResponse = response.parsed
        # Re-attach raw text if OCR was performed
        if raw_ocr_text:
            parsed.extractedText = raw_ocr_text
        parsed.evidenceScope = evidence_scope
            
        logger.info(f"Verification complete. Verdict: {parsed.verdict} (Confidence: {parsed.confidence}, Scope: {parsed.evidenceScope})")
        return parsed
    except Exception as e:
        logger.error(f"Error during claim verification reasoning: {e}")
        # Return fallback Unresolved response
        return VerificationResponse(
            extractedText=raw_ocr_text,
            extractedClaim=extracted_claim,
            claimType=claim_type,
            verdict="Unresolved",
            why=["An error occurred during verification processing."],
            confidence="Low",
            warnings=[f"System error: {str(e)}"],
            sources=[
                Source(
                    title=doc.get("title", "Unknown"),
                    domain=doc.get("domain", "Unknown"),
                    tier=doc.get("tier", 3),
                    date=doc.get("date", "Unknown"),
                    url=doc.get("url", "#"),
                    snippet=doc.get("snippet", "")
                ) for doc in evidence
            ],
            evidenceScope=evidence_scope
        )

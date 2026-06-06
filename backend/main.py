import os
import logging
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv

# Import our custom agents and search engines
from backend.agent import ocr_screenshot, extract_claim_from_text, verify_claim_against_evidence, decompose_claim
from backend.search import retrieve_evidence
from backend.schema import VerificationResponse

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("claimlens.api")

app = FastAPI(
    title="ClaimLens Backend Agent API",
    description="A thin verification gateway using Vertex AI Gemini and Elastic-backed search",
    version="1.0.0"
)

# Configure CORS to allow the frontend to call our endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VerifyRequest(BaseModel):
    claimText: Optional[str] = Field(None, description="Pasted claim text to verify")
    imageB64: Optional[str] = Field(None, description="Base64 encoded screenshot image data")
    mimeType: Optional[str] = Field("image/png", description="Mime type of the screenshot")
    demoMode: Optional[bool] = Field(False, description="If True, forces real Elastic search and fails loudly on missing credentials")

@app.get("/api/health")
def health_check():
    es_configured = bool(os.getenv("ES_URL") and os.getenv("ES_API_KEY"))
    return {
        "status": "healthy",
        "project": os.getenv("GOOGLE_CLOUD_PROJECT", "dataagentplatform"),
        "elastic_configured": es_configured,
        "reasoning_model": os.getenv("REASONING_MODEL", "gemini-2.5-flash")
    }

@app.post("/api/verify", response_model=VerificationResponse)
def verify_claim(payload: VerifyRequest):
    logger.info("Received verification request.")
    
    # 1. Input resolution and OCR
    raw_text = ""
    raw_ocr_text = None
    
    if payload.imageB64:
        logger.info("Processing screenshot input...")
        # Clean potential base64 prefixes (e.g. data:image/png;base64,...)
        b64_data = payload.imageB64
        if "," in b64_data:
            b64_data = b64_data.split(",")[1]
            
        raw_ocr_text = ocr_screenshot(b64_data, payload.mimeType)
        # If OCR returns an error, raise it
        if raw_ocr_text.startswith("OCR Error:"):
            raise HTTPException(status_code=400, detail=raw_ocr_text)
            
        # Fallback to claimText if OCR returned no text or is empty
        if not raw_ocr_text or "No text could be extracted" in raw_ocr_text or raw_ocr_text.strip() == "":
            logger.info("OCR returned no text, falling back to claimText for claim extraction")
            raw_text = payload.claimText or ""
        else:
            raw_text = raw_ocr_text
    elif payload.claimText:
        logger.info("Processing text claim input...")
        raw_text = payload.claimText
    else:
        raise HTTPException(
            status_code=400, 
            detail="Invalid request: You must provide either 'claimText' or 'imageB64'."
        )

    # 2. Extract single atomic claim & classification
    logger.info("Extracting atomic claim...")
    extraction = extract_claim_from_text(raw_text)
    extracted_claim = extraction.get("extractedClaim", "").strip()
    claim_type = extraction.get("claimType", "Mixed")
    
    # Fallback to claimText if extracted claim is empty or resolves to "None" / "Null" / "N/A"
    if (not extracted_claim or extracted_claim.lower() in ["none", "null", "n/a", ""]) and payload.claimText:
        logger.info("Extracted claim from OCR text was empty or invalid. Falling back to claimText for extraction...")
        extraction = extract_claim_from_text(payload.claimText)
        extracted_claim = extraction.get("extractedClaim", "").strip()
        claim_type = extraction.get("claimType", "Mixed")
    
    # If the claim is empty or invalid even after fallback
    if not extracted_claim or extracted_claim.lower() in ["none", "null", "n/a", ""]:
        logger.info("Could not extract any verifiable claim. Returning Unresolved response early.")
        return VerificationResponse(
            extractedText=raw_ocr_text,
            extractedClaim=payload.claimText or "N/A",
            claimType="Mixed",
            verdict="Unresolved",
            why=["The input does not contain a specific, verifiable factual claim."],
            confidence="Low",
            warnings=["No verifiable claim could be extracted from the input text."],
            sources=[],
            evidenceScope="None"
        )

    # 3. Retrieve evidence
    # Pass demoMode so it fails loudly if Elastic is missing
    logger.info(f"Retrieving evidence for claim: '{extracted_claim}'...")
    try:
        evidence, evidence_scope = retrieve_evidence(extracted_claim, demo_mode=payload.demoMode)
    except ValueError as val_err:
        logger.error(f"Demo Mode Validation Failure: {val_err}")
        raise HTTPException(status_code=500, detail=str(val_err))
    except Exception as search_err:
        logger.error(f"Search retrieval failed: {search_err}")
        raise HTTPException(status_code=500, detail=f"Search retrieval error: {str(search_err)}")

    # 3.b Decompose the claim
    logger.info("Decomposing claim...")
    subclaims = decompose_claim(extracted_claim, raw_ocr_text)

    # 4. Agent verification reasoning
    logger.info("Running agent verification reasoning...")
    result = verify_claim_against_evidence(
        extracted_claim=extracted_claim,
        claim_type=claim_type,
        evidence=evidence,
        evidence_scope=evidence_scope,
        raw_ocr_text=raw_ocr_text,
        subclaims=subclaims
    )
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

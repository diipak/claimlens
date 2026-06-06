import React, { useState, useEffect } from "react";
import { 
  ExternalLink, 
  UploadCloud, 
  ShieldAlert, 
  RefreshCw,
  AlertCircle,
  X,
  Share2
} from "lucide-react";
import "./App.css";

// Match backend types
interface Source {
  title: string;
  domain: string;
  tier: 1 | 2 | 3;
  date: string;
  url: string;
  snippet: string;
}

interface VerificationResponse {
  extractedText?: string;
  extractedClaim: string;
  claimType: 'Numeric' | 'Ranking' | 'Temporal' | 'Mixed';
  verdict: 'Supported' | 'Misleading' | 'Projected as current' | 'Outdated' | 'Unsupported' | 'Unresolved';
  why: string[];
  confidence: 'Low' | 'Medium' | 'High';
  warnings: string[];
  sources: Source[];
  evidenceScope: 'Curated' | 'Live Web' | 'Hybrid' | 'None';
}

// Sample base64 screenshot representing a fake dashboard showing inflation at 8.5%
// Using 100x100 solid color red PNG base64 for Gemini multimodal API compatibility
const MINI_PNG_BASE64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAA5klEQVR4nO3QQQkAIADAQLV/Z63gXiLcJRibe3BrvQ74iVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWcEBil4Bx/GEGnoAAAAASUVORK5CYII=";

export default function App() {
  const [claimText, setClaimText] = useState("");
  const [imageB64, setImageB64] = useState<string | null>(null);
  const [imageFileName, setImageFileName] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState(false);
  const [checking, setChecking] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [result, setResult] = useState<VerificationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeScenario, setActiveScenario] = useState<number | null>(null);
  const [sharedDetected, setSharedDetected] = useState(false);

  // Verification progress steps definitions
  const steps = [
    "Raw Input Ingestion",
    "Gemini OCR Text Extraction",
    "Atomic Claim Formulation",
    "Elastic Curated Source Retrieval",
    "Comparative Logic Audit",
    "Structured Report Synthesis"
  ];

  // Pipeline simulation timer during API call
  useEffect(() => {
    let interval: any;
    if (checking) {
      interval = setInterval(() => {
        setCurrentStep((prev) => (prev < 4 ? prev + 1 : prev));
      }, 1200);
    } else {
      setCurrentStep(0);
    }
    return () => clearInterval(interval);
  }, [checking]);

  // Intake Shared Content from PWA Web Share Target
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const title = params.get("title") || "";
    const text = params.get("text") || "";
    const url = params.get("url") || "";

    let sharedInput = "";
    if (text) {
      sharedInput += text;
    }
    
    // Append URL if provided and not already in text
    if (url) {
      if (sharedInput) {
        if (!sharedInput.includes(url)) {
          sharedInput += "\n\n" + url;
        }
      } else {
        sharedInput = url;
      }
    }
    
    // Prefill with Title if text is empty
    if (!sharedInput && title) {
      sharedInput = title;
    }

    if (sharedInput) {
      setClaimText(sharedInput);
      setActiveScenario(null);
      setResult(null);
      setError(null);
      setSharedDetected(true);
      // Clean query parameters from address bar to avoid re-intake on page refresh
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  // Categorize and guide user actions on unresolved audits
  const getUnresolvedAnalysis = (res: VerificationResponse) => {
    const whyText = res.why.join(" ").toLowerCase();
    const hasSources = res.sources && res.sources.length > 0;
    
    // Case 1: Ambiguous Wording
    if (
      whyText.includes("ambiguous") || 
      whyText.includes("broad") || 
      whyText.includes("vague") || 
      whyText.includes("specify") || 
      whyText.includes("opinion") ||
      whyText.includes("wording") ||
      whyText.includes("unclear") ||
      whyText.includes("subjective")
    ) {
      return {
        type: "Ambiguous Wording",
        description: "The claim text is too broad, vague, or subjective, which prevents mapping it to specific, verifiable numeric, ranking, or temporal facts.",
        actions: [
          "Highlight a shorter, more specific claim (e.g. isolate a single numeric assertion).",
          "Remove opinions, adjectives, or subjective framing from the input.",
          "Check that the claim focuses on a single concrete event or metric."
        ]
      };
    }
    
    // Case 2: Weak Retrieval
    if (!hasSources || res.evidenceScope === "None" || whyText.includes("no relevant") || whyText.includes("no evidence") || whyText.includes("no documents") || whyText.includes("not found")) {
      return {
        type: "Weak Source Retrieval",
        description: "No matching documents, statistics, or reports could be found in the curated index or live web search for this specific claim topic.",
        actions: [
          "Double-check the spelling of key numbers, dates, or proper names.",
          "Ensure your query contains specific keywords rather than a general conversation.",
          "Attach the original screenshot or share the direct link to run verification on a specific URL."
        ]
      };
    }
    
    // Case 3: No Trustworthy Evidence
    return {
      type: "No Trustworthy Evidence",
      description: "Factual sources were retrieved, but they do not contain clear, authoritative, or consistent evidence to confidently support or contradict the claim.",
      actions: [
        "Provide a direct URL to the official source report in the query.",
        "Upload a screenshot of the original chart to leverage multimodal visual verification.",
        "Verify if the claim refers to a highly volatile or disputed statistic."
      ]
    };
  };

  // Handle Scenario Pre-selection
  const handleScenarioSelect = (num: number) => {
    setActiveScenario(num);
    setResult(null);
    setError(null);
    
    if (num === 1) {
      setClaimText("The new Alpha Metro expansion line is finally complete and open for passenger operations this week!");
      setImageB64(null);
      setImageFileName(null);
    } else if (num === 2) {
      setClaimText("According to latest official data, India's economy is now the 3rd largest in the world, ahead of Germany and Japan.");
      setImageB64(null);
      setImageFileName(null);
    } else if (num === 3) {
      setClaimText("CPI inflation is currently sitting at 8.5 percent according to this dashboard capture.");
      // Seed base64 screenshot
      setImageB64(MINI_PNG_BASE64);
      setImageFileName("inflation_dashboard_screenshot.png");
    } else if (num === 4) {
      setClaimText("Taylor Swift Eras Tour concert film box office sales exceeded 260 million dollars globally.");
      setImageB64(null);
      setImageFileName(null);
    }
  };

  // Process manual screenshot files
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImageFileName(file.name);
    setActiveScenario(null);
    setResult(null);
    setError(null);

    const reader = new FileReader();
    reader.onloadend = () => {
      setImageB64(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const removeScreenshot = () => {
    setImageB64(null);
    setImageFileName(null);
    if (activeScenario === 3) {
      setActiveScenario(null);
      setClaimText("");
    }
  };

  // Submit Claim to API
  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claimText && !imageB64) return;

    setChecking(true);
    setResult(null);
    setError(null);
    setCurrentStep(0);

    const payload = {
      claimText: claimText || null,
      imageB64: imageB64 || null,
      mimeType: imageFileName?.endsWith(".jpg") || imageFileName?.endsWith(".jpeg") ? "image/jpeg" : "image/png",
      demoMode: demoMode
    };

    try {
      // Use VITE_API_URL if set (production), otherwise derive from current host.
      // Preserve the page protocol so HTTPS pages never make HTTP requests (mixed-content block).
      const apiBase = import.meta.env.VITE_API_URL
        ? import.meta.env.VITE_API_URL.replace(/\/$/, "")
        : (window.location.port === "5173" || window.location.port === "3000"
            ? `${window.location.protocol}//${window.location.hostname}:8000`
            : "");
      const response = await fetch(`${apiBase}/api/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Server returned an error during verification.");
      }

      const data: VerificationResponse = await response.json();
      
      // Let the reasoning step light up before showing results
      setCurrentStep(5);
      setTimeout(() => {
        setResult(data);
        setChecking(false);
      }, 800);

    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
      setChecking(false);
    }
  };

  const getVerdictClass = (verdict: string) => {
    const v = verdict.toLowerCase();
    if (v === "supported") return "supported";
    if (v === "unsupported") return "unsupported";
    if (v === "unresolved") return "unresolved";
    return "misleading"; // Outdated, Projected as current, Misleading
  };

  return (
    <div className="app-layout animate-fade-in">
      {/* Top Bar Navigation */}
      <header className="header">
        <div className="header-inner">
          <div className="logo-group">
            <span className="logo-main font-bold">ClaimLens</span>
            <span className="logo-badge">v1.5</span>
          </div>
          <span className="header-tagline-mobile hidden md:inline-block">GCP Audit Intelligence</span>
        </div>
      </header>

      <div className="container">
        {/* Hero Area */}
        <div className="hero-section">
          <h2 className="hero-title serif-font italic">Verify anything.</h2>
          <p className="hero-subtitle">Institutional-grade audits for claims, screenshots, and threads.</p>
        </div>

        {/* Collapsible Info Block */}
        <details className="how-it-works-details">
          <summary className="how-it-works-summary">
            <span>How ClaimLens Works</span>
            <span className="details-toggle-icon">expand_more</span>
          </summary>
          <div className="how-it-works-content">
            <p>
              ClaimLens validates public numeric, ranking, and temporal assertions in real-time through a two-stage lookup flow:
            </p>
            <div className="how-it-works-grid">
              <div className="how-it-works-card">
                <strong>1. Curated Database Audit</strong>
                <p>Queries a secure index of official reports, government statistics, and high-trust institutional facts.</p>
              </div>
              <div className="how-it-works-card">
                <strong>2. Live Web Fallback</strong>
                <p>If the curated index yields insufficient evidence, the system performs targeted live discovery over trusted primary domains and news.</p>
              </div>
            </div>
            <p className="how-it-works-footer">
              Finally, Vertex AI's Gemini reasoning engine cross-references all evidence, flags manipulative framing, and issues a structured audit report.
            </p>
          </div>
        </details>

        {/* Scenario Selection Pills */}
        <div className="scenario-selector">
          <span className="scenario-title">Try a demo:</span>
          <div className="scenario-chips">
            <button 
              type="button" 
              className={`scenario-chip ${activeScenario === 1 ? "active" : ""}`}
              onClick={() => handleScenarioSelect(1)}
              disabled={checking}
            >
              2026 Alpha Metro
            </button>
            <button 
              type="button" 
              className={`scenario-chip ${activeScenario === 2 ? "active" : ""}`}
              onClick={() => handleScenarioSelect(2)}
              disabled={checking}
            >
              Global GDP Ranking
            </button>
            <button 
              type="button" 
              className={`scenario-chip ${activeScenario === 3 ? "active" : ""}`}
              onClick={() => handleScenarioSelect(3)}
              disabled={checking}
            >
              Inflation Dashboard
            </button>
            <button 
              type="button" 
              className={`scenario-chip ${activeScenario === 4 ? "active" : ""}`}
              onClick={() => handleScenarioSelect(4)}
              disabled={checking}
            >
              Taylor Swift Box Office
            </button>
          </div>
        </div>

        {sharedDetected && (
          <div className="shared-alert-banner">
            <div className="shared-alert-content">
              <Share2 size={15} />
              <span>Shared input prefilled. Verify in one tap!</span>
            </div>
            <button 
              type="button" 
              className="btn-dismiss-shared" 
              onClick={() => setSharedDetected(false)}
            >
              <X size={13} />
            </button>
          </div>
        )}

        {/* Input Card Form */}
        <form onSubmit={handleVerify} className="card input-card">
          <div className="input-group">
            <label className="input-label" htmlFor="claim-textarea">Claim Assertion / Context</label>
            <textarea
              id="claim-textarea"
              className="textarea-claim"
              placeholder="Paste public claim, budget number, economic ranking, or upload a screenshot to OCR..."
              value={claimText}
              onChange={(e) => {
                setClaimText(e.target.value);
                setActiveScenario(null);
              }}
              disabled={checking}
            />
          </div>

          {/* Screenshot Input and preview */}
          <div className="input-group">
            <span className="input-label">Claim Screenshot (Optional)</span>
            {!imageB64 ? (
              <>
                <label className="file-dropzone">
                  <UploadCloud size={20} className="text-muted" />
                  <p className="dropzone-text">Upload screenshot for Multimodal OCR</p>
                  <span className="dropzone-subtext">PNG or JPG files</span>
                  <input 
                    type="file" 
                    accept="image/png, image/jpeg" 
                    onChange={handleFileChange} 
                    style={{ display: "none" }}
                    disabled={checking}
                  />
                </label>
                <span className="screenshot-upload-note">💡 Sharing a screenshot? Select it here to run Multimodal OCR.</span>
              </>
            ) : (
              <div className="screenshot-preview">
                {imageFileName && (
                  <div className="screenshot-filename-badge">
                    {imageFileName}
                  </div>
                )}
                <img src={imageB64} alt="Screenshot preview" />
                <button type="button" className="remove-screenshot" onClick={removeScreenshot} disabled={checking}>
                  Remove
                </button>
              </div>
            )}
          </div>

          <div className="action-bar">
            {/* Demo Mode Toggle */}
            <label className="mode-toggle">
              <input 
                type="checkbox" 
                checked={demoMode} 
                onChange={(e) => setDemoMode(e.target.checked)}
                disabled={checking}
              />
              <span>Force Curated Index</span>
            </label>

            <button 
              type="submit" 
              className="btn-verify" 
              disabled={checking || (!claimText && !imageB64)}
            >
              {checking ? (
                <>
                  <RefreshCw size={13} className="animate-spin" />
                  <span>Auditing...</span>
                </>
              ) : (
                <span>Verify Claim</span>
              )}
            </button>
          </div>
        </form>

        {/* Error panel */}
        {error && (
          <div className="card error-card">
            <div className="error-content">
              <AlertCircle size={18} className="error-icon" />
              <div className="error-text-container">
                <strong className="error-title">System Audit Interrupted</strong>
                <p className="error-message">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Loading Pipeline Status Display */}
        {checking && (
          <div className="card pipeline-card">
            <span className="section-label">Active Audit Pipeline</span>
            <div className="pipeline-status">
              {steps.map((stepText, idx) => {
                const isActive = idx === currentStep;
                const isCompleted = idx < currentStep;
                let statusClass = "";
                if (isActive) statusClass = "active";
                else if (isCompleted) statusClass = "completed";

                // Don't show OCR step if we don't have an image
                if (idx === 1 && !imageB64) return null;

                return (
                  <div key={stepText} className={`step-item ${statusClass}`}>
                    <div className="step-dot" />
                    <span className="step-text">{stepText}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Report Result Dashboard */}
        {result && !checking && (
          <div className="result-container animate-fade-in">
            {/* 1) Verdict Display Banner */}
            <div className={`verdict-banner-container ${getVerdictClass(result.verdict)}`}>
              <div className="verdict-banner-content">
                <span className="verdict-banner-subtitle">Final Verdict</span>
                <h2 className="verdict-banner-title serif-font italic">{result.verdict}</h2>
                
                {/* 2) One-sentence explanation integrated for cleaner hierarchy */}
                {result.why && result.why.length > 0 && (
                  <p className="verdict-banner-explanation">
                    {result.why[0]}
                  </p>
                )}
              </div>
              <div className="verdict-banner-badges">
                <span className="badge badge-outline">
                  Confidence level: {result.confidence}
                </span>
                <span className="badge badge-outline">
                  Checked against: {
                    result.evidenceScope === "Curated" 
                      ? "Curated Sources" 
                      : result.evidenceScope === "Live Web" 
                      ? "Live Web" 
                      : result.evidenceScope === "Hybrid" 
                      ? "Hybrid" 
                      : "None"
                  }
                </span>
              </div>
            </div>

            {/* 3) Claim being checked */}
            <div className="result-section">
              <span className="section-label">Claim being checked</span>
              <div className="claim-blockquote-card">
                <blockquote className="claim-blockquote">
                  "{result.extractedClaim}"
                </blockquote>
              </div>
            </div>

            {/* Unresolved failure analysis details */}
            {result.verdict.toLowerCase() === "unresolved" && (
              <div className="result-section unresolved-section">
                <div className="unresolved-header">
                  <ShieldAlert size={16} className="text-unresolved-icon" />
                  <span className="section-label">Why this claim could not be verified</span>
                </div>
                {(() => {
                  const analysis = getUnresolvedAnalysis(result);
                  return (
                    <div className="unresolved-card">
                      <div className="unresolved-badge-row">
                        <span className="unresolved-type-badge">{analysis.type}</span>
                      </div>
                      <p className="unresolved-description">{analysis.description}</p>
                      
                      <div className="unresolved-actions-box">
                        <span className="actions-label">Recommended Next Steps</span>
                        <ul className="unresolved-actions-list">
                          {analysis.actions.map((act, idx) => (
                            <li key={idx} className="unresolved-action-item">
                              <span className="action-bullet">➔</span>
                              <span>{act}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}

            {/* 4) Top reasons (remaining explanations) */}
            {result.verdict.toLowerCase() !== "unresolved" && result.why && result.why.length > 1 && (
              <div className="result-section">
                <span className="section-label">Top reasons</span>
                <ul className="reasons-list">
                  {result.why.slice(1).map((bullet, i) => (
                    <li key={i} className="reason-item">
                      <div className="reason-bullet" />
                      <p className="reason-text">{bullet}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* 5) Sources reviewed */}
            {result.sources && result.sources.length > 0 && (
              <div className="result-section">
                <span className="section-label">Sources reviewed</span>
                <div className="source-list">
                  {result.sources.map((src, i) => (
                    <div key={i} className="source-card">
                      <div className="source-header">
                        <span className="source-publisher">{src.domain}</span>
                        <div className="source-badges">
                          <span className="source-date-badge">
                            {src.date}
                          </span>
                          <span className={`source-tier tier-${src.tier}`}>
                            {src.tier === 1 ? "Primary Source" : src.tier === 2 ? "Secondary Source" : "General Context"}
                          </span>
                        </div>
                      </div>
                      <h4 className="source-title">{src.title}</h4>
                      <p className="source-snippet">"{src.snippet}"</p>
                      <div className="source-footer">
                        <a href={src.url} target="_blank" rel="noopener noreferrer" className="source-link">
                          <span>Visit Source Link</span>
                          <ExternalLink size={11} />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 6) Expandable details: See how this was checked */}
            <details className="advanced-details">
              <summary className="advanced-summary">
                <span>See how this was checked</span>
                <span className="advanced-toggle-icon">expand_more</span>
              </summary>
              <div className="advanced-content">
                <div className="advanced-grid">
                  <div className="advanced-row">
                    <strong>Checked against:</strong>
                    <span>
                      {result.evidenceScope === "Curated" 
                        ? "Curated Index Only" 
                        : result.evidenceScope === "Live Web" 
                        ? "Live Web Fallback" 
                        : result.evidenceScope === "Hybrid" 
                        ? "Hybrid (Curated + Live)" 
                        : "No Sources"}
                    </span>
                  </div>
                  <div className="advanced-row">
                    <strong>Confidence level:</strong>
                    <span>{result.confidence}</span>
                  </div>
                  <div className="advanced-row">
                    <strong>Claim type:</strong>
                    <span>{result.claimType}</span>
                  </div>
                </div>

                {result.warnings && result.warnings.length > 0 && (
                  <div className="important-notes-section">
                    <strong>Important note:</strong>
                    <ul className="notes-list">
                      {result.warnings.map((warn, i) => (
                        <li key={i}>{warn}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.extractedText && (
                  <div className="advanced-ocr">
                    <strong>Extracted image text:</strong>
                    <pre>{result.extractedText}</pre>
                  </div>
                )}
              </div>
            </details>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <footer className="footer">
        CLAIMLENS // SECURE VERIFICATION LEDGER v1.5
      </footer>
    </div>
  );
}

import sys
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_result(name, success, info=""):
    status = "SUCCESS" if success else "FAILED"
    print(f"[{status}] {name}")
    if info:
        print(f"      Details: {info}")
    print("-" * 50)

def run_tests():
    print("=" * 60)
    print("STARTING CLAIMLENS PIPELINE INTEGRATION TESTS")
    print("=" * 60)

    elastic_configured = False

    # Test 1: Health Check
    try:
        r = requests.get(f"{BASE_URL}/api/health")
        if r.status_code == 200:
            data = r.json()
            elastic_configured = data.get("elastic_configured", False)
            print_result(
                "Test 1: Health Check Endpoint",
                True,
                f"Status: {data['status']}, GCP Project: {data['project']}, Elastic Configured: {elastic_configured}"
            )
        else:
            print_result("Test 1: Health Check Endpoint", False, f"HTTP Status: {r.status_code}")
            sys.exit(1)
    except Exception as e:
        print_result("Test 1: Health Check Endpoint", False, f"Connection error: {e}")
        print("ERROR: FastAPI backend is not running. Please start the backend with 'python main.py' first.")
        sys.exit(1)

    # Test 2: Scenario 1 - Future projection framed as current fact
    try:
        payload = {
            "claimText": "The new Alpha Metro expansion line is finally complete and open for passenger operations this week!",
            "demoMode": False
        }
        r = requests.post(f"{BASE_URL}/api/verify", json=payload)
        if r.status_code == 200:
            data = r.json()
            verdict = data.get("verdict")
            claim = data.get("extractedClaim")
            success = verdict in ["Projected as current", "Misleading"]
            print_result(
                "Test 2: Scenario 1 - Future Projection Audit",
                success,
                f"Claim: '{claim}'\n      Verdict: '{verdict}'\n      Bullets: {data.get('why')}\n      Sources: {[s['domain'] for s in data.get('sources', [])]}"
            )
        else:
            print_result("Test 2: Scenario 1", False, f"HTTP Status: {r.status_code}")
    except Exception as e:
        print_result("Test 2: Scenario 1", False, f"Error: {e}")

    # Test 3: Scenario 2 - GDP nominal vs PPP ranking mismatch
    try:
        payload = {
            "claimText": "According to latest official data, India's economy is now the 3rd largest in the world, ahead of Germany and Japan.",
            "demoMode": False
        }
        r = requests.post(f"{BASE_URL}/api/verify", json=payload)
        if r.status_code == 200:
            data = r.json()
            verdict = data.get("verdict")
            claim = data.get("extractedClaim")
            success = verdict in ["Misleading", "Unsupported"]
            print_result(
                "Test 3: Scenario 2 - GDP Ranking Ambiguity Audit",
                success,
                f"Claim: '{claim}'\n      Verdict: '{verdict}'\n      Bullets: {data.get('why')}\n      Sources: {[s['domain'] for s in data.get('sources', [])]}"
            )
        else:
            print_result("Test 3: Scenario 2", False, f"HTTP Status: {r.status_code}")
    except Exception as e:
        print_result("Test 3: Scenario 2", False, f"Error: {e}")

    # Test 4: Scenario 3 - Outdated inflation screenshot dashboard
    try:
        # Mini PNG base64 representation
        mini_png_base64 = "data:image/png;base64,iVBORw0KGgoAAAASUVORK5CYII="
        # Using 100x100 solid color red PNG base64 for Gemini multimodal API compatibility
        mini_png_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAA5klEQVR4nO3QQQkAIADAQLV/Z63gXiLcJRibe3BrvQ74iVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWcEBil4Bx/GEGnoAAAAASUVORK5CYII="
        payload = {
            "claimText": "CPI inflation is currently sitting at 8.5 percent according to this dashboard capture.",
            "imageB64": mini_png_base64,
            "mimeType": "image/png",
            "demoMode": False
        }
        r = requests.post(f"{BASE_URL}/api/verify", json=payload)
        if r.status_code == 200:
            data = r.json()
            verdict = data.get("verdict")
            claim = data.get("extractedClaim")
            success = verdict in ["Outdated", "Misleading"]
            print_result(
                "Test 4: Scenario 3 - Screenshot Outdated Data Audit",
                success,
                f"Claim: '{claim}'\n      Verdict: '{verdict}'\n      Bullets: {data.get('why')}\n      Warnings: {data.get('warnings')}\n      Sources: {[s['domain'] for s in data.get('sources', [])]}"
            )
        else:
            print_result("Test 4: Scenario 3", False, f"HTTP Status: {r.status_code}")
    except Exception as e:
        print_result("Test 4: Scenario 3", False, f"Error: {e}")

    # Test 5: Demo Mode Loud Fail Security
    if elastic_configured:
        print_result(
            "Test 5: Demo Mode Loud Fail Security",
            True,
            "SKIPPED: Elasticsearch is successfully configured. Loud fail safety check only runs when credentials are missing."
        )
    else:
        try:
            payload = {
                "claimText": "Checking for Elastic credentials loud-fail safety.",
                "demoMode": True
            }
            r = requests.post(f"{BASE_URL}/api/verify", json=payload)
            # It should fail with 500 because we haven't configured ES credentials
            if r.status_code == 500:
                err_msg = r.json().get("detail", "")
                success = "LOUD FAIL" in err_msg or "Elastic" in err_msg
                print_result(
                    "Test 5: Demo Mode Loud Fail Security",
                    success,
                    f"HTTP Status: {r.status_code}, Error Detail: '{err_msg}'"
                )
            else:
                print_result(
                    "Test 5: Demo Mode Loud Fail Security", 
                    False, 
                    f"Expected status 500, got {r.status_code}. Response: {r.text}"
                )
        except Exception as e:
            print_result("Test 5: Demo Mode Loud Fail Security", False, f"Error: {e}")

    # Test 6: Unknown claim should resolve as Unresolved or Unsupported via live web
    try:
        payload = {
            "claimText": "Alien spacecraft landing in New York central park was officially confirmed by world leaders yesterday.",
            "demoMode": False
        }
        r = requests.post(f"{BASE_URL}/api/verify", json=payload)
        if r.status_code == 200:
            data = r.json()
            verdict = data.get("verdict")
            success = verdict in ["Unresolved", "Unsupported"]
            print_result(
                "Test 6: Graceful Fallback (Web Audited)",
                success,
                f"Verdict: '{verdict}', Explanation: {data.get('why')}"
            )
        else:
            print_result("Test 6: Graceful Fallback (Web Audited)", False, f"HTTP Status: {r.status_code}")
    except Exception as e:
        print_result("Test 6: Graceful Fallback (Web Audited)", False, f"Error: {e}")

    # Test 8: Absolutely no evidence (curated & live web both 0 results) should resolve as Unresolved
    try:
        payload = {
            "claimText": "qwert12345yuiop67890asdfghjklzxcvbnm claim verification scenario.",
            "demoMode": False
        }
        r = requests.post(f"{BASE_URL}/api/verify", json=payload)
        if r.status_code == 200:
            data = r.json()
            verdict = data.get("verdict")
            scope = data.get("evidenceScope")
            success = verdict == "Unresolved" and scope == "None"
            print_result(
                "Test 8: Graceful Unresolved Fallback (Zero Evidence)",
                success,
                f"Verdict: '{verdict}'\n      Scope: '{scope}'\n      Explanation: {data.get('why')}"
            )
        else:
            print_result("Test 8: Graceful Unresolved Fallback (Zero Evidence)", False, f"HTTP Status: {r.status_code}")
    except Exception as e:
        print_result("Test 8: Graceful Unresolved Fallback (Zero Evidence)", False, f"Error: {e}")


    # Test 7: Live Web Fallback Verification
    try:
        payload = {
            "claimText": "Taylor Swift Eras Tour concert film box office sales exceeded 260 million dollars globally.",
            "demoMode": False
        }
        r = requests.post(f"{BASE_URL}/api/verify", json=payload)
        if r.status_code == 200:
            data = r.json()
            verdict = data.get("verdict")
            scope = data.get("evidenceScope")
            sources = data.get("sources", [])
            success = scope in ["Live Web", "Hybrid"] and len(sources) > 0
            print_result(
                "Test 7: Live Web Fallback Audit",
                success,
                f"Verdict: '{verdict}'\n      Scope: '{scope}'\n      Sources: {[s['domain'] for s in sources]}"
            )
        else:
            print_result("Test 7: Live Web Fallback Audit", False, f"HTTP Status: {r.status_code}")
    except Exception as e:
        print_result("Test 7: Live Web Fallback Audit", False, f"Error: {e}")

    print("=" * 60)
    print("CLAIMLENS VALIDATION INTEGRATION COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()

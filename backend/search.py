import os
import json
import logging
from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("claimlens.search")

# Stopwords for simple local search ranking
STOPWORDS = {"the", "a", "an", "is", "are", "was", "were", "of", "and", "in", "to", "for", "on", "with", "at", "by", "from", "has", "have", "had", "as", "than", "that", "this", "it"}

def get_elasticsearch_client() -> Optional[Elasticsearch]:
    es_url = os.getenv("ES_URL")
    es_api_key = os.getenv("ES_API_KEY")
    
    if not es_url or not es_api_key:
        return None
        
    try:
        # Initialize official Elasticsearch client
        client = Elasticsearch(
            es_url,
            api_key=es_api_key
        )
        # Check connection
        if client.ping():
            logger.info("Successfully connected to Elasticsearch.")
            return client
        else:
            logger.error("Elasticsearch ping failed.")
            return None
    except Exception as e:
        logger.error(f"Failed to initialize Elasticsearch client: {e}")
        return None

def search_local_fallback(query: str) -> List[Dict[str, Any]]:
    """
    A smart local keyword search simulator over curated_sources.json.
    Splits the query into words, filters stopwords, and ranks records based on exact word matches
    with thresholding to filter out false positives from single token matches in long queries.
    """
    import re
    logger.info(f"Running local fallback search for: '{query}'")
    try:
        db_path = os.path.join(os.path.dirname(__file__), "..", "database", "curated_sources.json")
        if not os.path.exists(db_path):
            logger.error(f"Local source database not found at {db_path}")
            return []
            
        with open(db_path, "r") as f:
            records = json.load(f)
            
        # Clean and tokenize query into lowercase words
        query_words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in query_words if w and w not in STOPWORDS]
        
        if not keywords:
            # Fallback to all words if query consists only of stopwords
            keywords = [w for w in query_words if w]
            
        if not keywords:
            logger.info("Local search query has no valid keywords.")
            return []

        scored_records = []
        for record in records:
            title_text = record.get("title", "").lower()
            content_text = record.get("content", "").lower()
            
            # Tokenize document fields into exact word sets
            title_words = set(re.findall(r'\b\w+\b', title_text))
            content_words = set(re.findall(r'\b\w+\b', content_text))
            all_doc_words = title_words.union(content_words)
            
            # Count exact matches for keywords
            matched_keywords = [kw for kw in keywords if kw in all_doc_words]
            
            if not matched_keywords:
                continue
                
            # If the query is long (>= 3 keywords), require at least 2 distinct keywords to match.
            # This avoids returning documents for completely unrelated topics (like GDP or Inflation)
            # that happen to share a single common token like a year ("2026") or number.
            if len(keywords) >= 3 and len(matched_keywords) < 2:
                continue
                
            # Compute score
            score = 0
            for kw in matched_keywords:
                score += 2
                if kw in title_words:
                    score += 3
                    
            if score > 0:
                scored_records.append((score, record))
                
        # Sort by score descending
        scored_records.sort(key=lambda x: x[0], reverse=True)
        results = [item[1] for item in scored_records]
        
        logger.info(f"Local search found {len(results)} matching sources after keyword thresholding.")
        return results
    except Exception as e:
        logger.error(f"Error reading local fallback database: {e}")
        return []

def determine_source_tier(url: str) -> int:
    """
    Categorizes domain from url into tiers:
    Tier 1 (Primary): .gov, .edu, or trusted international organization domains (imf.org, who.int, un.org, etc.)
    Tier 2 (Reputable News / Secondary): bbc.com, reuters.com, apnews.com, nytimes.com, bloomberg.com, wsj.com, etc.
    Tier 3 (Context / General): other sites
    """
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        hostname = hostname.lower()
        
        # Primary trusted domains
        tier1_suffixes = (".gov", ".edu")
        tier1_domains = {"imf.org", "who.int", "un.org", "worldbank.org", "wto.org", "unicef.org", "iea.org", "oecd.org", "europa.eu"}
        
        if hostname.endswith(tier1_suffixes) or any(hostname == td or hostname.endswith("." + td) for td in tier1_domains):
            return 1
            
        # Reputable news / Secondary sources
        tier2_domains = {
            "bbc.com", "bbc.co.uk", "reuters.com", "apnews.com", "nytimes.com", 
            "bloomberg.com", "wsj.com", "ft.com", "economist.com", "theguardian.com", 
            "cnbc.com", "cnn.com"
        }
        
        if any(hostname == nd or hostname.endswith("." + nd) for nd in tier2_domains):
            return 2
            
        return 3
    except Exception:
        return 3

def search_brave_web(query: str) -> List[Dict[str, Any]]:
    """
    Search Brave Web Search API for evidence when curated retrieval is insufficient.
    Filters and boosts trusted domains (Tier 1/2).
    """
    import requests
    brave_key = os.getenv("BRAVE_API_KEY")
    if not brave_key:
        logger.warning("BRAVE_API_KEY is not configured. Live web fallback skipped.")
        return []
        
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": brave_key
    }
    params = {
        "q": query,
        "count": 10
    }
    
    try:
        logger.info(f"Triggering Brave Web Search for: '{query}'")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            logger.error(f"Brave Search API returned error: {response.status_code} - {response.text}")
            return []
            
        data = response.json()
        web_results = data.get("web", {}).get("results", [])
        
        results = []
        for res in web_results:
            url_str = res.get("url", "")
            title = res.get("title", "No Title")
            snippet = res.get("description", "")
            
            # Extract hostname
            from urllib.parse import urlparse
            try:
                hostname = urlparse(url_str).hostname or ""
                # Strip 'www.' if present
                if hostname.startswith("www."):
                    hostname = hostname[4:]
            except Exception:
                hostname = ""
                
            # Date extraction
            date = res.get("age") or res.get("page_age") or "Recent"
            # Format the ISO timestamp to a cleaner date if possible
            if date and "T" in date:
                date = date.split("T")[0]
                
            tier = determine_source_tier(url_str)
            
            results.append({
                "title": title,
                "domain": hostname or "Web Link",
                "tier": tier,
                "date": date,
                "url": url_str,
                "content": snippet,
                "snippet": snippet,
                "scenarioTag": "live_web"
            })
            
        # Prioritize trusted domains: Sort by tier ascending (Tier 1, then Tier 2, then Tier 3)
        results.sort(key=lambda x: x["tier"])
        
        # Limit to top 5 results
        final_results = results[:5]
        logger.info(f"Brave Search returned {len(final_results)} prioritized results.")
        return final_results
        
    except Exception as e:
        logger.error(f"Brave Search API request failed: {e}")
        return []

def retrieve_evidence(query: str, demo_mode: bool = False) -> tuple[List[Dict[str, Any]], str]:
    """
    Retrieves evidence from curated sources. If curated evidence is insufficient,
    falls back to live web discovery via Brave Search API.
    Returns a tuple of (evidence_list, scope_string).
    scope_string can be "Curated", "Live Web", "Hybrid", or "None".
    """
    es_url = os.getenv("ES_URL")
    es_api_key = os.getenv("ES_API_KEY")
    
    # Check demo mode constraint
    if demo_mode:
        if not es_url or not es_api_key:
            raise ValueError(
                "LOUD FAIL: The system is in DEMO MODE, but Elastic credentials (ES_URL, ES_API_KEY) are not configured! "
                "Elastic-backed retrieval is mandatory for demo submissions."
            )
            
    curated_results = []
    
    es_client = get_elasticsearch_client()
    if es_client:
        try:
            logger.info(f"Querying Elasticsearch index for: '{query}'")
            # Query the standard elasticsearch index
            response = es_client.search(
                index="curated-sources",
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^3", "content", "snippet"],
                            "minimum_should_match": "2<35%"
                        }
                    },
                    "size": 5
                }
            )
            hits = response.get("hits", {}).get("hits", [])
            for hit in hits:
                source = hit.get("_source", {})
                curated_results.append({
                    "title": source.get("title"),
                    "domain": source.get("domain"),
                    "tier": int(source.get("tier", 3)),
                    "date": source.get("date"),
                    "url": source.get("url"),
                    "content": source.get("content"),
                    "snippet": source.get("snippet", source.get("content")[:200]),
                    "scenarioTag": source.get("scenarioTag", "elasticsearch")
                })
            logger.info(f"Elasticsearch returned {len(curated_results)} results.")
        except Exception as e:
            logger.error(f"Elasticsearch query failed: {e}")
            if demo_mode:
                raise e
            logger.info("Falling back to local search due to Elasticsearch query error.")
            curated_results = search_local_fallback(query)
    else:
        # Fallback to local search
        curated_results = search_local_fallback(query)

    # Determine fallback routing based on curated sufficiency
    # Sufficient if we get 3 or more curated results
    if len(curated_results) >= 3:
        return curated_results, "Curated"
        
    # If weak curated (1 or 2 results), query live web to supplement and return Hybrid
    if 0 < len(curated_results) < 3:
        live_results = search_brave_web(query)
        if live_results:
            # Combine sources, deduplicating by URL
            combined = curated_results + live_results
            seen_urls = set()
            deduped = []
            for doc in combined:
                url_str = doc.get("url", "")
                if url_str not in seen_urls:
                    seen_urls.add(url_str)
                    deduped.append(doc)
            logger.info(f"Merged weak curated with live web fallback. Total merged sources: {len(deduped)}")
            return deduped[:5], "Hybrid"
        else:
            return curated_results, "Curated"
            
    # If no curated evidence (0 results), fall back entirely to live web
    live_results = search_brave_web(query)
    if live_results:
        return live_results, "Live Web"
        
    return [], "None"


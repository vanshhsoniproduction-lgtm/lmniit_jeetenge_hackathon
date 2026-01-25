"""
================================================================================
                        WEB3.AI - WEBSITE SCRAPER MODULE
================================================================================
YEH FILE COMPETITOR WEBSITES KO SCRAPE KARTI HAI

FUNCTIONALITY:
- Kisi bhi website ka content fetch karta hai
- HTML se clean text extract karta hai
- Multiple pages scrape karta hai (homepage + key pages)

USED BY:
- CompeteScan AI Agent (competitor analysis)
- x402 Scraper Agent (simple web scraping)

LOCATION: agents/scraper.py

WORKFLOW:
┌─────────────────────────────────────────────────────────────────────┐
│ 1. scrape_competitor(url) call hota hai                             │
│ 2. Homepage fetch hota hai                                          │
│ 3. Important links dhundhe jaate hain (pricing, about, features)    │
│ 4. Un pages ka content bhi fetch hota hai                           │
│ 5. Sab content combine karke return hota hai                        │
└─────────────────────────────────────────────────────────────────────┘
================================================================================
"""

# ============================================================================
# IMPORTS - Required libraries
# ============================================================================

import requests          # HTTP requests bhejne ke liye (website fetch)
from bs4 import BeautifulSoup  # HTML parse karne ke liye (content extraction)
from urllib.parse import urljoin, urlparse  # URL manipulation ke liye


# ============================================================================
# CONSTANTS - Configuration values
# ============================================================================

# Browser User-Agent header - Website ko lagta hai ki real browser hai
# Bina iske kuch websites block kar deti hain
# Browser User-Agent header - Website ko lagta hai ki real browser hai
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def clean_text(soup):
    for script in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
        script.decompose()
    text = soup.get_text(separator=' ', strip=True)
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text[:15000]


def get_page_content(url):
    try:
        print(f"    📥 Fetching: {url[:50]}...")
        # Method 1: Direct Request
        resp = requests.get(url, headers=HEADERS, timeout=10)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            clean = clean_text(soup)
            print(f"    ✅ Scraped {len(clean)} characters")
            return clean, soup
        
        print(f"    ⚠️ Direct fetch failed (HTTP {resp.status_code}). Trying Jina Reader...")
        
        # Method 2: Jina Reader Fallback (For 403s/JS sites)
        jina_url = f"https://r.jina.ai/{url}"
        resp = requests.get(jina_url, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            print(f"    ✅ Scraped via Jina Reader ({len(resp.text)} chars)")
            return resp.text, None  # Jina returns plain MD, no Soup
            
        print(f"    ❌ Jina Reader failed: HTTP {resp.status_code}")
        return "", None
        
    except Exception as e:
        print(f"    ❌ Scrape Error: {str(e)[:50]}")
        return "", None


# ============================================================================
# MAIN SCRAPER FUNCTION
# ============================================================================

def scrape_competitor(base_url):
    if not base_url.startswith('http'):
        base_url = 'https://' + base_url

    print(f"\n🔍 [SCRAPER] Starting scrape for: {base_url}")
    print("=" * 60)
    
    # Homepage scrape
    print("📄 Fetching Homepage...")
    home_text, home_soup = get_page_content(base_url)
    
    if not home_text:
        print("❌ Failed to fetch content via all methods!")
        return "Failed to fetch website content."

    combined_context = f"--- HOMEPAGE ({base_url}) ---\n{home_text}\n\n"

    # Link discovery (only if Direct fetch worked and Soup is available)
    if home_soup:
        print("\n🔗 Discovering important pages...")
        visited = set([base_url, base_url + '/'])
        keywords = ['pricing', 'plans', 'features', 'product', 'about', 'contact']
        links_to_visit = []

        for a in home_soup.find_all('a', href=True):
            href = a['href']
            try:
                full_url = urljoin(base_url, href)
                if urlparse(full_url).netloc != urlparse(base_url).netloc:
                    continue
                if any(k in full_url.lower() for k in keywords):
                    if full_url not in visited and full_url not in links_to_visit:
                        links_to_visit.append(full_url)
                        visited.add(full_url)
                        print(f"    Found: {full_url}")
            except:
                continue
        
        links_to_visit = links_to_visit[:4]
        print(f"\n📄 Fetching {len(links_to_visit)} additional pages...")
        
        for link in links_to_visit:
            text, _ = get_page_content(link)
            if text:
                section = "PAGE"
                for k in keywords:
                    if k in link.lower(): 
                        section = k.upper()
                        break
                combined_context += f"--- {section} ({link}) ---\n{text}\n\n"
    else:
        print("    ℹ Soup unavailable (Jina Scrape). Skipping sub-page discovery.")

    result = combined_context[:50000]
    
    print("=" * 60)
    print(f"✅ [SCRAPER] Complete! Total: {len(result)} characters")
    print("=" * 60 + "\n")
    
    return result

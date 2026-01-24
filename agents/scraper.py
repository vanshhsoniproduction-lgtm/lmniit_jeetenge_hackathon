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
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def clean_text(soup):
    """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║  CLEAN TEXT FUNCTION                                                      ║
    ║  HTML se sirf useful text extract karta hai                              ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    
    YEH FUNCTION KYA KARTA HAI:
    1. Unwanted elements remove karta hai (scripts, styles, nav, footer)
    2. Text extract karta hai
    3. Extra whitespace clean karta hai
    4. 15000 characters tak limit karta hai
    
    PARAMETERS:
    - soup: BeautifulSoup object (parsed HTML)
    
    RETURNS:
    - Clean text string (max 15000 chars)
    """
    
    # Step 1: Unwanted elements remove karo
    # Yeh elements mein actual content nahi hota, sirf code/styling hota hai
    for script in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
        script.decompose()  # Element completely remove karo
    
    # Step 2: Text extract karo
    # separator=' ' = elements ke beech space daalo
    # strip=True = extra whitespace hatado
    text = soup.get_text(separator=' ', strip=True)
    
    # Step 3: Extra whitespace clean karo
    # Multiple newlines aur spaces ko single mein convert karo
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    # Step 4: Limit to 15000 characters (Gemini ke context limit ke liye)
    return text[:15000]


def get_page_content(url):
    """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║  GET PAGE CONTENT FUNCTION                                                ║
    ║  Ek URL se content fetch karta hai                                       ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    
    YEH FUNCTION KYA KARTA HAI:
    1. URL pe HTTP GET request bhejta hai
    2. Response check karta hai
    3. HTML parse karta hai
    4. Clean text return karta hai
    
    PARAMETERS:
    - url: Website URL (e.g., "https://example.com")
    
    RETURNS:
    - Tuple: (clean_text, soup_object)
    - Error case: ("", None)
    """
    
    try:
        # Step 1: HTTP GET request bhejo
        # timeout=10 = 10 seconds mein response nahi aaya toh error
        print(f"    📥 Fetching: {url[:50]}...")
        resp = requests.get(url, headers=HEADERS, timeout=10)
        
        # Step 2: Status code check karo
        # 200 = Success, anything else = Error
        if resp.status_code != 200:
            print(f"    ❌ Failed: HTTP {resp.status_code}")
            return "", None
        
        # Step 3: HTML parse karo
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # Step 4: Clean text banao aur return karo
        clean = clean_text(soup)
        print(f"    ✅ Scraped {len(clean)} characters")
        
        return clean, soup
        
    except Exception as e:
        # Error handling - kuch bhi galat hua toh empty return karo
        print(f"    ❌ Scrape Error: {str(e)[:50]}")
        return "", None


# ============================================================================
# MAIN SCRAPER FUNCTION
# ============================================================================

def scrape_competitor(base_url):
    """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║  MAIN SCRAPER FUNCTION                                                    ║
    ║  Competitor website ka complete content scrape karta hai                 ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    
    YEH FUNCTION KYA KARTA HAI:
    1. Homepage scrape karta hai
    2. Important pages dhundhta hai (pricing, about, features, etc.)
    3. Un pages ko bhi scrape karta hai
    4. Sab content combine karta hai
    
    PARAMETERS:
    - base_url: Website ka main URL (e.g., "https://competitor.com")
    
    RETURNS:
    - Combined text of all scraped pages (max 50000 chars)
    
    WORKFLOW:
    ┌─────────────────────────────────────────────────────────────────┐
    │ scrape_competitor("https://example.com")                        │
    │                        ↓                                        │
    │ Homepage fetch karo                                             │
    │                        ↓                                        │
    │ Links dhundho (pricing, about, features, product, contact)      │
    │                        ↓                                        │
    │ Top 4 important pages fetch karo                                │
    │                        ↓                                        │
    │ Sab content combine karo                                        │
    │                        ↓                                        │
    │ Return combined text (max 50K chars)                            │
    └─────────────────────────────────────────────────────────────────┘
    """
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 1: URL Fix - https:// add karo agar missing hai
    # ═══════════════════════════════════════════════════════════════════
    if not base_url.startswith('http'):
        base_url = 'https://' + base_url

    print(f"\n🔍 [SCRAPER] Starting scrape for: {base_url}")
    print("=" * 60)
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 2: Homepage scrape karo
    # ═══════════════════════════════════════════════════════════════════
    print("📄 Fetching Homepage...")
    home_text, home_soup = get_page_content(base_url)
    
    # Agar homepage hi nahi mila toh error return karo
    if not home_soup:
        print("❌ Failed to fetch homepage!")
        return "Failed to fetch website."

    # Combined context start karo homepage content ke saath
    combined_context = f"--- HOMEPAGE ({base_url}) ---\n{home_text}\n\n"

    # ═══════════════════════════════════════════════════════════════════
    # STEP 3: Important pages ke links dhundho
    # ═══════════════════════════════════════════════════════════════════
    print("\n🔗 Discovering important pages...")
    
    visited = set([base_url, base_url + '/'])  # Already visited URLs
    
    # Yeh keywords important pages identify karte hain
    keywords = ['pricing', 'plans', 'features', 'product', 'about', 'contact']
    links_to_visit = []

    # Homepage pe sabhi <a> tags check karo
    for a in home_soup.find_all('a', href=True):
        href = a['href']
        full_url = urljoin(base_url, href)  # Relative URL ko full URL banao
        
        # Sirf internal links (same domain)
        if urlparse(full_url).netloc != urlparse(base_url).netloc:
            continue
            
        # Check karo ki URL mein koi important keyword hai ya nahi
        if any(k in full_url.lower() for k in keywords):
            if full_url not in visited and full_url not in links_to_visit:
                links_to_visit.append(full_url)
                visited.add(full_url)
                print(f"    Found: {full_url}")
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 4: Top 4 important pages scrape karo
    # ═══════════════════════════════════════════════════════════════════
    # Speed ke liye sirf 4 pages (homepage + 4 = 5 total)
    links_to_visit = links_to_visit[:4]
    
    print(f"\n📄 Fetching {len(links_to_visit)} additional pages...")
    
    for link in links_to_visit:
        text, _ = get_page_content(link)
        if text:
            # Section name dhundho based on keyword
            section = "PAGE"
            for k in keywords:
                if k in link.lower(): 
                    section = k.upper()
                    break
            
            # Combined context mein add karo
            combined_context += f"--- {section} ({link}) ---\n{text}\n\n"

    # ═══════════════════════════════════════════════════════════════════
    # STEP 5: Final result return karo
    # ═══════════════════════════════════════════════════════════════════
    result = combined_context[:50000]  # 50K char limit
    
    print("=" * 60)
    print(f"✅ [SCRAPER] Complete! Total: {len(result)} characters")
    print("=" * 60 + "\n")
    
    return result

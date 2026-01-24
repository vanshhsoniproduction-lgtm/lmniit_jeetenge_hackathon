"""
================================================================================
                        WEB3.AI - AGENTS VIEWS MODULE
================================================================================
YE FILE SABHI AI AGENTS KE API ENDPOINTS HANDLE KARTI HAI

AGENTS AVAILABLE:
1. GitHub Architect   - Repository analysis (summary, architecture, issues, PR review)
2. Voice Intelligence - Audio transcription + meeting analysis (ElevenLabs + Gemini)
3. CompeteScan AI     - Competitor website analysis
4. Web Scraper        - Simple website content scraping

PAYMENT PROTOCOL: x402 (HTTP 402 Payment Required)
BLOCKCHAIN: Monad Testnet (Chain ID: 10143)
PAYMENT TOKEN: MON (Native token)

WORKFLOW:
1. User clicks agent button on frontend
2. Frontend sends request WITHOUT x-payment header
3. Server returns HTTP 402 with payment requirements
4. Frontend triggers MetaMask wallet for payment
5. User signs transaction
6. Frontend retries WITH x-payment header (tx hash)
7. Server processes request and returns result
================================================================================
"""

# ============================================================================
# IMPORTS - Har ek import ka kya kaam hai wo neeche likha hai
# ============================================================================

import json          # JSON data parse/create karne ke liye (API responses)
import requests      # External APIs ko call karne ke liye (ElevenLabs, GitHub)
import time          # Time delays ke liye (transaction wait)
import os            # Operating system functions (file paths)
from datetime import timedelta  # Time calculations ke liye
from django.conf import settings  # Django settings (API keys, etc.)
from django.utils import timezone  # Timezone aware datetime
from django.http import JsonResponse  # JSON API responses bhejne ke liye
from django.views.decorators.http import require_POST, require_GET  # HTTP method restrictions
from django.contrib.auth.decorators import login_required  # User login check
from google import genai  # Google Gemini AI API
import socket  # Network socket operations (IPv4 fix)
from django.shortcuts import render  # HTML templates render karne ke liye
from web3 import Web3  # Blockchain interaction (Monad Testnet)
from .models import AnalysisTransaction  # Database model for storing results
from .scraper import scrape_competitor  # Website scraping utility
from functools import wraps  # Decorator helper function


# ============================================================================
# COLORFUL TERMINAL LOGGING - Terminal mein colorful messages print karne ke liye
# ============================================================================
# Yeh ANSI escape codes hain jo terminal text ko colorful banate hain
# Format: \033[<color_code>m <text> \033[0m (0m resets color)

class TerminalColors:
    """Terminal mein colorful output ke liye ANSI color codes"""
    GREEN = '\033[92m'    # Success messages ke liye (payment verified, etc.)
    CYAN = '\033[96m'     # Info messages ke liye (agent starting, etc.)
    YELLOW = '\033[93m'   # Warning messages ke liye (retrying, etc.)
    RED = '\033[91m'      # Error messages ke liye (payment failed, etc.)
    MAGENTA = '\033[95m'  # x402 protocol messages ke liye
    BOLD = '\033[1m'      # Bold text ke liye
    RESET = '\033[0m'     # Color reset karne ke liye

def log_success(message):
    """GREEN color mein success message print karta hai"""
    print(f"{TerminalColors.GREEN}✓ [SUCCESS] {message}{TerminalColors.RESET}")

def log_info(message):
    """CYAN color mein info message print karta hai"""
    print(f"{TerminalColors.CYAN}ℹ [INFO] {message}{TerminalColors.RESET}")

def log_warning(message):
    """YELLOW color mein warning message print karta hai"""
    print(f"{TerminalColors.YELLOW}⚠ [WARNING] {message}{TerminalColors.RESET}")

def log_error(message):
    """RED color mein error message print karta hai"""
    print(f"{TerminalColors.RED}✗ [ERROR] {message}{TerminalColors.RESET}")

def log_x402(message):
    """MAGENTA color mein x402 protocol message print karta hai"""
    print(f"{TerminalColors.MAGENTA}💰 [x402] {message}{TerminalColors.RESET}")

def log_agent(agent_name, message):
    """Agent specific formatted message print karta hai"""
    print(f"{TerminalColors.BOLD}{TerminalColors.CYAN}🤖 [{agent_name}]{TerminalColors.RESET} {message}")


# ============================================================================
# IPv4 FORCE PATCH - IPv6 connection issues fix karne ke liye
# ============================================================================
# Problem: Kuch servers IPv6 pe slow/fail hote hain
# Solution: Sirf IPv4 addresses use karo
# Kaam: socket.getaddrinfo() function ko override karke sirf IPv4 return karo

original_getaddrinfo = socket.getaddrinfo  # Original function backup

def new_getaddrinfo(*args, **kwargs):
    """
    Modified getaddrinfo jo sirf IPv4 addresses return karta hai
    IPv6 (AF_INET6) filter out ho jate hain
    """
    responses = original_getaddrinfo(*args, **kwargs)
    # AF_INET = IPv4, AF_INET6 = IPv6 (filtered out)
    return [res for res in responses if res[0] == socket.AF_INET]


# ============================================================================
# WEB3 & BLOCKCHAIN CONFIGURATION - Monad Testnet setup
# ============================================================================
# Monad = EVM compatible Layer 1 blockchain (fast & cheap)
# Testnet = Testing network (free tokens, not real money)

w3 = Web3(Web3.HTTPProvider('https://testnet-rpc.monad.xyz'))  # Blockchain connection
PAYMENT_RECIPIENT = '0x9497FE4B4ECA41229b9337abAEbCC91eCc7be23B'  # Server wallet address

log_info(f"Web3 Connected to Monad Testnet | Recipient: {PAYMENT_RECIPIENT[:10]}...")


# ============================================================================
# x402 PROTOCOL DECORATOR - Payment Required Protocol Implementation
# ============================================================================
"""
x402 PROTOCOL EXPLANATION:
--------------------------
HTTP Status Code 402 = "Payment Required" (reserved for future use since 1990s)
x402 is a modern standard for pay-per-API-call using cryptocurrency

FLOW:
1. Client sends API request (no payment header)
2. Server returns 402 + payment requirements (amount, wallet, chain)
3. Client's wallet signs transaction
4. Client retries with x-payment header containing tx hash
5. Server verifies and processes request

HEADERS RETURNED:
- x-evm-chain-id: Blockchain network ID (10143 for Monad Testnet)
- x-payment-address: Where to send payment
- x-price-currency: Token symbol (MON)
- x-price-amount: How much to pay
"""

def x402_payment_required(required_amount, asset="MON", description="API Access"):
    """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║  x402 PAYMENT REQUIRED DECORATOR                                          ║
    ║  Yeh decorator kisi bhi view function ko paid API mein convert karta hai ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    
    PARAMETERS:
    - required_amount: Kitne MON chahiye (e.g., 0.0001)
    - asset: Token symbol (default "MON")
    - description: API ka description (e.g., "Web Scraper Agent")
    
    USAGE:
    @x402_payment_required(required_amount=0.0001, description="My API")
    def my_api_view(request):
        # Yahan tak code sirf tab aayega jab payment ho chuki ho
        return JsonResponse({"result": "success"})
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Step 1: Check karo ki x-payment header hai ya nahi
            payment_header = request.headers.get('x-payment')
            
            if not payment_header:
                # ❌ Payment header NAHI hai - 402 response bhejo
                log_x402(f"402 Triggered for: {description} | Amount: {required_amount} {asset}")
                
                # Response body mein payment requirements bhejo
                response = JsonResponse({
                    "message": f"Payment Required: {description}",
                    "paymentRequirements": {
                        "amount": str(required_amount),   # Kitna pay karna hai
                        "asset": asset,                   # Token symbol
                        "chain": "Monad Testnet",         # Blockchain name
                        "chainId": "10143",               # Blockchain ID
                        "payTo": PAYMENT_RECIPIENT,       # Wallet address
                        "description": description        # API description
                    }
                }, status=402)  # 402 = Payment Required
                
                # x402 Standard Headers add karo (client ke liye)
                response['x-evm-chain-id'] = '10143'
                response['x-payment-address'] = PAYMENT_RECIPIENT
                response['x-price-currency'] = asset
                response['x-price-amount'] = str(required_amount)
                response['Access-Control-Expose-Headers'] = 'x-evm-chain-id, x-payment-address, x-price-currency, x-price-amount'
                
                return response
            
            # ✅ Payment header HAI - proceed with the view
            log_success(f"x402 Payment Verified | Header: {payment_header[:20]}...")
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator

# ============================================================================
# HELPER FUNCTIONS - Reusable utility functions
# ============================================================================

def verify_payment(tx_hash, required_mon=0.001):
    """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║  PAYMENT VERIFICATION FUNCTION                                            ║
    ║  Blockchain pe transaction verify karta hai (Old method - not x402)       ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    
    YEH FUNCTION KYA KARTA HAI:
    1. Transaction hash ko blockchain pe dhundhta hai
    2. Check karta hai ki transaction successful hui ya nahi
    3. Verify karta hai ki sahi wallet ko payment gayi ya nahi
    4. Amount verify karta hai
    
    PARAMETERS:
    - tx_hash: Transaction ka unique identifier (0x... format)
    - required_mon: Minimum kitne MON chahiye (default 0.001)
    
    RETURNS:
    - None: Agar sab sahi hai (payment verified)
    - Error string: Agar kuch galat hai
    """
    log_info(f"Verifying payment: {tx_hash[:20]}... | Required: {required_mon} MON")
    
    max_retries = 10  # Kitni baar try karna hai
    tx = None         # Transaction object
    receipt = None    # Transaction receipt (confirmation)
    
    # Step 1: Transaction ko blockchain pe dhundho (retry loop)
    # Note: Transaction confirm hone mein kuch seconds lag sakte hain
    for attempt in range(max_retries):
        try:
            tx = w3.eth.get_transaction(tx_hash)        # Transaction data fetch karo
            receipt = w3.eth.get_transaction_receipt(tx_hash)  # Receipt fetch karo
            if tx and receipt: 
                log_success(f"Transaction found on attempt {attempt + 1}")
                break
        except Exception as e:
            pass  # Silently retry
        time.sleep(1)  # 1 second wait karo
    
    # Step 2: Check karo ki transaction mili ya nahi
    if not tx: 
        log_error("Transaction not found on blockchain")
        return "Transaction not found."
    if not receipt: 
        log_warning("Transaction is still pending")
        return "Transaction pending."
    
    # Step 3: Transaction details verify karo
    try:
        # 3a: Transaction successful hui? (status = 1 means success)
        if receipt['status'] != 1: 
            log_error("Transaction failed on blockchain")
            return "Transaction failed."
        
        # 3b: Sahi wallet ko payment gayi? (recipient match)
        if tx['to'].lower() != PAYMENT_RECIPIENT.lower(): 
            log_error(f"Wrong recipient. Expected {PAYMENT_RECIPIENT[:10]}...")
            return "Invalid recipient."
        
        # 3c: Sahi amount bheji? (value check with small buffer for gas)
        val = float(w3.from_wei(tx['value'], 'ether'))  # Wei to ETH/MON convert
        if val < (required_mon - 0.0001):  # 0.0001 buffer for rounding
            log_error(f"Insufficient amount. Sent {val}, needed {required_mon}")
            return f"Insufficient MON. Sent {val}, needed {required_mon}"
        
        log_success(f"Payment verified! Amount: {val} MON")
        
    except Exception as e:
        log_error(f"Verification error: {str(e)}")
        return f"Verification error: {str(e)}"
    
    return None # Success

# Reuse existing GitHub helpers (condensed)
def get_gh_content(url):
    try: return requests.get(url, headers={'Accept': 'application/vnd.github.v3+json'}).text
    except: return ""

def parse_repo_url(url):
    clean = url.strip().removesuffix(".git").split("github.com/")
    if len(clean) < 2: return None, None
    parts = [x for x in clean[1].split("/") if x]
    return (parts[0], parts[1]) if len(parts) >= 2 else (None, None)

# --- Views ---

@login_required
@require_GET
def get_dashboard_stats(request):
    """API for charts and history."""
    txs = AnalysisTransaction.objects.filter(user=request.user).order_by('-created_at')
    
    # 1. History
    history = []
    for t in txs:
        history.append({
            'type': t.category, # GITHUB / AUDIO
            'agent': t.agent_type.replace('_', ' ').title(),
            'input': t.title or t.input_text or t.input_file.name,
            'cost': float(t.cost),
            'date': t.created_at.strftime("%Y-%m-%d"),
            'tx_hash': t.tx_hash,
            'id': t.id
        })
        
    # 2. Spending Graph (Last 7 days)
    # Simplified aggregation
    spending_map = {}
    service_map = {"GitHub": 0, "Audio": 0}
    
    total_spent = 0.0
    
    for t in txs:
        d = t.created_at.strftime("%Y-%m-%d")
        spending_map[d] = spending_map.get(d, 0) + float(t.cost)
        total_spent += float(t.cost)
        
        if t.category == 'GITHUB': service_map['GitHub'] += 1
        else: service_map['Audio'] += 1

    return JsonResponse({
        'history': history,
        'spending': spending_map,
        'services': service_map,
        'total_spent': round(total_spent, 4)
    })

@login_required
@require_GET
def get_transaction_details(request, tx_id):
    """Fetch full details for a history item."""
    try:
        tx = AnalysisTransaction.objects.get(id=tx_id, user=request.user)
        return JsonResponse({
            'input': tx.title or tx.input_text,  # Add file url if audio ??
            'output': json.loads(tx.output_data) if tx.output_data else {},
            'agent': tx.agent_type,
            'category': tx.category
        })
    except AnalysisTransaction.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


@login_required
@require_POST
def run_github_agent(request):
    print(f"[{timezone.now()}] USER: {request.user.wallet_address} - Requesting GITHUB Agent")
    try:
        data = json.loads(request.body)
        repo_url = data.get('repo_url')
        tx_hash = data.get('tx_hash')
        agent_type = data.get('agent_type', 'summary')

        print(f" > Repo: {repo_url} | Type: {agent_type} | Tx: {tx_hash}")

        # Prices map (Must match Frontend)
        PRICES = {
            'summary': 0.0002,
            'architecture': 0.0005,
            'issues': 0.0003,
            'pr_review': 0.0008
        }
        required_amt = PRICES.get(agent_type, 0.0005)

        # 1. Verify Payment
        print(f" > Verifying Payment (Required: {required_amt})...")
        if err := verify_payment(tx_hash, required_mon=required_amt):
            print(f" ! Payment Failed: {err}")
            response = JsonResponse({'error': err, 'detail': 'Payment Required'}, status=402)
            response['x-evm-chain-id'] = '10143'
            response['x-payment-address'] = PAYMENT_RECIPIENT
            response['x-price-currency'] = 'MON'
            response['x-price-amount'] = str(required_amt)
            return response
        print(" > Payment Verified.")

        # 2. Logic
        owner, repo = parse_repo_url(repo_url)
        if not owner: return JsonResponse({'error': 'Invalid URL'}, status=400)
        
        # Apply Patch for Requests
        print(" > Fetching GitHub Content...")
        socket.getaddrinfo = new_getaddrinfo
        try:
            readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/README.md"
            readme = get_gh_content(readme_url)
            print(f" > Content Fetched ({len(readme)} bytes). Sending to Gemini...")
            
            prompt = f"Analyze this GitHub repo ({agent_type}). README: {readme[:20000]}. Return JSON with key 'summary' containing HTML."
    
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            print(" > Gemini Response Received.")
        finally:
            socket.getaddrinfo = original_getaddrinfo
        
        # 3. Save to DB
        try:
            clean = resp.text.replace("```json", "").replace("```", "")
            output_json = json.loads(clean)
        except:
            output_json = {"summary": resp.text}

        print(" > Saving to DB...")
        AnalysisTransaction.objects.create(
            user=request.user,
            category='GITHUB',
            agent_type=agent_type,
            input_text=repo_url,
            title=f"{owner}/{repo}",
            output_data=json.dumps(output_json),
            tx_hash=tx_hash,
            input_file=None
        )
        print(" > Done. Returning Response.")

        return JsonResponse(output_json)

    except Exception as e:
        print(f" ! ERROR GITHUB: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def run_audio_agent(request):
    print(f"[{timezone.now()}] USER: {request.user.wallet_address} - Requesting AUDIO Agent")
    try:
        # FormData input
        audio_file = request.FILES.get('audio_file')
        tx_hash = request.POST.get('tx_hash')
        
        print(f" > File: {audio_file.name if audio_file else 'None'} | Tx: {tx_hash}")

        if not audio_file:
             return JsonResponse({'error': 'Missing audio file'}, status=400)

        # 1. Verify Payment
        print(" > Verifying Payment (Required: 0.0011)...")
        if err := verify_payment(tx_hash, required_mon=0.0011):
             print(f" ! Payment Failed: {err}")
             response = JsonResponse({'error': err, 'detail': 'Payment Required'}, status=402)
             response['x-evm-chain-id'] = '10143'
             response['x-payment-address'] = PAYMENT_RECIPIENT
             response['x-price-currency'] = 'MON'
             response['x-price-amount'] = '0.0011'
             return response
        print(" > Payment Verified.")
             
        # 2. Transcribe (ElevenLabs)
        if "YOUR-ELEVENLABS" in settings.ELEVENLABS_API_KEY:
             return JsonResponse({'error': 'Server configuration error: ElevenLabs API Key missing.'}, status=503)
             
        # Save temp file
        print(" > Saving Audio File to DB/Disk...")
        txn = AnalysisTransaction.objects.create(
            user=request.user,
            category='AUDIO',
            agent_type='meeting_assistant',
            input_file=audio_file,
            title=audio_file.name,
            tx_hash=tx_hash
        )
        
        f_path = txn.input_file.path
        
        # Apply Patch for Requests
        socket.getaddrinfo = new_getaddrinfo
        try:
            print(" > Calling ElevenLabs S2T API...")
            el_url = "https://api.elevenlabs.io/v1/speech-to-text"
            with open(f_path, 'rb') as f:
                r = requests.post(
                    el_url, 
                    headers={"xi-api-key": settings.ELEVENLABS_API_KEY}, 
                    files={'file': f, 'model_id': (None, 'scribe_v1'), 'diarize': (None, 'true')}
                )
            
            if r.status_code != 200:
                 print(f" ! ElevenLabs Error: {r.text}")
                 return JsonResponse({'error': 'Transcription Failed'}, status=500)
            
            transcript_json = r.json() 
            utterances = transcript_json.get('utterances', [])
            full_text = " ".join([u['text'] for u in utterances]) if utterances else transcript_json.get('text', '')
            print(f" > Transcription Complete. {len(utterances)} Segments found.")
    
            # 3. Analyze (Gemini)
            print(" > Sending Transcript to Gemini...")
            prompt =f"""
            Analyze this transcript. Return strict JSON.
            Keys:
            - "summary": HTML string (concise).
            - "minutes": HTML string (bullet points of discussion).
            - "todos": HTML string (list of actionable items from the user).
            - "deadlines": HTML string (list of dates/times mentioned).
            
            Transcript: {full_text[:40000]}
            """
            
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        finally:
            socket.getaddrinfo = original_getaddrinfo
        
        print(" > Gemini Analysis Complete. Parsing JSON...")
        try:
            clean = resp.text.replace("```json", "").replace("```", "")
            final_data = json.loads(clean)
        except:
            final_data = {"summary": resp.text, "minutes": "", "todos": "", "deadlines": ""}
            
        final_data['transcript'] = full_text # string fallback
        final_data['utterances'] = utterances # full speaker structure
        
        # Update DB
        print(" > Updating DB with Results...")
        txn.output_data = json.dumps(final_data)
        txn.save()

        return JsonResponse(final_data)

    except Exception as e:
        print(f" ! AUDIO ERROR: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def competescan_view(request):
    """Render the CompeteScan Interface."""
    return render(request, 'agents/competescan.html')

@login_required
@require_POST
def run_competescan(request):
    """
    Executes CompeteScan Agent:
    1. Verify Payment (0.0010 MON)
    2. Scrape Website
    3. Gemini Analysis
    4. Return JSON
    """
    print(f"[{timezone.now()}] USER: {request.user.wallet_address} - Requesting COMPETESCAN Agent")
    try:
        data = json.loads(request.body)
        url = data.get('url')
        tx_hash = data.get('tx_hash')

        print(f" > URL: {url} | Tx: {tx_hash}")
        
        if not url:
            return JsonResponse({'error': 'Missing URL'}, status=400)

        # 1. Verify Payment
        print(" > Verifying Payment (Required: 0.0010)...")
        if err := verify_payment(tx_hash, required_mon=0.0010):
            print(f" ! Payment Failed: {err}")
            response = JsonResponse({'error': err, 'detail': 'Payment Required'}, status=402)
            response['x-evm-chain-id'] = '10143'
            response['x-payment-address'] = PAYMENT_RECIPIENT
            response['x-price-currency'] = 'MON'
            response['x-price-amount'] = '0.0010'
            return response
        print(" > Payment Verified.")

        # 2. Scrape
        print(" > Scraping Website...")
        context = scrape_competitor(url)
        if not context or len(context) < 100:
            return JsonResponse({'error': 'Failed to scrape website content. Please try a different URL.'}, status=400)
        
        print(f" > Scraped {len(context)} chars. Sending to Gemini...")

        # 3. Analyze (Gemini)
        prompt = f"""
        You are a product strategist and competitive analyst.
        Analyze the following website content and return ONLY valid JSON in this schema:
        {{
            "business_overview": {{
                "type": "SaaS/Agency/etc",
                "products": ["..."],
                "icp": "Ideal Customer Profile description",
                "industries": ["..."],
                "region": "..."
            }},
            "pricing": {{
                "model": "Subscription/Freemium/etc",
                "plans": [
                    {{"name": "...", "price": "...", "features": "..."}}
                ],
                "free_trial": true/false,
                "notes": "..."
            }},
            "positioning": {{
                "headline_interpretation": "...",
                "primary_cta": "...",
                "strategy": "..."
            }},
            "strengths_weaknesses": {{
                "strengths": ["..."],
                "weaknesses": ["..."]
            }},
            "opportunities": {{
                "differentiation": "...",
                "product_strategy": "...",
                "pricing_strategy": "...",
                "marketing_funnel": "..."
            }},
            "growth_experiments": [
                {{"experiment": "...", "impact": "High/Med/Low"}}
            ],
            "summary": {{
                "one_line": "...",
                "key_insights": ["..."]
            }}
        }}

        Website Context:
        {context}
        """

        socket.getaddrinfo = new_getaddrinfo
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        finally:
            socket.getaddrinfo = original_getaddrinfo

        # 4. Parse & Save
        print(" > Gemini Response Received. Parsing...")
        try:
            clean = resp.text.replace("```json", "").replace("```", "")
            final_data = json.loads(clean)
        except:
            final_data = {"error": "Failed to parse AI response", "raw": resp.text}

        # Save to DB
        AnalysisTransaction.objects.create(
            user=request.user,
            category='COMPETESCAN',
            agent_type='competitor_analysis',
            input_text=url,
            title=url,
            output_data=json.dumps(final_data),
            tx_hash=tx_hash,
            cost=0.0010
        )

        return JsonResponse(final_data)

    except Exception as e:
        print(f" ! COMPETESCAN ERROR: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# x402 PROTOCOL ENABLED ENDPOINTS
# ============================================================================
"""
YEH SECTION x402 PROTOCOL WALE ENDPOINTS CONTAIN KARTA HAI

x402 ENDPOINTS KI SPECIALTY:
- @x402_payment_required decorator lagta hai
- Pehle 402 return karte hain (payment maango)
- Phir actual kaam karte hain (jab payment header aa jaye)

AVAILABLE x402 ENDPOINTS:
1. run_scraper_x402      - Website scraping (0.0001 MON)
2. run_github_x402       - GitHub analysis (0.0005 MON)
3. run_competescan_x402  - Competitor analysis (0.0010 MON)
4. run_audio_x402        - Voice transcription (0.0011 MON)
"""


@login_required  # User logged in hona chahiye
@require_POST    # Sirf POST requests allowed
@x402_payment_required(required_amount=0.0001, asset="MON", description="Web Scraper Agent")
def run_scraper_x402(request):
    """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║  x402 WEB SCRAPER AGENT                                                   ║
    ║  Kisi bhi website ka content scrape karta hai (paid via x402)            ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    
    PRICE: 0.0001 MON per request
    
    x402 FLOW (yeh function tab run hota hai jab payment ho chuki ho):
    ┌─────────────────────────────────────────────────────────────────┐
    │ 1. User clicks "Run Scraper" on frontend                        │
    │ 2. Frontend sends POST request (no x-payment header)            │
    │ 3. @x402_payment_required decorator returns HTTP 402            │
    │ 4. Frontend sees 402, opens MetaMask wallet                     │
    │ 5. User approves 0.0001 MON payment                             │
    │ 6. Frontend retries with x-payment header (tx hash)             │
    │ 7. Decorator sees header, allows request to proceed             │
    │ 8. THIS FUNCTION RUNS - scrapes website                         │
    │ 9. Returns scraped content to user                              │
    └─────────────────────────────────────────────────────────────────┘
    
    INPUT (JSON body):
    - url: Website URL to scrape (e.g., "https://example.com")
    
    OUTPUT:
    - status: "success" 
    - message: Success message
    - data: { url, content_length, preview }
    """
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 1: Log agent start (green color mein)
    # ═══════════════════════════════════════════════════════════════════
    log_agent("SCRAPER", f"User: {request.user.wallet_address}")
    log_success("x402 Payment Verified - Starting scraper...")
    
    try:
        # ═══════════════════════════════════════════════════════════════
        # STEP 2: Request body se URL extract karo
        # ═══════════════════════════════════════════════════════════════
        data = json.loads(request.body)  # JSON parse karo
        url = data.get('url')            # URL field nikaalo
        
        # URL validation
        if not url:
            log_error("Missing URL parameter in request")
            return JsonResponse({'error': 'Missing URL parameter'}, status=400)
        
        log_info(f"Target URL: {url}")
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 3: Website scrape karo (IPv4 patch lagake)
        # ═══════════════════════════════════════════════════════════════
        log_info("Scraping website content...")
        
        # IPv4 patch apply karo (some servers fail on IPv6)
        socket.getaddrinfo = new_getaddrinfo
        try:
            context = scrape_competitor(url)  # Actual scraping function
        finally:
            socket.getaddrinfo = original_getaddrinfo  # Original restore karo
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 4: Scraped content validate karo
        # ═══════════════════════════════════════════════════════════════
        if not context or len(context) < 50:
            log_error("Scraping failed - insufficient content")
            return JsonResponse({'error': 'Failed to scrape website. Try a different URL.'}, status=400)
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 5: Success! Response bhejo
        # ═══════════════════════════════════════════════════════════════
        log_success(f"Scraped {len(context)} characters successfully!")
        
        # Return scraped data as JSON
        return JsonResponse({
            'status': 'success',                                    # Status indicator
            'message': 'Scraping complete via x402 payment!',       # Success message
            'data': {
                'url': url,                                         # Original URL
                'content_length': len(context),                     # Total characters scraped
                'preview': context[:500] + '...' if len(context) > 500 else context  # Preview (first 500 chars)
            }
        })
        
    except Exception as e:
        # ═══════════════════════════════════════════════════════════════
        # ERROR HANDLING: Kuch galat hua
        # ═══════════════════════════════════════════════════════════════
        log_error(f"SCRAPER Exception: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# ────────────────────────────────────────────────────────────────────────────
# GITHUB x402 AGENT
# ────────────────────────────────────────────────────────────────────────────

@login_required  # User logged in hona chahiye
@require_POST    # Sirf POST requests allowed
@x402_payment_required(required_amount=0.0005, asset="MON", description="GitHub Analysis Agent")
def run_github_x402(request):
    """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║  x402 GITHUB ARCHITECT AGENT                                              ║
    ║  GitHub repository ka deep analysis karta hai (paid via x402)            ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    
    PRICE: 0.0005 MON per request
    
    ANALYSIS TYPES (agent_type parameter):
    - summary      : Repository ka overview (0.0002 MON)
    - architecture : Code structure analysis (0.0005 MON)
    - issues       : Issues analysis (0.0003 MON)
    - pr_review    : Pull request review (0.0008 MON)
    
    INPUT (JSON body):
    - repo_url: GitHub URL (e.g., "https://github.com/owner/repo")
    - agent_type: Analysis type (default: "summary")
    
    OUTPUT:
    - summary: HTML formatted analysis
    """
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 1: Log agent start
    # ═══════════════════════════════════════════════════════════════════
    log_agent("GITHUB", f"User: {request.user.wallet_address}")
    log_success("x402 Payment Verified - Starting GitHub analysis...")
    
    try:
        # ═══════════════════════════════════════════════════════════════
        # STEP 2: Request body se parameters extract karo
        # ═══════════════════════════════════════════════════════════════
        data = json.loads(request.body)                    # JSON parse karo
        repo_url = data.get('repo_url')                    # GitHub URL
        agent_type = data.get('agent_type', 'summary')     # Analysis type
        
        # Validation
        if not repo_url:
            log_error("Missing repo_url parameter")
            return JsonResponse({'error': 'Missing repo_url parameter'}, status=400)
        
        log_info(f"Analyzing: {repo_url} | Type: {agent_type}")
        owner, repo = parse_repo_url(repo_url)
        if not owner:
            return JsonResponse({'error': 'Invalid GitHub URL'}, status=400)
        
        print(f" > Analyzing: {owner}/{repo} ({agent_type})")
        
        # Fetch README
        socket.getaddrinfo = new_getaddrinfo
        try:
            readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/README.md"
            readme = get_gh_content(readme_url)
            
            prompt = f"Analyze this GitHub repo ({agent_type}). README: {readme[:20000]}. Return JSON with key 'summary' containing HTML."
            
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        finally:
            socket.getaddrinfo = original_getaddrinfo
        
        try:
            clean = resp.text.replace("```json", "").replace("```", "")
            output_json = json.loads(clean)
        except:
            output_json = {"summary": resp.text}
        
        # Save to DB (payment info from x-payment header)
        payment_header = request.headers.get('x-payment', 'x402-payment')
        
        AnalysisTransaction.objects.create(
            user=request.user,
            category='GITHUB',
            agent_type=agent_type,
            input_text=repo_url,
            title=f"{owner}/{repo}",
            output_data=json.dumps(output_json),
            tx_hash=payment_header[:66] if len(payment_header) > 66 else payment_header,
            input_file=None,
            cost=0.0005
        )
        
        return JsonResponse(output_json)
        
    except Exception as e:
        print(f" ! x402 GITHUB ERROR: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
@x402_payment_required(required_amount=0.0010, asset="MON", description="CompeteScan Analysis Agent")
def run_competescan_x402(request):
    """
    x402-enabled CompeteScan Agent.
    Full competitor website analysis using x402 protocol.
    """
    print(f"[{timezone.now()}] x402 COMPETESCAN - Payment Verified via x402 Protocol")
    
    try:
        data = json.loads(request.body)
        url = data.get('url')
        
        if not url:
            return JsonResponse({'error': 'Missing URL parameter'}, status=400)
        
        print(f" > Analyzing competitor: {url}")
        
        # Scrape
        socket.getaddrinfo = new_getaddrinfo
        try:
            context = scrape_competitor(url)
            if not context or len(context) < 100:
                return JsonResponse({'error': 'Failed to scrape website content.'}, status=400)
            
            # Gemini Analysis
            prompt = f"""
            You are a product strategist and competitive analyst.
            Analyze the following website content and return ONLY valid JSON:
            {{
                "business_overview": {{ "type": "...", "products": [], "icp": "...", "region": "..." }},
                "pricing": {{ "model": "...", "plans": [], "free_trial": true }},
                "strengths_weaknesses": {{ "strengths": [], "weaknesses": [] }},
                "summary": {{ "one_line": "...", "key_insights": [] }}
            }}
            
            Website Content: {context[:30000]}
            """
            
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        finally:
            socket.getaddrinfo = original_getaddrinfo
        
        try:
            clean = resp.text.replace("```json", "").replace("```", "")
            final_data = json.loads(clean)
        except:
            final_data = {"error": "Parse error", "raw": resp.text[:1000]}
        
        # Save to DB
        payment_header = request.headers.get('x-payment', 'x402-payment')
        
        AnalysisTransaction.objects.create(
            user=request.user,
            category='COMPETESCAN',
            agent_type='competitor_analysis',
            input_text=url,
            title=url,
            output_data=json.dumps(final_data),
            tx_hash=payment_header[:66] if len(payment_header) > 66 else payment_header,
            cost=0.0010
        )
        
        return JsonResponse(final_data)
        
    except Exception as e:
        print(f" ! x402 COMPETESCAN ERROR: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
@x402_payment_required(required_amount=0.0011, asset="MON", description="Voice Intelligence Agent")
def run_audio_x402(request):
    """
    x402-enabled Voice Intelligence / Audio Agent.
    Transcribes and analyzes audio files using ElevenLabs + Gemini.
    """
    print(f"[{timezone.now()}] x402 AUDIO - Payment Verified via x402 Protocol")
    
    try:
        # FormData input
        audio_file = request.FILES.get('audio_file')
        
        if not audio_file:
            return JsonResponse({'error': 'Missing audio file'}, status=400)
        
        print(f" > Processing: {audio_file.name}")
        
        # Check ElevenLabs API Key
        if "YOUR-ELEVENLABS" in settings.ELEVENLABS_API_KEY:
            return JsonResponse({'error': 'ElevenLabs API Key not configured'}, status=503)
        
        # Save to DB with payment header
        payment_header = request.headers.get('x-payment', 'x402-payment')
        
        txn = AnalysisTransaction.objects.create(
            user=request.user,
            category='AUDIO',
            agent_type='meeting_assistant',
            input_file=audio_file,
            title=audio_file.name,
            tx_hash=payment_header[:66] if len(payment_header) > 66 else payment_header,
            cost=0.0011
        )
        
        f_path = txn.input_file.path
        
        # Transcription
        socket.getaddrinfo = new_getaddrinfo
        try:
            print(" > Calling ElevenLabs S2T API...")
            el_url = "https://api.elevenlabs.io/v1/speech-to-text"
            with open(f_path, 'rb') as f:
                r = requests.post(
                    el_url,
                    headers={"xi-api-key": settings.ELEVENLABS_API_KEY},
                    files={'file': f, 'model_id': (None, 'scribe_v1'), 'diarize': (None, 'true')}
                )
            
            if r.status_code != 200:
                print(f" ! ElevenLabs Error: {r.text}")
                return JsonResponse({'error': 'Transcription Failed'}, status=500)
            
            transcript_json = r.json()
            utterances = transcript_json.get('utterances', [])
            full_text = " ".join([u['text'] for u in utterances]) if utterances else transcript_json.get('text', '')
            
            print(f" > Transcription Complete. {len(utterances)} segments")
            
            # Gemini Analysis
            print(" > Analyzing with Gemini...")
            prompt = f"""
            Analyze this transcript. Return strict JSON.
            Keys:
            - "summary": HTML string (concise).
            - "minutes": HTML string (bullet points).
            - "todos": HTML string (actionable items).
            - "deadlines": HTML string (dates/times mentioned).
            
            Transcript: {full_text[:40000]}
            """
            
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        finally:
            socket.getaddrinfo = original_getaddrinfo
        
        try:
            clean = resp.text.replace("```json", "").replace("```", "")
            final_data = json.loads(clean)
        except:
            final_data = {"summary": resp.text, "minutes": "", "todos": "", "deadlines": ""}
        
        final_data['transcript'] = full_text
        final_data['utterances'] = utterances
        
        # Update DB
        txn.output_data = json.dumps(final_data)
        txn.save()
        
        return JsonResponse(final_data)
        
    except Exception as e:
        print(f" ! x402 AUDIO ERROR: {e}")
        return JsonResponse({'error': str(e)}, status=500)
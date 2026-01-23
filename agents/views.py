import json
import requests
import time
import os
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from google import genai
import socket
from web3 import Web3
from .models import AnalysisTransaction

# IPv4 Force Patch
original_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = original_getaddrinfo(*args, **kwargs)
    return [res for res in responses if res[0] == socket.AF_INET]


# Initialize Web3
w3 = Web3(Web3.HTTPProvider('https://ethereum-sepolia.publicnode.com'))
PAYMENT_RECIPIENT = '0x9497FE4B4ECA41229b9337abAEbCC91eCc7be23B'

# --- Helpers ---

def verify_payment(tx_hash, required_eth=0.001):
    """Verifies Sepolia transaction."""
    max_retries = 10
    tx = None
    receipt = None
    
    # 1. Wait for tx to appear
    for _ in range(max_retries):
        try:
            tx = w3.eth.get_transaction(tx_hash)
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if tx and receipt: break
        except:
            pass
        time.sleep(1)
        
    if not tx: return "Transaction not found."
    if not receipt: return "Transaction pending."
    
    try:
        if receipt['status'] != 1: return "Transaction failed."
        if tx['to'].lower() != PAYMENT_RECIPIENT.lower(): return "Invalid recipient."
        val = float(w3.from_wei(tx['value'], 'ether'))
        if val < (required_eth - 0.0001): # Small buffer
            return f"Insufficient ETH. Sent {val}, needed {required_eth}"
    except Exception as e:
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

        # 1. Verify Payment
        print(" > Verifying Payment...")
        if err := verify_payment(tx_hash):
            print(f" ! Payment Failed: {err}")
            return JsonResponse({'error': err}, status=400)
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

        if not audio_file or not tx_hash:
             return JsonResponse({'error': 'Missing file or Payment'}, status=400)

        # 1. Verify Payment
        print(" > Verifying Payment...")
        if err := verify_payment(tx_hash):
             print(f" ! Payment Failed: {err}")
             return JsonResponse({'error': err}, status=400)
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
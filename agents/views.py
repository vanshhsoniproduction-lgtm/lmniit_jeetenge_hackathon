import json
import requests
import time
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from google import genai
from web3 import Web3

# Initialize Web3 for Sepolia Testnet
w3 = Web3(Web3.HTTPProvider('https://ethereum-sepolia.publicnode.com'))
PAYMENT_RECIPIENT = '0x9497FE4B4ECA41229b9337abAEbCC91eCc7be23B'
PAYMENT_AMOUNT_ETH = 0.001

# --- GitHub Helpers ---

def parse_repo_url(repo_url):
    clean_url = repo_url.strip().removesuffix(".git")
    if "github.com/" not in clean_url:
        return None, None, "Invalid GitHub URL."
    parts = clean_url.split("github.com/")
    if len(parts) < 2: return None, None, "Invalid URL."
    owner_repo = [x for x in parts[1].split("/") if x]
    if len(owner_repo) < 2: return None, None, "Need owner/repo."
    return owner_repo[0], owner_repo[1], None

def fetch_github_api(url):
    headers = {'Accept': 'application/vnd.github.v3+json'}
    # Helper to add Auth if we had a token, but for public repos mostly fine strictly rate limited
    # If the user has a GH token in settings, use it.
    # headers['Authorization'] = f"token {settings.GITHUB_TOKEN}" 
    try:
        response = requests.get(url, headers=headers)
        return response
    except Exception as e:
        print(f"GH Fetch Error: {e}")
        return None

def get_file_content(owner, repo, file_path):
    # Try raw fetch first for speed
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{file_path}"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.text
    
    # Fallback to API if raw fails (e.g. private or weird branch)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    resp = fetch_github_api(api_url)
    if resp and resp.status_code == 200:
        import base64
        content = resp.json().get('content', '')
        return base64.b64decode(content).decode('utf-8')
    return None

def get_issue_context(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=open&sort=created&per_page=15"
    resp = fetch_github_api(url)
    if resp and resp.status_code == 200:
        issues = resp.json()
        text = "OPEN ISSUES LIST:\n"
        for i in issues:
            if 'pull_request' in i: continue # Skip PRs
            text += f"- Issue #{i['number']}: {i['title']}\n  Labels: {[l['name'] for l in i['labels']]}\n  Body: {i['body'][:200]}...\n\n"
        return text
    return "No issues found or API error."

def get_pr_context(owner, repo):
    # Get latest open PR
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=open&sort=updated&per_page=5"
    resp = fetch_github_api(url)
    if resp and resp.status_code == 200:
        prs = resp.json()
        if not prs: return "No open PRs found."
        
        # Analyze the most recently updated one
        pr = prs[0]
        text = f"ANALYZING PR #{pr['number']}: {pr['title']}\n"
        text += f"Description: {pr['body']}\n"
        
        # Fetch diff (simplified)
        diff_url = pr['diff_url']
        diff_resp = requests.get(diff_url)
        if diff_resp.status_code == 200:
            text += f"\nDIFF PREVIEW:\n{diff_resp.text[:5000]}" # Limit diff size
        return text
    return "Failed to fetch PRs."

def get_release_context(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=5"
    resp = fetch_github_api(url)
    if resp and resp.status_code == 200:
        releases = resp.json()
        if not releases: return "No releases found."
        text = "RECENT RELEASES:\n"
        for r in releases:
            text += f"- {r['tag_name']} ({r['published_at']}): {r['body'][:300]}...\n"
        return text
    return "Failed to fetch releases."

# --- Agent Logic ---

def get_agent_prompt(agent_type, owner, repo):
    """
    Constructs the prompt and fetches context based on agent type.
    """
    context = ""
    readme = get_file_content(owner, repo, "README.md") or ""
    
    # Common HTML formatting instruction
    fmt_instr = """
    Format output using clean HTML tags (no markdown):
    - <h3 class="text-xl font-bold mt-4 mb-2 text-indigo-700">Title</h3>
    - <p class="mb-2 text-slate-700">Text</p>
    - <ul class="list-disc pl-5 mb-4 space-y-1"><li>Item</li></ul>
    - <code class="bg-slate-100 px-2 py-1 rounded text-red-500 font-mono text-sm">Code</code>
    """

    if agent_type == 'setup_runner':
        context = readme[:40000]
        return f"""
        {fmt_instr}
        You are a Setup Helper. Analyze the README to extract precise setup steps.
        
        Output Sections:
        1. <h3>Prerequisites</h3> (node, python versions, etc)
        2. <h3>Installation</h3> (exact install commands)
        3. <h3>Running Locally</h3> (how to start dev server)
        4. <h3>Common Issues</h3> (potential pitfalls)

        Context: {context}
        """

    elif agent_type == 'architecture':
        # Simulating file tree for now using File Content or just README structure
        # A real recursive tree fetch is heavy. Let's rely on README description of architecture first.
        # If possible, we'd fetch the root file list.
        context = readme[:40000]
        return f"""
        {fmt_instr}
        You are a Senior Architect. Analyze the project structure and logic based on the documentation.
        
        Output Sections:
        1. <h3>High Level Architecture</h3>
        2. <h3>Key Modules & Responsibilities</h3>
        3. <h3>Tech Stack & Data Flow</h3>
        
        Context (README): {context}
        """

    elif agent_type == 'contributing':
        contributing = get_file_content(owner, repo, "CONTRIBUTING.md") or ""
        context = (contributing + "\n\n" + readme)[:40000]
        return f"""
        {fmt_instr}
        You are a Community Manager. Explain how a new developer can contribute.
        
        Output Sections:
        1. <h3>Getting Started</h3>
        2. <h3>Environment Setup</h3>
        3. <h3>Pull Request Guildelines</h3>
        4. <h3>Testing Standards</h3>
        
        Context: {context}
        """

    elif agent_type == 'issues':
        context = get_issue_context(owner, repo)
        return f"""
        {fmt_instr}
        You are an Issue Triage Manager. Group and classify these open issues.
        
        Output Sections:
        1. <h3>Good First Issues</h3> (Beginner friendly)
        2. <h3>Critical Bugs</h3> (Urgent)
        3. <h3>Feature Requests</h3>
        
        Context: {context}
        """

    elif agent_type == 'pr_review':
        context = get_pr_context(owner, repo)
        return f"""
        {fmt_instr}
        You are a Senior Code Reviewer. Review the LATEST Open PR.
        
        Output Sections:
        1. <h3>PR Summary</h3> (What is changing?)
        2. <h3>Code Quality Assessment</h3>
        3. <h3>Potential Risks/Bugs</h3>
        4. <h3>Verdict</h3> (Approve/Request Changes)
        
        Context: {context}
        """

    elif agent_type == 'release_notes':
        context = get_release_context(owner, repo)
        return f"""
        {fmt_instr}
        You are a Release Manager. Summarize the recent changes.
        
        Output Sections:
        1. <h3>Latest Version</h3>
        2. <h3>Key Features Added</h3>
        3. <h3>Breaking Changes</h3> (If any)
        
        Context: {context}
        """
        
    elif agent_type == 'dependencies':
        pkg_json = get_file_content(owner, repo, "package.json") or ""
        req_txt = get_file_content(owner, repo, "requirements.txt") or ""
        go_mod = get_file_content(owner, repo, "go.mod") or ""
        context = f"Package.json:\n{pkg_json}\n\nRequirements.txt:\n{req_txt}\n\nGo.mod:\n{go_mod}"
        return f"""
        {fmt_instr}
        You are a Security Auditor. Analyze the dependencies.
        
        Output Sections:
        1. <h3>Main Dependencies</h3>
        2. <h3>Outdated/Risky Signals</h3> (Based on common knowledge)
        3. <h3>Security Recommendations</h3>
        
        Context: {context[:40000]}
        """
        
    elif agent_type == 'license':
        lic = get_file_content(owner, repo, "LICENSE") or get_file_content(owner, repo, "LICENSE.md") or ""
        return f"""
        {fmt_instr}
        You are a Legal Advisor. Analyze the license.
        
        Output Sections:
        1. <h3>License Type</h3>
        2. <h3>Key Permissions</h3> (Commercial use, modification, etc)
        3. <h3>Limitations & Conditions</h3>
        
        Context: {lic[:20000]}
        """

    # Default fallback (summary)
    else:
        context = readme[:40000]
        return f"""
        {fmt_instr}
        You are an expert developer. Summarize this repo.
        Include: Overview, Tech Stack, Key Features, Usage.
        Context: {context}
        """

# --- Main Logic ---

@login_required
@require_POST
def summarize_repo(request):
    try:
        data = json.loads(request.body)
        repo_url = data.get('repo_url')
        tx_hash = data.get('tx_hash')
        agent_type = data.get('agent_type', 'summary') # Default to summary
        
        if not repo_url:
            return JsonResponse({'error': 'Repository URL is required'}, status=400)
            
        if not tx_hash:
            return JsonResponse({'error': 'Payment required. Please pay 0.001 ETH.'}, status=402)

        # 0. Verify Sepolia Payment (with Retries)
        max_retries = 10
        tx = None
        receipt = None
        
        for attempt in range(max_retries):
            try:
                tx = w3.eth.get_transaction(tx_hash)
                receipt = w3.eth.get_transaction_receipt(tx_hash)
                if tx and receipt:
                    break
            except Exception:
                pass
            time.sleep(2) 
            
        if not tx:
             return JsonResponse({'error': 'Transaction not found on chain yet. Please wait.'}, status=400)
        
        if not receipt:
             return JsonResponse({'error': 'Transaction pending. Please wait for confirmation.'}, status=400)

        try:
            if receipt['status'] != 1: return JsonResponse({'error': 'Transaction failed.'}, status=400)
            if tx['to'].lower() != PAYMENT_RECIPIENT.lower(): return JsonResponse({'error': 'Invalid recipient.'}, status=400)
            value_eth = float(w3.from_wei(tx['value'], 'ether'))
            if value_eth < 0.00099: 
                 return JsonResponse({'error': f'Insufficient ETH. Sent {value_eth}, need 0.001'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Validation failed: {str(e)}'}, status=400)

        # 1. Parse URL/Fetch Context for Agent
        owner, repo, err = parse_repo_url(repo_url)
        if err: return JsonResponse({'error': err}, status=400)

        # 2. Get Prompt
        prompt = get_agent_prompt(agent_type, owner, repo)

        # 3. Call Gemini
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        try:
             response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
             return JsonResponse({'summary': response.text})
        except Exception:
             # Fallback
             response = client.models.generate_content(model='gemini-2.5-pro', contents=prompt)
             return JsonResponse({'summary': response.text})

    except Exception as e:
        print(f"Server Error: {e}")
        return JsonResponse({'error': f'Internal Error: {str(e)}'}, status=500)
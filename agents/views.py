import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from google import genai

def get_github_content(repo_url):
    """
    Extracts owner/repo from URL and fetches README content via GitHub API.
    """
    # Remove .git extension if present
    clean_url = repo_url.strip().removesuffix(".git")
    
    # Handle different URL formats
    if "github.com/" not in clean_url:
        return None, "Invalid GitHub URL. Must contain 'github.com/'"
        
    parts = clean_url.split("github.com/")
    
    if len(parts) < 2:
        return None, "Invalid GitHub URL"
    
    owner_repo = parts[1].split("/")
    # Filter out empty strings from trailing slashes
    owner_repo = [x for x in owner_repo if x]
    
    if len(owner_repo) < 2:
        return None, "Invalid GitHub URL format. Needed: github.com/owner/repo"
    
    owner = owner_repo[0]
    repo = owner_repo[1]
    
    # Fetch README Metadata
    api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    headers = {'Accept': 'application/vnd.github.v3.raw'}
    
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            return response.text, None
        elif response.status_code == 404:
            return None, "README not found in this repository."
        elif response.status_code == 403:
            return None, "GitHub API Rate Limit Exceeded. Try again later."
        else:
            return None, f"GitHub API Error: {response.status_code}"
    except Exception as e:
        return None, str(e)

@login_required
@require_POST
def summarize_repo(request):
    try:
        data = json.loads(request.body)
        repo_url = data.get('repo_url')
        
        if not repo_url:
            return JsonResponse({'error': 'Repository URL is required'}, status=400)

        # 1. Fetch README
        readme_content, error = get_github_content(repo_url)
        if error:
            return JsonResponse({'error': error}, status=400)
            
        # 2. Prepare Prompt
        # Truncate content to avoid token limits (1.5 Flash has ~1M context window, so this is safe)
        safe_content = readme_content[:40000] 
        
        prompt = f"""
        You are an expert developer assistant. Analyze the following GitHub README content and provide a structured summary.
        
        Format your response using clean HTML tags (no markdown, just HTML):
        - Use <h3 class="text-lg font-bold mt-4 mb-2"> for Section Titles.
        - Use <p class="mb-2"> for descriptions.
        - Use <ul class="list-disc pl-5 mb-4"> and <li> for features.
        - Use <code class="bg-slate-100 p-1 rounded text-sm text-red-500"> for commands/code.
        
        Sections to include:
        1. <h3>Project Overview</h3>: What is this project?
        2. <h3>Key Features</h3>: Bullet points of main capabilities.
        3. <h3>Tech Stack</h3>: Languages and frameworks used.
        4. <h3>How to Run</h3>: Installation/Run commands.
        
        README CONTENT:
        {safe_content}
        """

        # 3. Call Gemini API
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            # SWITCHED TO gemini-2.5-flash (New Standard)
            response = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=prompt
            )
            
            return JsonResponse({'summary': response.text})
            
        except Exception as ai_error:
            # Fallback to Pro if Flash fails
            try:
                print(f"Flash failed: {ai_error}, trying Pro...")
                response = client.models.generate_content(
                    model='gemini-2.5-pro',
                    contents=prompt
                )
                return JsonResponse({'summary': response.text})
            except Exception as e:
                print(f"Gemini API Error: {e}")
                return JsonResponse({'error': f'AI Generation Failed. Quota exceeded or API Key invalid.'}, status=500)

    except Exception as e:
        print(f"Server Error: {e}")
        return JsonResponse({'error': f'Internal Server Error: {str(e)}'}, status=500)
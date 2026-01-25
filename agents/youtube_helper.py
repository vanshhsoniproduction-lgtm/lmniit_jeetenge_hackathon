"""
================================================================================
                    YOUTUBE HELPER MODULE - Transcript Extraction
================================================================================
YE MODULE YOUTUBE VIDEO SE TRANSCRIPT NIKALNE KE LIYE HAI

MAIN FUNCTIONS:
1. extract_video_id() - YouTube URL se video ID nikalta hai
2. get_transcript()   - Video ka transcript fetch karta hai

SUPPORTED URL FORMATS:
- https://www.youtube.com/watch?v=VIDEO_ID
- https://youtu.be/VIDEO_ID
- https://www.youtube.com/embed/VIDEO_ID
- https://youtube.com/shorts/VIDEO_ID

REQUIRES: youtube-transcript-api>=1.0.0 (pip install youtube-transcript-api)
================================================================================
"""

import re

# youtube-transcript-api v1.2.x uses instance-based API
from youtube_transcript_api import YouTubeTranscriptApi


# ============================================================================
# TERMINAL COLORS - Colorful logging ke liye (same as views.py)
# ============================================================================

class TerminalColors:
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'

def log_yt(message):
    """YouTube agent specific log message"""
    print(f"{TerminalColors.MAGENTA}📺 [YT-DOCS] {message}{TerminalColors.RESET}")

def log_success(message):
    print(f"{TerminalColors.GREEN}✓ [SUCCESS] {message}{TerminalColors.RESET}")

def log_error(message):
    print(f"{TerminalColors.RED}✗ [ERROR] {message}{TerminalColors.RESET}")


# ============================================================================
# VIDEO ID EXTRACTION - Multiple URL formats support
# ============================================================================

def extract_video_id(youtube_url):
    """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║  YOUTUBE URL SE VIDEO ID EXTRACT KARTA HAI                                ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    
    SUPPORTED FORMATS:
    - https://www.youtube.com/watch?v=dQw4w9WgXcQ     → dQw4w9WgXcQ
    - https://youtu.be/dQw4w9WgXcQ                    → dQw4w9WgXcQ
    - https://www.youtube.com/embed/dQw4w9WgXcQ      → dQw4w9WgXcQ
    - https://youtube.com/shorts/dQw4w9WgXcQ         → dQw4w9WgXcQ
    
    RETURNS:
    - video_id (string) agar success
    - None agar invalid URL
    """
    log_yt(f"Extracting video ID from: {youtube_url}")
    
    if not youtube_url:
        log_error("Empty URL provided")
        return None
    
    # Multiple regex patterns for different URL formats
    patterns = [
        # Standard watch URL: youtube.com/watch?v=VIDEO_ID
        r'(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})',
        
        # Short URL: youtu.be/VIDEO_ID
        r'(?:youtu\.be\/)([a-zA-Z0-9_-]{11})',
        
        # Embed URL: youtube.com/embed/VIDEO_ID
        r'(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        
        # Shorts URL: youtube.com/shorts/VIDEO_ID
        r'(?:youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})',
        
        # Live URL: youtube.com/live/VIDEO_ID
        r'(?:youtube\.com\/live\/)([a-zA-Z0-9_-]{11})',
        
        # With additional params: youtube.com/watch?v=VIDEO_ID&list=...
        r'(?:youtube\.com\/watch\?.*v=)([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            video_id = match.group(1)
            log_success(f"Video ID extracted: {video_id}")
            return video_id
    
    log_error(f"Could not extract video ID from URL: {youtube_url}")
    return None


# ============================================================================
# TRANSCRIPT FETCHING - YouTube Transcript API v1.2.x compatible
# ============================================================================

def get_transcript(video_id, language_codes=['en', 'hi', 'en-US', 'en-GB']):
    """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║  YOUTUBE VIDEO KA TRANSCRIPT FETCH KARTA HAI                              ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    
    PARAMETERS:
    - video_id: YouTube video ID (11 characters)
    - language_codes: Preferred languages (English aur Hindi by default)
    
    RETURNS:
    - Dictionary with:
        - success: True/False
        - transcript: Full text (agar success)
        - segments: List of transcript segments with timestamps
        - error: Error message (agar fail)
    
    NOTE: Updated for youtube-transcript-api v1.2.x (instance-based API)
    """
    log_yt(f"Fetching transcript for video: {video_id}")
    
    if not video_id:
        return {
            'success': False,
            'error': 'Video ID is required',
            'transcript': None,
            'segments': []
        }
    
    try:
        # Create API instance (v1.2.x uses instance-based approach)
        ytt_api = YouTubeTranscriptApi()
        
        log_yt(f"Trying languages: {language_codes}")
        
        # Try to fetch transcript with preferred languages
        transcript_data = None
        used_language = None
        
        # First, try to list available transcripts
        try:
            available_transcripts = ytt_api.list(video_id)
            log_yt(f"Available transcripts found")
            
            # Try each preferred language
            for lang in language_codes:
                try:
                    # Find matching transcript
                    for t in available_transcripts:
                        if t.language_code == lang or t.language_code.startswith(lang.split('-')[0]):
                            transcript_data = t.fetch()
                            used_language = t.language_code
                            log_success(f"Found transcript in: {used_language}")
                            break
                    if transcript_data:
                        break
                except Exception:
                    continue
            
            # If no preferred language found, use first available
            if not transcript_data and available_transcripts:
                try:
                    first_transcript = list(available_transcripts)[0]
                    transcript_data = first_transcript.fetch()
                    used_language = first_transcript.language_code
                    log_success(f"Using first available transcript: {used_language}")
                except Exception as e:
                    log_error(f"Could not fetch first transcript: {e}")
                    
        except Exception as e:
            log_yt(f"List failed, trying direct fetch: {e}")
            # Fallback: try direct fetch
            try:
                transcript_data = ytt_api.fetch(video_id)
                used_language = "auto-detected"
                log_success("Direct fetch successful")
            except Exception as fetch_error:
                log_error(f"Direct fetch also failed: {fetch_error}")
        
        if not transcript_data:
            log_error("No transcript available for this video")
            return {
                'success': False,
                'error': 'Transcript not available for this video.',
                'fallback': 'Paste transcript manually',
                'transcript': None,
                'segments': []
            }
        
        # Convert transcript data to segments list
        segments = []
        for item in transcript_data:
            segments.append({
                'text': item.text if hasattr(item, 'text') else str(item.get('text', '')),
                'start': item.start if hasattr(item, 'start') else item.get('start', 0),
                'duration': item.duration if hasattr(item, 'duration') else item.get('duration', 0)
            })
        
        # Combine all text into full transcript
        full_text = ' '.join([seg['text'] for seg in segments])
        
        log_success(f"Transcript fetched: {len(segments)} segments, {len(full_text)} characters")
        
        return {
            'success': True,
            'transcript': full_text,
            'segments': segments,
            'language': used_language,
            'segment_count': len(segments),
            'character_count': len(full_text)
        }
        
    except Exception as e:
        error_msg = str(e)
        log_error(f"Transcript error: {error_msg}")
        
        # Handle specific error cases
        if 'disabled' in error_msg.lower():
            return {
                'success': False,
                'error': 'Transcripts are disabled for this video.',
                'fallback': 'Paste transcript manually',
                'transcript': None,
                'segments': []
            }
        elif 'unavailable' in error_msg.lower() or 'private' in error_msg.lower():
            return {
                'success': False,
                'error': 'Video is unavailable or private.',
                'transcript': None,
                'segments': []
            }
        else:
            return {
                'success': False,
                'error': f'Failed to fetch transcript: {error_msg}',
                'fallback': 'Paste transcript manually',
                'transcript': None,
                'segments': []
            }


# ============================================================================
# COMBINED FUNCTION - URL se seedha transcript
# ============================================================================

def get_youtube_transcript(youtube_url, language_codes=['en', 'hi', 'en-US', 'en-GB']):
    """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║  COMBINED FUNCTION: URL → VIDEO ID → TRANSCRIPT                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    
    Ek hi function mein pura kaam:
    1. URL se video ID extract
    2. Transcript fetch
    3. Return combined result
    """
    # Step 1: Extract video ID
    video_id = extract_video_id(youtube_url)
    
    if not video_id:
        return {
            'success': False,
            'error': 'Invalid YouTube URL. Please check the URL and try again.',
            'video_id': None,
            'transcript': None,
            'segments': []
        }
    
    # Step 2: Get transcript
    result = get_transcript(video_id, language_codes)
    
    # Add video_id to result
    result['video_id'] = video_id
    result['youtube_url'] = youtube_url
    
    return result

import os
import json
import urllib.request
from typing import Optional, Dict, Any
from src.detector import PromoCandidate

PROMPT_TEMPLATE = """You are an expert short-form video marketing producer for AI microdramas on TikTok, Instagram Reels, and YouTube Shorts.
Review the following screenplay clip candidate:

Episode: {episode}
Duration: {duration} seconds
Dialogue and Action:
{script_text}

Provide a JSON object with:
{{
  "hook_summary": "1 concise sentence explaining the 3-second hook that halts scrolling",
  "cliffhanger_summary": "1 concise sentence explaining the unresolved cut-off moment",
  "why_it_works": "1 sharp line explaining why a cold viewer with zero context will click",
  "hook_score": <score 1-10>,
  "cliffhanger_score": <score 1-10>,
  "suggested_title": "A punchy clickbait ad title (e.g. 'He abandoned his bride for her sister...')"
}}
Output ONLY valid JSON.
"""

def refine_with_llm(candidate: PromoCandidate, provider: Optional[str] = None) -> bool:
    """
    Attempts to enrich the candidate using an external LLM API if configured.
    Supports: 'gemini', 'openai', 'claude', or automatic detection from environment variables.
    Falls back gracefully to deterministic semantic templates if no API key is set.
    """
    provider = provider or os.environ.get("LLM_PROVIDER", "auto").lower()
    
    script_snippet = "\n".join([
        f"[{b.start_formatted} - {b.end_formatted}] {b.speaker or b.block_type}: {b.content}"
        for b in candidate.blocks
    ])
    
    # 1. Try Gemini
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if (provider in ("auto", "gemini")) and gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            prompt = PROMPT_TEMPLATE.format(
                episode=candidate.episode_number,
                duration=candidate.duration,
                script_text=script_snippet
            )
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            data = json.loads(response.text.strip('`json \n'))
            _apply_llm_data(candidate, data)
            return True
        except Exception:
            pass
            
    # 2. Try OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY")
    if (provider in ("auto", "openai")) and openai_key:
        try:
            prompt = PROMPT_TEMPLATE.format(
                episode=candidate.episode_number,
                duration=candidate.duration,
                script_text=script_snippet
            )
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            }
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode('utf-8'),
                headers=headers
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                res_data = json.loads(res.read().decode('utf-8'))
                raw_json = res_data["choices"][0]["message"]["content"]
                data = json.loads(raw_json)
                _apply_llm_data(candidate, data)
                return True
        except Exception:
            pass

    # 3. Default fast local semantic enrichment
    _local_enrichment(candidate)
    return False

def _apply_llm_data(candidate: PromoCandidate, data: Dict[str, Any]):
    """Applies structured LLM evaluation to the candidate."""
    candidate.hook_description = data.get("hook_summary", candidate.hook_description)
    candidate.cliffhanger_description = data.get("cliffhanger_summary", candidate.cliffhanger_description)
    candidate.why_it_works = data.get("why_it_works", candidate.why_it_works)
    if "hook_score" in data:
        candidate.hook_score = float(data["hook_score"])
    if "cliffhanger_score" in data:
        candidate.cliffhanger_score = float(data["cliffhanger_score"])

def _local_enrichment(candidate: PromoCandidate):
    """Fallback local enrichment when no external API key is provided."""
    h_b = candidate.hook_block
    c_b = candidate.cliffhanger_block
    
    if h_b.block_type == 'DIALOGUE':
        cand_hook = f"Opens with {h_b.speaker} declaring: '{h_b.content}'"
    else:
        cand_hook = f"Opens with immediate high-impact visual: {h_b.content}"
        
    if c_b.block_type == 'DIALOGUE':
        cand_cliff = f"Cuts off right after {c_b.speaker}'s unanswered confrontation: '{c_b.content}'"
    else:
        cand_cliff = f"Abruptly cuts on high-tension visual action: {c_b.content}"
        
    candidate.hook_description = cand_hook
    candidate.cliffhanger_description = cand_cliff

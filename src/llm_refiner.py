import os
import json
from typing import Optional
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

def refine_with_llm(candidate: PromoCandidate) -> bool:
    """Attempts to enrich the candidate using an external LLM API if configured."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    script_snippet = "\n".join([
        f"[{b.start_formatted} - {b.end_formatted}] {b.speaker or b.block_type}: {b.content}"
        for b in candidate.blocks
    ])
    
    if gemini_key:
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
            candidate.hook_description = data.get("hook_summary", candidate.hook_description)
            candidate.cliffhanger_description = data.get("cliffhanger_summary", candidate.cliffhanger_description)
            candidate.why_it_works = data.get("why_it_works", candidate.why_it_works)
            return True
        except Exception as e:
            # Fall back gracefully if API fails or quota exceeded
            pass
            
    # Default smart heuristic enrichment if no API key is set
    _local_enrichment(candidate)
    return False

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

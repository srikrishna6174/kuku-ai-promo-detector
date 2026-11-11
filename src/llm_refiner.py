import os
import re
import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from src.parser import Episode, ScriptBlock, format_time
from src.detector import PromoCandidate, find_promos_for_episode


PROVIDER_DEFAULTS: Dict[str, Dict[str, str]] = {
    "gemini": {
        "display_name": "Google Gemini",
        "env_key": "GEMINI_API_KEY",
        "default_model": "gemini-3.8-flash",
    },
    "openai": {
        "display_name": "OpenAI",
        "env_key": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
    },
    "anthropic": {
        "display_name": "Anthropic Claude",
        "env_key": "ANTHROPIC_API_KEY",
        "default_model": "claude-3-5-haiku-latest",
    },
    "groq": {
        "display_name": "Groq",
        "env_key": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
    },
    "openrouter": {
        "display_name": "OpenRouter",
        "env_key": "OPENROUTER_API_KEY",
        "default_model": "google/gemini-2.0-flash-001",
    },
    "custom": {
        "display_name": "Custom OpenAI-Compatible",
        "env_key": "CUSTOM_LLM_API_KEY",
        "default_model": "llama3.1",
    },
}


@dataclass
class LLMProviderConfig:
    name: str  # 'gemini', 'openai', 'anthropic', 'groq', 'openrouter', 'custom'
    api_key: str = ""
    model: str = ""
    base_url: str = ""
    enabled: bool = True
    display_name: str = ""

    def __post_init__(self):
        meta = PROVIDER_DEFAULTS.get(self.name, {})
        if not self.display_name:
            self.display_name = meta.get("display_name", self.name.title())
        if not self.model:
            self.model = meta.get("default_model", "")
        if not self.api_key:
            env_var = meta.get("env_key", "")
            if env_var:
                self.api_key = os.environ.get(env_var, "")


def load_backend_env(env_path: str = ".env"):
    """Loads environment variables from a local .env file if present (without overriding OS env)."""
    if not os.path.isfile(env_path):
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path, override=False)
        return
    except ImportError:
        pass
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


def _get_secret_or_env(key: str) -> str:
    """Reads a config value from OS/.env first, then Streamlit st.secrets if configured."""
    val = os.environ.get(key, "").strip()
    if val:
        return val
    try:
        import streamlit as st
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return ""


def get_configured_env_providers() -> List[LLMProviderConfig]:
    """Builds enabled provider configs (Gemini and OpenAI) from server-side .env, OS env, or st.secrets."""
    load_backend_env()
    providers: List[LLMProviderConfig] = []

    for name in ("gemini", "openai"):
        env_key = PROVIDER_DEFAULTS[name]["env_key"]
        key_val = _get_secret_or_env(env_key)
        if key_val:
            model_override = _get_secret_or_env(f"{name.upper()}_MODEL") or PROVIDER_DEFAULTS[name]["default_model"]
            providers.append(LLMProviderConfig(name=name, api_key=key_val, model=model_override))

    return providers


def get_backend_provider_status() -> List[Dict[str, Any]]:
    """Returns server-side configuration availability for Gemini and OpenAI."""
    configured = {p.name: p for p in get_configured_env_providers()}
    statuses: List[Dict[str, Any]] = []
    for name in ("gemini", "openai"):
        meta = PROVIDER_DEFAULTS[name]
        cfg = configured.get(name)
        statuses.append(
            {
                "name": name,
                "display_name": meta["display_name"],
                "env_key": meta["env_key"],
                "configured": cfg is not None,
                "model": cfg.model if cfg else meta["default_model"],
                "config": cfg,
            }
        )
    return statuses


def _extract_json_payload(raw_text: str) -> Dict[str, Any]:
    """Extracts and parses a JSON object from raw LLM text output."""
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text).strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
        return {"items": parsed}
    except json.JSONDecodeError:
        pass

    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx > start_idx:
        snippet = text[start_idx : end_idx + 1]
        parsed = json.loads(snippet)
        if isinstance(parsed, dict):
            return parsed

    raise ValueError(f"LLM response did not contain valid JSON: {text[:180]}")


def _http_post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8", errors="ignore")[:240]
        except Exception:
            pass
        raise RuntimeError(f"HTTP {e.code}: {err_body or e.reason}") from e
    except Exception as e:
        raise RuntimeError(f"Request error: {e}") from e


def call_provider_json(cfg: LLMProviderConfig, prompt: str, timeout: int = 30) -> Dict[str, Any]:
    """Calls a single LLM provider and returns parsed JSON or raises a clear error."""
    if not cfg.api_key and cfg.name != "custom":
        raise RuntimeError(f"{cfg.display_name} API key is missing.")

    if cfg.name == "gemini":
        # Prefer installed google.genai SDK, fall back to REST API
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=cfg.api_key)
            response = client.models.generate_content(
                model=cfg.model or "gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.25,
                ),
            )
            return _extract_json_payload(response.text or "")
        except ImportError:
            model = cfg.model or "gemini-3.8-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={cfg.api_key}"
            res_data = _http_post_json(
                url,
                {"Content-Type": "application/json"},
                {"contents": [{"parts": [{"text": prompt}]}]},
                timeout=timeout,
            )
            candidates = res_data.get("candidates", [])
            if not candidates:
                raise RuntimeError("Gemini returned no candidates.")
            parts = candidates[0].get("content", {}).get("parts", [])
            raw_txt = "".join(p.get("text", "") for p in parts)
            return _extract_json_payload(raw_txt)

    elif cfg.name == "anthropic":
        url = (cfg.base_url or "https://api.anthropic.com/v1/messages").rstrip("/")
        headers = {
            "x-api-key": cfg.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": cfg.model or "claude-3-5-haiku-latest",
            "max_tokens": 1800,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        }
        res_data = _http_post_json(url, headers, payload, timeout=timeout)
        content_blocks = res_data.get("content", [])
        raw_txt = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        return _extract_json_payload(raw_txt)

    else:
        # OpenAI, Groq, OpenRouter, or custom OpenAI-compatible server
        endpoint_map = {
            "openai": "https://api.openai.com/v1/chat/completions",
            "groq": "https://api.groq.com/openai/v1/chat/completions",
            "openrouter": "https://openrouter.ai/api/v1/chat/completions",
        }
        if cfg.name == "custom":
            if not cfg.base_url:
                raise RuntimeError("Custom OpenAI-compatible provider requires a Base URL.")
            base = cfg.base_url.rstrip("/")
            url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
        else:
            url = (cfg.base_url or endpoint_map[cfg.name]).rstrip("/")

        headers = {"Content-Type": "application/json"}
        if cfg.api_key:
            headers["Authorization"] = f"Bearer {cfg.api_key}"

        payload: Dict[str, Any] = {
            "model": cfg.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.25,
        }
        if cfg.name in ("openai", "groq"):
            payload["response_format"] = {"type": "json_object"}

        res_data = _http_post_json(url, headers, payload, timeout=timeout)
        choices = res_data.get("choices", [])
        if not choices:
            raise RuntimeError(f"{cfg.display_name} returned empty choices.")
        raw_txt = choices[0].get("message", {}).get("content", "")
        return _extract_json_payload(raw_txt)


def call_with_failover(
    providers: List[LLMProviderConfig],
    prompt: str,
    timeout: int = 30,
) -> Tuple[Optional[Dict[str, Any]], Optional[LLMProviderConfig], List[Dict[str, str]]]:
    """
    Attempts providers in order. If one fails (rate-limit, outage, bad JSON),
    seamlessly fails over to the next configured provider.
    """
    attempts: List[Dict[str, str]] = []
    for cfg in providers:
        if not cfg.enabled:
            continue
        try:
            data = call_provider_json(cfg, prompt, timeout=timeout)
            attempts.append({"provider": cfg.display_name, "model": cfg.model, "status": "ok", "error": ""})
            return data, cfg, attempts
        except Exception as exc:
            attempts.append({"provider": cfg.display_name, "model": cfg.model, "status": "failed", "error": str(exc)})
    return None, None, attempts


# ---------------- Legacy Single-Candidate Refiner (CLI compatible) ----------------

PROMPT_TEMPLATE = """You are an expert short-form video marketing producer for microdramas & vertical video on TikTok, Instagram Reels, and YouTube Shorts.
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
  "suggested_title": "A punchy clickbait ad title"
}}
Output ONLY valid JSON.
"""


def refine_with_llm(candidate: PromoCandidate, provider: Optional[str] = None) -> bool:
    """
    Attempts to enrich a single candidate using configured env providers with automatic failover.
    Falls back gracefully to deterministic templates if no API key is available.
    """
    requested = (provider or os.environ.get("LLM_PROVIDER", "auto")).lower()
    if requested == "offline":
        _local_enrichment(candidate)
        return False

    env_providers = get_configured_env_providers()
    if requested != "auto":
        req_name = "anthropic" if requested == "claude" else requested
        ordered = [p for p in env_providers if p.name == req_name] + [p for p in env_providers if p.name != req_name]
    else:
        ordered = env_providers

    if not ordered:
        _local_enrichment(candidate)
        return False

    script_snippet = "\n".join(
        f"[{b.start_formatted} - {b.end_formatted}] {b.speaker or b.block_type}: {b.content}"
        for b in candidate.blocks
    )
    prompt = PROMPT_TEMPLATE.format(
        episode=candidate.episode_number,
        duration=candidate.duration,
        script_text=script_snippet,
    )

    data, used_cfg, _ = call_with_failover(ordered, prompt, timeout=15)
    if data and used_cfg:
        _apply_llm_data(candidate, data)
        candidate.model_scores[used_cfg.display_name] = {
            "hook_score": candidate.hook_score,
            "cliffhanger_score": candidate.cliffhanger_score,
        }
        return True

    _local_enrichment(candidate)
    return False


def _apply_llm_data(candidate: PromoCandidate, data: Dict[str, Any]):
    """Applies structured LLM evaluation to the candidate."""
    candidate.hook_description = data.get("hook_summary", candidate.hook_description)
    candidate.cliffhanger_description = data.get("cliffhanger_summary", candidate.cliffhanger_description)
    candidate.why_it_works = data.get("why_it_works", candidate.why_it_works)
    if "hook_score" in data:
        candidate.hook_score = min(10.0, max(1.0, float(data["hook_score"])))
    if "cliffhanger_score" in data:
        candidate.cliffhanger_score = min(10.0, max(1.0, float(data["cliffhanger_score"])))
    if "coherence_score" in data:
        candidate.coherence_score = min(10.0, max(1.0, float(data["coherence_score"])))
    candidate.recalculate_total_score()


def _local_enrichment(candidate: PromoCandidate):
    """Fallback local enrichment when no external API key is provided."""
    h_b = candidate.hook_block
    c_b = candidate.cliffhanger_block

    if h_b.block_type == "DIALOGUE":
        cand_hook = f"Opens with {h_b.speaker} declaring: '{h_b.content}'"
    else:
        cand_hook = f"Opens with immediate high-impact visual: {h_b.content}"

    if c_b.block_type == "DIALOGUE":
        cand_cliff = f"Cuts off right after {c_b.speaker}'s unanswered confrontation: '{c_b.content}'"
    else:
        cand_cliff = f"Abruptly cuts on high-tension visual action: {c_b.content}"

    candidate.hook_description = cand_hook
    candidate.cliffhanger_description = cand_cliff


# ---------------- Full Multi-LLM Promo Selection & LLM-as-a-Judge ----------------

LLM_DETECTION_PROMPT = """You are an expert short-form video producer selecting high-converting {min_dur}s-{max_dur}s social promo clips from ANY genre (thriller, romance, drama, sci-fi, comedy, mystery).

Rules:
1. Pick up to {top_k} distinct, continuous promo segments from the numbered script blocks below.
2. Each segment MUST start at block `start_idx` and end at block `end_idx` (inclusive), with total duration strictly between {min_dur} and {max_dur} seconds.
3. Optimize for:
   - 0-3s Hook: immediate conflict, shock, mystery, twist, or emotional stakes.
   - Cliffhanger Ending: cuts cleanly on an unanswered question, revelation, threat, or dramatic beat.
   - Standalone Clarity: a viewer with zero prior context understands the stakes.

Episode {episode_num} | Logline: {logline}
Numbered Script Blocks:
{indexed_blocks}

Return ONLY valid JSON:
{{
  "candidates": [
    {{
      "start_idx": <int>,
      "end_idx": <int>,
      "hook_score": <float 1-10>,
      "cliffhanger_score": <float 1-10>,
      "coherence_score": <float 1-10>,
      "hook_summary": "1 concise sentence explaining the 0-3s scroll-stopping hook",
      "cliffhanger_summary": "1 concise sentence explaining the unresolved cut-off",
      "why_it_works": "1 sharp sentence explaining why cold viewers will click"
    }}
  ]
}}
"""

LLM_JUDGE_PROMPT = """You are an impartial **LLM-as-a-Judge** evaluating candidate {min_dur}s-{max_dur}s promo clips proposed by different detection pipelines/models for Episode {episode_num}.

Evaluate EVERY candidate strictly on short-form conversion quality across ANY genre:
- hook_strength (0-10): Does the opening 3 seconds stop a cold scroller?
- cliffhanger_pull (0-10): Does the cut-off create irresistible curiosity without resolving the tension?
- standalone_clarity (0-10): Can a stranger follow who wants what and why it matters?
- pacing_quality (0-10): Clean opening and clean cliffhanger cut (not cut mid-setup)?

Candidates to judge:
{candidates_text}

Return ONLY valid JSON evaluating ALL candidate IDs:
{{
  "judgments": [
    {{
      "candidate_id": <int>,
      "hook_strength": <float 0-10>,
      "cliffhanger_pull": <float 0-10>,
      "standalone_clarity": <float 0-10>,
      "pacing_quality": <float 0-10>,
      "judge_score": <float 0-100>,
      "judge_verdict": "1-2 concise sentences explaining strengths, weaknesses, and why this ranks where it does"
    }}
  ]
}}
"""


def _format_indexed_blocks(blocks: List[ScriptBlock], offset: int = 0) -> str:
    lines = []
    for idx, b in enumerate(blocks):
        g_idx = offset + idx
        if b.block_type == "DIALOGUE":
            tone = f" ({b.tone})" if b.tone else ""
            lines.append(f"[{g_idx}] ({b.start_formatted} - {b.end_formatted}) {b.speaker}{tone}: \"{b.content}\"")
        else:
            lines.append(f"[{g_idx}] ({b.start_formatted} - {b.end_formatted}) [{b.block_type}]: {b.content}")
    return "\n".join(lines)


def _snap_indices_to_duration(
    blocks: List[ScriptBlock],
    s_idx: int,
    e_idx: int,
    min_dur: float,
    max_dur: float,
) -> Optional[Tuple[int, int]]:
    """Validates and gently adjusts LLM-chosen block boundaries to meet duration constraints."""
    n = len(blocks)
    if n < 2:
        return None
    s_idx = max(0, min(n - 2, int(s_idx)))
    e_idx = max(s_idx + 1, min(n - 1, int(e_idx)))

    def dur(a: int, b: int) -> float:
        return blocks[b].end_time - blocks[a].start_time

    # Expand end if slightly short
    steps = 0
    while dur(s_idx, e_idx) < min_dur and e_idx < n - 1 and steps < 8:
        e_idx += 1
        steps += 1

    # Shrink end if slightly long
    steps = 0
    while dur(s_idx, e_idx) > max_dur and e_idx > s_idx + 1 and steps < 10:
        e_idx -= 1
        steps += 1

    final_d = dur(s_idx, e_idx)
    if final_d < min_dur or final_d > max_dur:
        return None
    return s_idx, e_idx


def _parse_llm_candidates_for_chunk(
    episode: Episode,
    blocks: List[ScriptBlock],
    data: Dict[str, Any],
    provider_label: str,
    effective_min: float,
    max_duration: float,
) -> List[PromoCandidate]:
    results: List[PromoCandidate] = []
    raw_cands = data.get("candidates", [])
    if not isinstance(raw_cands, list):
        return results

    for item in raw_cands:
        if not isinstance(item, dict) or "start_idx" not in item or "end_idx" not in item:
            continue
        snapped = _snap_indices_to_duration(
            blocks,
            item["start_idx"],
            item["end_idx"],
            effective_min,
            max_duration,
        )
        if not snapped:
            continue
        s_idx, e_idx = snapped
        window_blocks = blocks[s_idx : e_idx + 1]
        start_b = window_blocks[0]
        end_b = window_blocks[-1]

        h_score = min(10.0, max(1.0, float(item.get("hook_score", 7.5))))
        c_score = min(10.0, max(1.0, float(item.get("cliffhanger_score", 7.5))))
        coh_score = min(10.0, max(1.0, float(item.get("coherence_score", 7.5))))

        cand = PromoCandidate(
            episode_number=episode.ep_number,
            start_time=start_b.start_time,
            end_time=end_b.end_time,
            hook_block=start_b,
            cliffhanger_block=end_b,
            blocks_in_range=window_blocks,
            hook_score=h_score,
            cliffhanger_score=c_score,
            coherence_score=coh_score,
            detection_method=f"LLM ({provider_label})",
            proposed_by=[provider_label],
            model_scores={
                provider_label: {
                    "hook_score": h_score,
                    "cliffhanger_score": c_score,
                    "coherence_score": coh_score,
                    "total_score": round((h_score * 0.40 + c_score * 0.35 + coh_score * 0.25) * 10, 1),
                }
            },
        )
        cand.hook_description = str(item.get("hook_summary") or "").strip() or f"{start_b.speaker or start_b.block_type}: \"{start_b.content}\""
        cand.cliffhanger_description = str(item.get("cliffhanger_summary") or "").strip() or f"Cuts on: \"{end_b.content}\""
        cand.why_it_works = str(item.get("why_it_works") or "").strip() or "Selected by LLM semantic dramatic analysis."
        results.append(cand)

    return results


def _merge_candidate_pool(candidates: List[PromoCandidate]) -> List[PromoCandidate]:
    """Consolidates overlapping candidates from multiple LLMs/manual cuts while keeping provenance."""
    merged: List[PromoCandidate] = []
    for cand in candidates:
        matched = None
        for existing in merged:
            if existing.episode_number != cand.episode_number:
                continue
            inter = max(0.0, min(existing.end_time, cand.end_time) - max(existing.start_time, cand.start_time))
            union = max(existing.end_time, cand.end_time) - min(existing.start_time, cand.start_time)
            iou = inter / union if union > 0 else 0.0
            if iou >= 0.72:
                matched = existing
                break

        if matched is None:
            merged.append(cand)
        else:
            for src in cand.proposed_by:
                if src not in matched.proposed_by:
                    matched.proposed_by.append(src)
            matched.model_scores.update(cand.model_scores)
            # Prefer LLM descriptions over generic rule descriptions when merging
            if "Manual" in matched.detection_method and "LLM" in cand.detection_method:
                matched.hook_description = cand.hook_description
                matched.cliffhanger_description = cand.cliffhanger_description
                matched.why_it_works = cand.why_it_works
                matched.detection_method = "Both (Rule + LLM)"
            elif len(matched.proposed_by) > 1 and "Manual" not in " ".join(matched.proposed_by):
                matched.detection_method = f"Multi-LLM ({len(matched.proposed_by)} models)"
            # Average multi-source scores cleanly
            matched.hook_score = round((matched.hook_score + cand.hook_score) / 2.0, 1)
            matched.cliffhanger_score = round((matched.cliffhanger_score + cand.cliffhanger_score) / 2.0, 1)
            matched.coherence_score = round((matched.coherence_score + cand.coherence_score) / 2.0, 1)
            matched.recalculate_total_score()

    return merged


def _run_llm_judge(
    episode: Episode,
    pool: List[PromoCandidate],
    judge_order: List[LLMProviderConfig],
    min_dur: float,
    max_dur: float,
) -> Tuple[List[PromoCandidate], Optional[LLMProviderConfig], List[Dict[str, str]]]:
    """Runs LLM-as-a-Judge across the consolidated candidate pool with failover."""
    if not pool or not judge_order:
        return pool, None, []

    cand_sections = []
    for idx, c in enumerate(pool):
        excerpt = "\n".join(
            f"  [{b.start_formatted}-{b.end_formatted}] {b.speaker or b.block_type}: {b.content}"
            for b in c.blocks[:18]
        )
        cand_sections.append(
            f"Candidate #{idx} | Proposed by: {', '.join(c.proposed_by)} | "
            f"Time: {format_time(c.start_time)}-{format_time(c.end_time)} ({c.duration}s) | "
            f"Current Score: {c.total_score}/100\n"
            f"  Hook Note: {c.hook_description}\n"
            f"  Cliffhanger Note: {c.cliffhanger_description}\n"
            f"  Script:\n{excerpt}"
        )

    prompt = LLM_JUDGE_PROMPT.format(
        min_dur=int(min_dur),
        max_dur=int(max_dur),
        episode_num=episode.ep_number,
        candidates_text="\n\n".join(cand_sections),
    )

    data, judge_cfg, attempts = call_with_failover(judge_order, prompt, timeout=30)
    if not data or not judge_cfg:
        return pool, None, attempts

    judgments = data.get("judgments", [])
    if isinstance(judgments, list):
        by_id = {int(j["candidate_id"]): j for j in judgments if isinstance(j, dict) and "candidate_id" in j}
        for idx, c in enumerate(pool):
            j = by_id.get(idx)
            if not j:
                continue
            hs = min(10.0, max(0.0, float(j.get("hook_strength", c.hook_score))))
            cp = min(10.0, max(0.0, float(j.get("cliffhanger_pull", c.cliffhanger_score))))
            sc = min(10.0, max(0.0, float(j.get("standalone_clarity", c.coherence_score))))
            pq = min(10.0, max(0.0, float(j.get("pacing_quality", 7.5))))
            j_score = float(j.get("judge_score", round((hs * 0.35 + cp * 0.35 + sc * 0.20 + pq * 0.10) * 10, 1)))
            j_score = min(100.0, max(0.0, round(j_score, 1)))

            c.hook_score = round(hs, 1)
            c.cliffhanger_score = round(cp, 1)
            c.coherence_score = round(sc, 1)
            c.total_score = j_score
            c.judge_verdict = {
                "judge_provider": judge_cfg.display_name,
                "judge_model": judge_cfg.model,
                "judge_score": j_score,
                "hook_strength": round(hs, 1),
                "cliffhanger_pull": round(cp, 1),
                "standalone_clarity": round(sc, 1),
                "pacing_quality": round(pq, 1),
                "verdict": str(j.get("judge_verdict", "")).strip(),
            }
            if "Judged" not in c.detection_method:
                c.detection_method = f"{c.detection_method} · Judged"

    return pool, judge_cfg, attempts


def detect_promos_with_llms(
    episode: Episode,
    providers: List[LLMProviderConfig],
    min_duration: float = 20.0,
    max_duration: float = 60.0,
    top_k: int = 2,
    manual_candidates: Optional[List[PromoCandidate]] = None,
    use_judge: bool = False,
    judge_provider_name: str = "auto",
    detection_mode: str = "llm",
    run_all_active_llms: bool = True,
) -> Tuple[List[PromoCandidate], Dict[str, Any]]:
    """
    Runs LLM promo detection with automatic failover across multiple LLMs,
    optional hybrid merging with manual cliffhanger cuts, and optional LLM-as-a-Judge.
    """
    active_providers = [p for p in providers if p.enabled]
    telemetry: Dict[str, Any] = {
        "episode": episode.ep_number,
        "providers_configured": [p.display_name for p in active_providers],
        "providers_succeeded": [],
        "provider_failures": [],
        "failover_triggered": False,
        "judge_used": False,
        "judge_provider": None,
        "judge_failures": [],
        "all_llms_failed": False,
    }

    effective_min = min_duration
    if episode.total_duration > 0 and episode.total_duration < min_duration:
        effective_min = max(5.0, round(episode.total_duration * 0.65, 1))

    # Build chunked block views if episode has > 120 blocks
    blocks = episode.blocks
    chunks: List[Tuple[int, List[ScriptBlock]]] = []
    if len(blocks) <= 120:
        chunks.append((0, blocks))
    else:
        step = 95
        for start in range(0, len(blocks), step):
            chunk = blocks[start : start + 120]
            if len(chunk) >= 4:
                chunks.append((start, chunk))

    llm_candidates: List[PromoCandidate] = []
    succeeded_providers: List[LLMProviderConfig] = []

    if active_providers and blocks:
        if run_all_active_llms and len(active_providers) >= 2:
            # Query all active LLMs independently (ensemble); any outage is logged while survivors proceed
            for cfg in active_providers:
                provider_cands: List[PromoCandidate] = []
                provider_ok = False
                last_err = ""
                for offset, chunk in chunks:
                    prompt = LLM_DETECTION_PROMPT.format(
                        min_dur=int(effective_min),
                        max_dur=int(max_duration),
                        top_k=max(top_k, 2),
                        episode_num=episode.ep_number,
                        logline=episode.logline or "N/A",
                        indexed_blocks=_format_indexed_blocks(chunk, offset=0),
                    )
                    try:
                        data = call_provider_json(cfg, prompt, timeout=30)
                        provider_ok = True
                        parsed = _parse_llm_candidates_for_chunk(
                            episode, chunk, data, cfg.display_name, effective_min, max_duration
                        )
                        provider_cands.extend(parsed)
                    except Exception as exc:
                        last_err = str(exc)

                if provider_ok:
                    succeeded_providers.append(cfg)
                    telemetry["providers_succeeded"].append(cfg.display_name)
                    llm_candidates.extend(provider_cands)
                else:
                    telemetry["provider_failures"].append({"provider": cfg.display_name, "error": last_err})
                    telemetry["failover_triggered"] = True
        else:
            # Sequential failover chain: first working provider handles the episode
            for offset, chunk in chunks:
                prompt = LLM_DETECTION_PROMPT.format(
                    min_dur=int(effective_min),
                    max_dur=int(max_duration),
                    top_k=max(top_k, 2),
                    episode_num=episode.ep_number,
                    logline=episode.logline or "N/A",
                    indexed_blocks=_format_indexed_blocks(chunk, offset=0),
                )
                data, winner_cfg, attempts = call_with_failover(active_providers, prompt, timeout=30)
                for att in attempts:
                    if att["status"] == "failed":
                        telemetry["provider_failures"].append({"provider": att["provider"], "error": att["error"]})
                        telemetry["failover_triggered"] = True
                if data and winner_cfg:
                    if winner_cfg.display_name not in telemetry["providers_succeeded"]:
                        telemetry["providers_succeeded"].append(winner_cfg.display_name)
                        succeeded_providers.append(winner_cfg)
                    llm_candidates.extend(
                        _parse_llm_candidates_for_chunk(
                            episode, chunk, data, winner_cfg.display_name, effective_min, max_duration
                        )
                    )

    if active_providers and not succeeded_providers:
        telemetry["all_llms_failed"] = True

    # Combine manual candidates + LLM candidates depending on mode
    combined_pool: List[PromoCandidate] = []
    if detection_mode == "both" and manual_candidates:
        for mc in manual_candidates:
            mc.detection_method = "Both (Rule + LLM)" if succeeded_providers else mc.detection_method
            combined_pool.append(mc)
    combined_pool.extend(llm_candidates)

    # If LLM-only mode failed completely or returned zero valid duration windows, fall back safely
    if not combined_pool and blocks:
        fallback_cands = find_promos_for_episode(
            episode, min_duration=min_duration, max_duration=max_duration, top_k=top_k
        )
        for fc in fallback_cands:
            fc.detection_method = "Fallback (Universal Rules)"
            fc.proposed_by = ["Universal Rules Fallback"]
        combined_pool.extend(fallback_cands)

    merged_pool = _merge_candidate_pool(combined_pool)

    # Optional LLM-as-a-Judge step (uses healthy providers with failover)
    judge_candidates_for_routing = succeeded_providers if succeeded_providers else active_providers
    if use_judge and judge_candidates_for_routing and len(merged_pool) >= 1:
        if judge_provider_name and judge_provider_name != "auto":
            ordered_judges = [p for p in judge_candidates_for_routing if p.name == judge_provider_name] + [
                p for p in judge_candidates_for_routing if p.name != judge_provider_name
            ]
        else:
            ordered_judges = judge_candidates_for_routing

        merged_pool, used_judge, j_attempts = _run_llm_judge(
            episode, merged_pool, ordered_judges, effective_min, max_duration
        )
        for ja in j_attempts:
            if ja["status"] == "failed":
                telemetry["judge_failures"].append({"provider": ja["provider"], "error": ja["error"]})
        if used_judge:
            telemetry["judge_used"] = True
            telemetry["judge_provider"] = f"{used_judge.display_name} ({used_judge.model})"

    # Final deduplication & top-K selection
    merged_pool.sort(
        key=lambda c: float(c.judge_verdict["judge_score"]) if c.judge_verdict else c.total_score,
        reverse=True,
    )
    selected: List[PromoCandidate] = []
    for c in merged_pool:
        overlap = False
        for s in selected:
            overlap_dur = max(0.0, min(c.end_time, s.end_time) - max(c.start_time, s.start_time))
            if overlap_dur > min(15.0, effective_min * 0.6):
                overlap = True
                break
        if not overlap:
            selected.append(c)
            if len(selected) >= top_k:
                break

    return selected, telemetry

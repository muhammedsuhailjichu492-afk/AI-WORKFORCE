
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"   # change to whatever you have pulled, e.g. "llama3"
TIMEOUT_SECONDS = 12


def _call_ollama(prompt: str, system: str = "") -> str | None:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "options": {"temperature": 0.4, "num_predict": 220},
            },
            timeout=TIMEOUT_SECONDS,
        )
        if resp.status_code == 200:
            text = resp.json().get("response", "").strip()
            return text or None
    except requests.exceptions.RequestException:
        return None
    return None


def explain_risk(task_title: str, risk_score: float, risk_level: str, factors: dict) -> str:
    """RAG-lite: the 'retrieved context' is the structured factor dict computed
    upstream by the ML/rule stages — grounding the LLM in real numbers instead
    of letting it hallucinate a rationale."""
    system = (
        "You are a concise project-risk analyst. Explain WHY a task is risky "
        "in 2-3 sentences, referencing the given factors. No fluff, no headers."
    )
    prompt = (
        f"Task: {task_title}\n"
        f"Risk score: {risk_score:.0f}/100 ({risk_level})\n"
        f"Contributing factors: {factors}\n\n"
        "Explain the risk in 2-3 plain sentences."
    )
    result = _call_ollama(prompt, system)
    if result:
        return result

    # Template fallback
    numeric_factors = {k: v for k, v in factors.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
    top_factor = max(numeric_factors, key=lambda k: abs(numeric_factors[k])) if numeric_factors else "multiple factors"
    return (
        f"'{task_title}' is flagged {risk_level} risk ({risk_score:.0f}/100), "
        f"driven mainly by {top_factor.replace('_', ' ')}. Review deadline, "
        f"workload, and blockers before this becomes a project delay."
    )


def draft_recommendation(rec_type: str, context: dict) -> str:
    system = (
        "You are a workforce planning assistant. Write ONE short, actionable "
        "recommendation sentence for a project manager to approve or reject. "
        "Be specific and concrete, no headers, no bullet points."
    )
    prompt = f"Recommendation type: {rec_type}\nContext: {context}\n\nWrite the recommendation."
    result = _call_ollama(prompt, system)
    if result:
        return result

    # Template fallback per type
    if rec_type == "reassignment":
        return (
            f"Reassign '{context.get('task_title')}' from {context.get('from_name')} "
            f"(overloaded) to {context.get('to_name')} (has capacity) to reduce delay risk."
        )
    if rec_type == "deadline_extension":
        return (
            f"Extend the deadline for '{context.get('task_title')}' by 3 days — "
            f"current pace makes the original date unrealistic."
        )
    if rec_type == "priority_change":
        return f"Raise priority on '{context.get('task_title')}' given its high delay risk."
    return f"Review '{context.get('task_title')}' — flagged for manager attention."

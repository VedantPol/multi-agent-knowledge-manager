from __future__ import annotations

from app.agents.guardrails import split_claims
from app.config import get_settings
from app.models import ClaimCheck, JudgeReport


def citation_ids_from_answer(answer: str, available_ids: set[str]) -> set[str]:
    return {citation_id for citation_id in available_ids if f"[{citation_id}]" in answer}


def check_claim_support(answer: str, context_by_id: dict[str, str]) -> list[ClaimCheck]:
    claims = split_claims(answer)
    cited_ids = citation_ids_from_answer(answer, set(context_by_id))
    checks: list[ClaimCheck] = []

    for claim in claims:
        claim_terms = {term.lower().strip(".,:;()[]") for term in claim.split() if len(term) > 4}
        supporting_ids = []
        for citation_id, context in context_by_id.items():
            context_lower = context.lower()
            overlap = sum(1 for term in claim_terms if term in context_lower)
            if overlap >= max(2, min(5, len(claim_terms) // 3)):
                supporting_ids.append(citation_id)
        supported = bool(supporting_ids) and (not cited_ids or bool(cited_ids.intersection(supporting_ids)))
        checks.append(
            ClaimCheck(
                claim=claim,
                supported=supported,
                citation_ids=supporting_ids[:3],
                note=None if supported else "Claim terms were not sufficiently grounded in retrieved citations.",
            )
        )
    return checks


async def judge_answer(question: str, answer: str, context_by_id: dict[str, str], claims: list[ClaimCheck]) -> JudgeReport:
    settings = get_settings()
    unsupported = [claim for claim in claims if not claim.supported]
    base_score = max(0.0, 1.0 - (len(unsupported) * 0.22))
    if not context_by_id:
        return JudgeReport(score=0.0, verdict="no_context", details={"reason": "No citations were retrieved."})

    if not settings.openai_api_key:
        verdict = "pass" if base_score >= 0.75 else "review"
        return JudgeReport(
            score=round(base_score, 2),
            verdict=verdict,
            details={"mode": "heuristic", "unsupported_claims": len(unsupported)},
        )

    try:
        from autogen_agentchat.agents import AssistantAgent
        from autogen_ext.models.openai import OpenAIChatCompletionClient

        model_client = OpenAIChatCompletionClient(model=settings.openai_judge_model, api_key=settings.openai_api_key)
        judge = AssistantAgent(
            "citation_judge",
            model_client=model_client,
            system_message=(
                "You are an LLM-as-Judge evaluator. Score whether the answer is fully supported by "
                "the cited context. Return concise JSON with score, verdict, and reason."
            ),
        )
        context = "\n\n".join(f"[{key}] {value}" for key, value in context_by_id.items())
        result = await judge.run(task=f"Question: {question}\nAnswer: {answer}\nContext:\n{context}")
        await model_client.close()
        content = getattr(result.messages[-1], "content", "")
        return JudgeReport(
            score=round(base_score, 2),
            verdict="autogen_review",
            details={"mode": "autogen", "judge_response": content, "unsupported_claims": len(unsupported)},
        )
    except Exception as exc:
        verdict = "pass" if base_score >= 0.75 else "review"
        return JudgeReport(
            score=round(base_score, 2),
            verdict=verdict,
            details={"mode": "heuristic_fallback", "error": str(exc), "unsupported_claims": len(unsupported)},
        )

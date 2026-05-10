from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.evaluation import check_claim_support, judge_answer
from app.agents.guardrails import check_prompt_injection, sanitize_context
from app.agents.llm import generate_answer
from app.models import Citation, SafetyReport
from app.storage import KnowledgeStore


class AgentState(TypedDict, total=False):
    question: str
    top_k: int
    safety: SafetyReport
    plan: list[str]
    hits: list[Citation]
    context_by_id: dict[str, str]
    answer: str
    claims: list
    hallucination_risk: str
    judge_report: object
    trace: list[str]


def build_workflow(store: KnowledgeStore):
    async def guardrail_agent(state: AgentState) -> dict:
        report = check_prompt_injection(state["question"])
        trace = ["Guardrail agent scanned the user question."]
        if report.blocked:
            trace.append("Guardrail agent blocked the request.")
        return {"safety": report, "trace": trace}

    async def planner_agent(state: AgentState) -> dict:
        if state["safety"].blocked:
            return {"plan": [], "trace": state["trace"] + ["Planner skipped because the request was blocked."]}
        plan = [
            "Retrieve the most relevant knowledge chunks.",
            "Draft an answer using only retrieved evidence.",
            "Validate citations and unsupported claims.",
            "Run judge evaluation and return traceable output.",
        ]
        return {"plan": plan, "trace": state["trace"] + ["Planner agent produced a four-step answer plan."]}

    async def retriever_agent(state: AgentState) -> dict:
        if state["safety"].blocked:
            return {"hits": [], "context_by_id": {}, "trace": state["trace"] + ["Retriever skipped blocked request."]}
        hits = store.search(state["question"], limit=state.get("top_k", 6))
        citations = [
            Citation(
                id=hit.citation_id,
                title=hit.title,
                source_url=hit.source_url,
                snippet=hit.content[:360],
                score=hit.score,
            )
            for hit in hits
        ]
        context_by_id = {hit.citation_id: sanitize_context(hit.content) for hit in hits}
        return {
            "hits": citations,
            "context_by_id": context_by_id,
            "trace": state["trace"] + [f"Retriever agent found {len(citations)} candidate citations."],
        }

    async def summarizer_agent(state: AgentState) -> dict:
        if state["safety"].blocked:
            answer = "This request was blocked because it appears to contain prompt-injection or secret-exfiltration instructions."
            return {"answer": answer, "trace": state["trace"] + ["Summarizer returned a safety response."]}
        context_blocks = [f"[{key}]\n{value}" for key, value in state["context_by_id"].items()]
        answer = await generate_answer(state["question"], context_blocks)
        return {"answer": answer, "trace": state["trace"] + ["Summarizer agent drafted a grounded answer."]}

    async def critic_agent(state: AgentState) -> dict:
        claims = check_claim_support(state["answer"], state["context_by_id"])
        unsupported = [claim for claim in claims if not claim.supported]
        if state["safety"].blocked:
            risk = "blocked"
        elif not state["hits"]:
            risk = "high"
        elif unsupported:
            risk = "medium"
        else:
            risk = "low"
        return {
            "claims": claims,
            "hallucination_risk": risk,
            "trace": state["trace"] + [f"Critic agent flagged hallucination risk as {risk}."],
        }

    async def judge_agent(state: AgentState) -> dict:
        report = await judge_answer(state["question"], state["answer"], state["context_by_id"], state["claims"])
        return {"judge_report": report, "trace": state["trace"] + ["AutoGen judge agent evaluated the answer."]}

    builder = StateGraph(AgentState)
    builder.add_node("guardrail", guardrail_agent)
    builder.add_node("planner", planner_agent)
    builder.add_node("retriever", retriever_agent)
    builder.add_node("summarizer", summarizer_agent)
    builder.add_node("critic", critic_agent)
    builder.add_node("judge", judge_agent)
    builder.add_edge(START, "guardrail")
    builder.add_edge("guardrail", "planner")
    builder.add_edge("planner", "retriever")
    builder.add_edge("retriever", "summarizer")
    builder.add_edge("summarizer", "critic")
    builder.add_edge("critic", "judge")
    builder.add_edge("judge", END)
    return builder.compile()

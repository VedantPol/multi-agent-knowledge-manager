from __future__ import annotations


DEMO_SOURCE_PREFIX = "demo://mak/"


SAMPLE_QUESTIONS = [
    "What must happen when retrieved context is weak?",
    "How does the system handle prompt injection inside source documents?",
    "What does the critic agent check before the answer is trusted?",
    "Which metrics are tracked for LLM-as-Judge evaluation?",
    "What is the incident response process for a high hallucination-risk answer?",
    "How should teams deploy the system for production use?",
    "What audit evidence is kept for each answer?",
    "How does the retriever decide which chunks to cite?",
]


DEMO_DOCUMENTS = [
    {
        "title": "MAK Operating Model",
        "source_url": f"{DEMO_SOURCE_PREFIX}operating-model",
        "content": """
The Multi-Agent Knowledge Manager is designed for enterprise teams that need grounded answers from internal knowledge. It is not a general chatbot. It is a retrieval, reasoning, validation, and evaluation system.

The standard workflow starts when a user asks a question. The guardrail agent scans the request for prompt injection, attempts to reveal system prompts, and secret-exfiltration language. The planner agent then prepares a short execution plan. The retriever agent searches indexed knowledge chunks and returns citations. The summarizer agent writes an answer from retrieved context. The critic agent checks unsupported claims and citation coverage. The judge agent scores the answer.

The system should always make it easy for the user to verify where an answer came from. Every answer should include citation identifiers when context is available. If the retrieved context is weak, the system should say what is missing instead of inventing details.

Production deployments should keep the knowledge database persistent, protect environment variables, and route public traffic through a TLS reverse proxy.
""",
    },
    {
        "title": "Prompt Injection Defense Policy",
        "source_url": f"{DEMO_SOURCE_PREFIX}prompt-injection-defense",
        "content": """
Prompt injection is treated as a first-class security risk. The system blocks user messages that ask it to override governing instructions, reveal system or developer prompts, disable safety controls, exfiltrate API keys, or operate in a fake developer mode.

Source documents can also contain hostile instructions. Before retrieved context is sent to the summarizer, suspicious lines are replaced with a filtered placeholder. This prevents a document from telling the model to ignore citations or override the workflow.

If prompt injection is detected in the user question, the request is blocked and the summarizer returns a safety response. If suspicious instructions are found inside a source document, the document can still be used, but the hostile instruction line is removed from model context.

Reviewers should treat repeated prompt-injection attempts as a signal to inspect the source collection and access controls.
""",
    },
    {
        "title": "Citation and Claim Validation Standard",
        "source_url": f"{DEMO_SOURCE_PREFIX}citation-validation",
        "content": """
Every important answer claim must be grounded in retrieved evidence. The preferred citation format is a compact identifier such as D3-C9, where D is the document identifier and C is the chunk identifier.

The critic agent splits the generated answer into claims and compares each claim against retrieved context. A claim is considered supported when it has meaningful term overlap with at least one retrieved source chunk and, when citations are present, the cited chunk overlaps the claim.

Unsupported claims are not automatically hidden, because the user should be able to inspect them. Instead, they are flagged in the Claims tab as Needs review. A response with unsupported claims usually receives medium hallucination risk. A response with no retrieved citations receives high hallucination risk.

The system is optimized for transparency over false confidence.
""",
    },
    {
        "title": "LLM-as-Judge Evaluation Guide",
        "source_url": f"{DEMO_SOURCE_PREFIX}judge-evaluation",
        "content": """
The judge evaluates whether the final answer is faithful to retrieved context. When an OpenAI API key is configured, AutoGen AgentChat creates a judge agent that reviews the question, answer, and cited context. The judge returns a concise assessment.

When no API key is configured, the system uses a deterministic heuristic fallback. The fallback score starts at 1.0 and is reduced for unsupported claims. If no context is retrieved, the score is 0.0 and the verdict is no_context.

Recommended evaluation fields are score, verdict, mode, unsupported_claims, and a short reason. The score is not a replacement for citations. It is an additional quality signal that helps triage answers.

Teams should sample judged outputs weekly and compare judge scores with human review notes.
""",
    },
    {
        "title": "Retriever Operations Manual",
        "source_url": f"{DEMO_SOURCE_PREFIX}retriever-operations",
        "content": """
The retriever searches a SQLite FTS5 index built from document chunks. Documents are split into overlapping chunks so answers can cite focused evidence instead of entire files.

Top K controls how many chunks are returned to the agent graph. A lower Top K value makes answers more focused, while a higher Top K value can help when the answer spans several documents. The default value is six chunks.

Retrieved chunks are converted into citation cards with title, optional source URL, snippet, and score. These cards are shown to the user so they can inspect the evidence directly.

If the retriever returns no chunks, the summarizer should not guess. The answer should explain that the knowledge base does not yet contain enough supporting context.
""",
    },
    {
        "title": "Answer Quality Playbook",
        "source_url": f"{DEMO_SOURCE_PREFIX}answer-quality",
        "content": """
A high-quality answer is grounded, concise, and reviewable. It should answer the user's question directly, include citations when context is available, avoid unsupported claims, and make uncertainty visible.

The answer should not cite sources that were not retrieved. It should not use citations as decoration. Citations must point to evidence that actually supports the claim.

When context is partial, the answer can provide a partial response and clearly describe what additional source material is needed. The system should prefer a precise refusal over an impressive but unsupported answer.

The Claims tab is intended for reviewers and operators. A claim marked Needs review should be checked against citations before being used in a decision.
""",
    },
    {
        "title": "Incident Response for Unsafe Answers",
        "source_url": f"{DEMO_SOURCE_PREFIX}incident-response",
        "content": """
An unsafe answer is any answer with high hallucination risk, blocked safety status, missing citations for factual claims, or obvious mismatch between citation text and answer text.

For high-risk answers, the operator should preserve the question, answer, citations, claim checks, judge report, and trace. The source collection should be reviewed to determine whether documents are missing, stale, or contaminated with prompt-injection content.

If the unsafe answer influenced a business decision, the decision owner should be notified and a corrected answer should be generated after the knowledge base is updated.

Recurring unsafe answers should trigger evaluation dataset updates and additional regression tests.
""",
    },
    {
        "title": "Deployment and Operations Checklist",
        "source_url": f"{DEMO_SOURCE_PREFIX}deployment-checklist",
        "content": """
The recommended deployment target is a Docker host running the application behind Nginx or Caddy. The application listens on port 8000 inside the container. Public traffic should use HTTPS.

The SQLite knowledge database must be stored on a persistent volume. Environment variables should be provided through a server-side .env file or secret manager. The OpenAI API key is optional but required for live LLM answer generation and AutoGen judge evaluation.

Health checks should call /health. Operators should also test /api/documents and /api/ask after deployment.

Backups should include the persistent data volume and the exact application version deployed.
""",
    },
    {
        "title": "Audit Trail Requirements",
        "source_url": f"{DEMO_SOURCE_PREFIX}audit-trail",
        "content": """
Each answer should expose enough information for an auditor to reconstruct how it was produced. The minimum audit record includes the original question, answer, citation list, safety report, claim checks, hallucination risk, judge report, and agent trace.

The trace records major workflow events, including guardrail scanning, planning, retrieval count, summarization, critic risk level, and judge completion.

For regulated workflows, teams should persist audit records outside the transient UI response. This demo returns the audit data in the API response but does not write every query to a separate audit table.

Auditability is a core reason to use multi-agent RAG instead of a single opaque chat completion.
""",
    },
    {
        "title": "Human Review Workflow",
        "source_url": f"{DEMO_SOURCE_PREFIX}human-review",
        "content": """
Human review is required when hallucination risk is medium or high, when the judge verdict is review, when any claim is marked Needs review, or when the answer will be used for legal, financial, security, or customer-facing decisions.

Reviewers should start with the Citations tab, then inspect the Claims tab, then compare the Trace with expected workflow behavior. If the retrieved context does not support the final answer, the answer should be rejected.

The reviewer can improve future behavior by adding missing source documents, rewriting ambiguous source content, or creating evaluation questions that capture the failure.

Low-risk answers can be used for internal exploration, but users should still inspect citations before acting.
""",
    },
    {
        "title": "Demo Banking Knowledge Base",
        "source_url": f"{DEMO_SOURCE_PREFIX}banking-demo",
        "content": """
The demo knowledge base includes sample banking operations content for realistic questions. A KYC review requires valid identity proof, current address proof, PAN or equivalent tax identifier, and consistency between application fields and uploaded documents.

Credit exceptions must include customer profile, requested exception, risk justification, approving manager, and expiration date. Exceptions older than ninety days must be reviewed again.

Customer complaint escalations are classified as standard, urgent, or regulatory. Regulatory complaints require same-day acknowledgement, root-cause analysis, and documented resolution evidence.

This banking content is synthetic and should not be treated as real compliance advice.
""",
    },
    {
        "title": "Demo Engineering Runbook",
        "source_url": f"{DEMO_SOURCE_PREFIX}engineering-runbook",
        "content": """
The engineering runbook describes how to operate the service. Before release, run pytest, build the Docker image, start docker compose, check /health, index a source, and ask a smoke-test question.

If the container is unhealthy, inspect docker compose logs and verify that the data directory is writable. If answer generation fails with an authentication error, check OPENAI_API_KEY and confirm the selected model is available.

If the UI loads but answers return no citations, verify that documents were indexed and that the question shares searchable terms with the source text.

Every deployment should include a rollback plan and a known-good Docker image tag.
""",
    },
]

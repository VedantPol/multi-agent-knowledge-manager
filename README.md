# Multi-Agent Knowledge Manager

> An enterprise-grade GenAI system for citation-backed knowledge workflows, multi-agent answer validation, and auditable LLM evaluation.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent%20Workflow-blueviolet.svg)](https://www.langchain.com/langgraph)
[![AutoGen](https://img.shields.io/badge/AutoGen-LLM%20Judge-black.svg)](https://microsoft.github.io/autogen/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

---

## What Problem Does This Solve?

Enterprise teams often have useful knowledge spread across internal docs, policies, support notes, runbooks, and project records. Standard chatbots are risky for this kind of work because:

- They can answer without evidence.
- They may follow malicious instructions hidden inside source documents.
- They do not always explain which source supports each claim.
- They are hard to evaluate consistently.

**Multi-Agent Knowledge Manager** solves this by combining retrieval, guardrails, critique, citations, and judge evaluation into one deployable system.

It is built to demonstrate:

- citation-backed RAG answers
- prompt-injection guardrails
- unsupported-claim checks
- hallucination-risk scoring
- LangGraph multi-agent orchestration
- AutoGen-based LLM-as-Judge evaluation
- FastAPI and Docker deployment

---

## Live Demo

Run it locally:

```powershell
docker compose up --build
```

Open:

```text
http://localhost:8723
```

Try this flow:

1. Click **Load demo data** to index the bundled enterprise knowledge base.
2. Select a sample question, or write your own.
3. Watch the progress bar move through each action and agent step.
4. Review the answer, citations, claim checks, agent trace, and judge score.

Example question:

```text
What must happen before model context is built?
```

---

## Website Walkthrough

The website is designed to hold the user's hand from first source upload to final answer verification.

### 1. Add Knowledge

The left sidebar is the source control area.

- **Load demo data** indexes a large synthetic knowledge base covering operating model, prompt-injection defense, citation validation, LLM-as-Judge evaluation, retrieval operations, deployment, audit trails, human review, banking operations, and engineering runbooks.
- **Add Source** lets the user paste a title, optional URL, and document text.
- **Upload .txt** lets the user index a UTF-8 text file.
- Each indexing action shows a progress bar:
  - reading document fields
  - chunking source text
  - writing searchable chunks
  - refreshing the source list

After a source is added, it appears under **Sources** with its chunk count. The user can delete a source, and the source-list progress bar shows that refresh/delete action.

### 2. Ask the Knowledge Base

The main workspace guides the user into asking a question once sources exist.

- **Sample Questions** are clickable prompts that fill the question box for the user.
- The **Top K** control decides how many retrieved chunks the agent can inspect.
- The **Run agents** button starts the LangGraph workflow.
- The agent progress bar advances through:
  - Guardrail
  - Planner
  - Retriever
  - Summarizer
  - Critic
  - Judge

This makes the multi-agent process visible instead of leaving the user staring at a loading spinner.

### 3. Verify the Output

After the answer returns, the guide moves the user to verification.

- **Answer** shows the final cited response.
- **Risk** shows hallucination risk: `low`, `medium`, `high`, or `blocked`.
- **Judge** shows the evaluation score and verdict.
- **Citations** show the exact retrieved source chunks.
- **Claims** show whether each answer claim appears supported.
- **Trace** shows what each agent did during the run.

The goal is that a user can always answer: "Where did this answer come from, and should I trust it?"

### Theme Support

The app defaults to **dark mode**. The **Light theme** toggle switches the full interface into light mode. The preference is stored in the browser with `localStorage`, so the app remembers the user's choice after refresh.

---

## Key Features

### Cited Knowledge Q&A

- Indexes text documents into a local SQLite FTS knowledge store.
- Retrieves relevant chunks for each question.
- Produces answers with citation IDs such as `[D1-C3]`.
- Refuses or weakens confidence when context is missing.

### LangGraph Agent Workflow

The system runs a deterministic multi-agent graph:

- **Guardrail Agent** scans the user question for prompt-injection and secret-exfiltration attempts.
- **Planner Agent** creates the retrieval and validation plan.
- **Retriever Agent** searches the knowledge base and prepares citation context.
- **Summarizer Agent** drafts a grounded answer from retrieved context.
- **Critic Agent** checks unsupported claims and citation coverage.
- **Judge Agent** scores the final answer.

### Enterprise Guardrails

- Blocks common prompt-injection attempts.
- Filters suspicious instructions found inside source documents.
- Checks whether generated claims overlap with retrieved evidence.
- Flags hallucination risk as `low`, `medium`, `high`, or `blocked`.

### LLM-as-Judge Evaluation

- Uses AutoGen AgentChat when `OPENAI_API_KEY` is configured.
- Falls back to deterministic heuristic scoring when no key is available.
- Returns a structured judge report with score, verdict, and details.

### Deployment Ready

- FastAPI backend and static web UI in one service.
- Dockerfile and Docker Compose included.
- Persistent Docker volume for indexed knowledge.
- PowerShell SSH deploy script included.
- GitHub Actions workflow for tests and Docker build.

---

## Architecture

```text
User
  |
  v
Browser UI
  |  add documents / ask questions
  v
FastAPI Backend
  |
  +--> SQLite FTS Knowledge Store
  |
  v
LangGraph Workflow
  |
  +--> Guardrail Agent
  +--> Planner Agent
  +--> Retriever Agent
  +--> Summarizer Agent
  +--> Critic Agent
  +--> AutoGen Judge Agent
  |
  v
Cited Answer + Claim Checks + Judge Score + Trace
```

---

## Tech Stack

**Backend**

- Python 3.11
- FastAPI
- Pydantic
- SQLite FTS5
- pytest

**AI / Agents**

- LangGraph
- AutoGen AgentChat
- OpenAI API, optional
- deterministic fallback mode

**Infrastructure**

- Docker
- Docker Compose
- GitHub Actions
- PowerShell SSH deployment script

---

## Quick Start

### Run with Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Then visit:

```text
http://localhost:8723
```

### Local Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

API docs:

```text
http://localhost:8723/docs
```

When running with Docker Compose, the public host port is `8723` and the app still listens on `8000` inside the container.

### Pull Published Docker Image

```bash
docker pull vedantpol/multi-agent-knowledge-manager:latest
docker run -d --name mak --restart unless-stopped -p 8723:8000 -v mak_data:/data vedantpol/multi-agent-knowledge-manager:latest
```

Or with the production Compose file:

```bash
cp .env.example .env
docker compose -f docker-compose.prod.yml up -d
```

If you already deployed an older container:

```bash
docker rm -f mak
docker pull vedantpol/multi-agent-knowledge-manager:latest
docker run -d --name mak --restart unless-stopped -p 8723:8000 -v mak_data:/data vedantpol/multi-agent-knowledge-manager:latest
docker logs -f mak
```

---

## API Guide

### Load Demo Data

```http
POST /api/demo/load
```

This indexes the bundled demo documents and returns sample questions.

### Get Sample Questions

```http
GET /api/sample-questions
```

### Add a Document

```http
POST /api/documents
```

```json
{
  "title": "Security Notes",
  "content": "Prompt injection attempts must be filtered before model context is built.",
  "source_url": null
}
```

### Ask a Question

```http
POST /api/ask
```

```json
{
  "question": "What must happen before model context is built?",
  "top_k": 6
}
```

### Response Shape

```json
{
  "answer": "Prompt injection attempts must be filtered before model context is built [D1-C1].",
  "citations": [],
  "claims": [],
  "hallucination_risk": "low",
  "judge": {
    "score": 1.0,
    "verdict": "pass"
  },
  "trace": []
}
```

---

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Current coverage checks:

- prompt-injection detection
- source-context sanitization
- claim-support validation
- document-to-answer API flow
- demo data and sample-question endpoints

---

## Evaluation Model

The critic and judge evaluate three practical risks:

- **Citation validity:** does the answer cite retrieved chunks?
- **Unsupported claims:** does each claim overlap with cited source text?
- **Hallucination risk:** should the answer be trusted, reviewed, or blocked?

When an OpenAI key is present, AutoGen creates a judge agent and asks it to evaluate the final answer against the retrieved context. Without a key, the system still runs locally with heuristic scoring.

---

## Security Notes

- Secrets are loaded from environment variables.
- `.env` is ignored by git.
- Source documents are sanitized before being passed into answer generation.
- The app does not require an external LLM to run.
- The local SQLite database is stored in the Docker volume `mak_data`.

---

## Deployment

### Docker Server Deployment

```powershell
.\scripts\deploy.ps1 -HostName "YOUR_SERVER_IP" -User "YOUR_SSH_USER" -RemotePath "/opt/mak"
```

Server requirements:

- Docker Engine
- Docker Compose plugin
- inbound access to port `8723`, or a reverse proxy to the container

For production, put Nginx or Caddy in front of the app for TLS and domain routing.

### Troubleshooting 500 Errors

Check the service and logs:

```bash
curl http://localhost:8723/health
docker logs --tail 100 mak
```

If you use Compose:

```bash
docker compose -f docker-compose.prod.yml logs --tail 100
```

### Memory Cleanup

The app closes LLM clients after each run, triggers garbage collection after heavy routes, and exposes a manual cleanup endpoint:

```bash
curl -X POST http://localhost:8723/api/admin/memory/collect
```

The production Compose file also caps the container at `768m`; with `restart: unless-stopped`, Docker will restart it if the process ever exceeds that limit.

---

## Resume Highlights

This project demonstrates:

- full-stack GenAI application development
- multi-agent orchestration with LangGraph
- AutoGen LLM-as-Judge evaluation
- prompt-injection guardrails
- citation-backed RAG design
- hallucination and unsupported-claim detection
- FastAPI, Docker, CI, and deploy automation

---

## What I Learned Building This

1. RAG systems need validation, not just retrieval.
2. Source documents can contain hostile instructions, so context needs sanitization.
3. Multi-agent workflows are easiest to reason about when each agent has one job.
4. LLM-as-Judge is useful, but deterministic fallbacks make demos and tests reliable.
5. A deployable GenAI project needs tests, Docker, docs, and operational traces.

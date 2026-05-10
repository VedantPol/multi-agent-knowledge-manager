from fastapi.testclient import TestClient

from app.agents import llm
from app.main import app


def test_document_to_answer_flow() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/documents",
        json={
            "title": "Security Notes",
            "content": "Prompt injection attempts must be filtered before model context is built.",
        },
    )
    assert created.status_code == 200

    asked = client.post("/api/ask", json={"question": "What must happen before model context is built?", "top_k": 4})
    assert asked.status_code == 200
    payload = asked.json()
    assert payload["citations"]
    assert "filtered" in payload["answer"].lower()
    assert payload["hallucination_risk"] in {"low", "medium"}


def test_demo_data_and_sample_questions() -> None:
    client = TestClient(app)

    questions = client.get("/api/sample-questions")
    assert questions.status_code == 200
    assert len(questions.json()) >= 5

    loaded = client.post("/api/demo/load")
    assert loaded.status_code == 200
    payload = loaded.json()
    assert payload["total_documents"] >= 10
    assert payload["sample_questions"]


def test_memory_collect_endpoint() -> None:
    client = TestClient(app)

    response = client.post("/api/admin/memory/collect")

    assert response.status_code == 200
    assert "collected" in response.json()


def test_invalid_openai_key_falls_back(monkeypatch) -> None:
    class FailingCompletions:
        async def create(self, *args, **kwargs):
            from openai import AuthenticationError
            import httpx

            request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
            response = httpx.Response(401, request=request, json={"error": {"message": "bad key"}})
            raise AuthenticationError("bad key", response=response, body=response.json())

    class FailingChat:
        completions = FailingCompletions()

    class FailingClient:
        chat = FailingChat()

        def __init__(self, *args, **kwargs):
            pass

    class FakeSettings:
        openai_api_key = "bad-key"
        openai_model = "gpt-4o-mini"

    monkeypatch.setattr(llm, "AsyncOpenAI", FailingClient)
    monkeypatch.setattr(llm, "get_settings", lambda: FakeSettings())

    client = TestClient(app)
    client.post(
        "/api/documents",
        json={
            "title": "Fallback Notes",
            "content": "Invalid OpenAI keys should fall back to deterministic cited answers.",
        },
    )
    asked = client.post("/api/ask", json={"question": "What should invalid OpenAI keys do?", "top_k": 4})
    assert asked.status_code == 200
    assert asked.json()["citations"]

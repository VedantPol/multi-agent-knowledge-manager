from fastapi.testclient import TestClient

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

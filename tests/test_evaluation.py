from app.agents.evaluation import safe_judge_error


def test_safe_judge_error_redacts_provider_details() -> None:
    error = Exception("Error code: 401 - Incorrect API key provided: AIzaSyC9SECRET")

    reason = safe_judge_error(error)

    assert reason == "llm_judge_auth_unavailable"
    assert "AIza" not in reason

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from backend.main import MODEL, SYSTEM_PROMPT, app


class ChatEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.lifespan = app.router.lifespan_context(app)
        await self.lifespan.__aenter__()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)

    async def test_health_endpoint_returns_service_status(self) -> None:
        response = await self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "service": "nokshi-threads-api"},
        )

    async def test_chat_endpoint_requires_a_groq_api_key(self) -> None:
        with patch.dict(os.environ, {"GROQ_APIKEY": "", "GROQ_API_KEY": ""}):
            response = await self.client.post(
                "/api/chat",
                json={"message": "What is the business about?"},
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn("GROQ_APIKEY", response.json()["detail"])

    async def test_chat_uses_retrieved_passages_and_returns_only_the_answer(self) -> None:
        fake_client = _FakeGroqClient()
        with (
            patch.dict(os.environ, {"GROQ_APIKEY": "test-key"}),
            patch("backend.main.OpenAI", return_value=fake_client) as openai_client,
        ):
            response = await self.client.post(
                "/api/chat",
                json={
                    "message": "Who is responsible for the defective shipment?",
                    "history": [{"role": "user", "content": "What is the case about?"}],
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["answer"], "Review the contract and inspection evidence.")
        self.assertEqual(set(data), {"answer"})
        self.assertEqual(openai_client.call_args.kwargs["base_url"], "https://api.groq.com/openai/v1")
        request = fake_client.completions.request
        self.assertEqual(request["model"], MODEL)
        self.assertIn("no source lists", request["messages"][0]["content"])
        self.assertIn("plain text", SYSTEM_PROMPT)
        self.assertEqual(request["messages"][1]["content"], "What is the case about?")
        self.assertIn("Retrieved document passages:", request["messages"][-1]["content"])
        self.assertIn("Source:", request["messages"][-1]["content"])

    async def test_chat_rejects_oversized_messages(self) -> None:
        response = await self.client.post(
            "/api/chat",
            json={"message": "x" * 1501},
        )

        self.assertEqual(response.status_code, 422)


class _FakeGroqClient:
    def __init__(self) -> None:
        self.completions = _FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)

    def __enter__(self) -> "_FakeGroqClient":
        return self

    def __exit__(self, *_: object) -> None:
        return None


class _FakeCompletions:
    def create(self, **request: object) -> SimpleNamespace:
        self.request = request
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Review the contract and inspection evidence."
                    )
                )
            ]
        )


if __name__ == "__main__":
    unittest.main()

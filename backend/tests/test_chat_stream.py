import json
from types import SimpleNamespace as NS

import pytest

from chat import llm
from chat.models import Message

pytestmark = pytest.mark.django_db


def _events(response) -> list[tuple[str, dict]]:
    body = b"".join(response.streaming_content).decode()
    events = []
    for chunk in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in chunk.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def _start(client, settings):
    settings.ANTHROPIC_API_KEY = ""
    return client.post("/api/chat/conversations/", {"mode": "free"}, format="json").json()["id"]


def test_the_tutor_line_arrives_while_it_is_written(client, settings, monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    cid = _start(client, settings)
    r = client.post(f"/api/chat/conversations/{cid}/messages/stream/", {"text": "I buyed a phone."}, format="json")
    assert r["Content-Type"].startswith("text/event-stream")
    events = _events(r)
    replies = [data["text"] for kind, data in events if kind == "reply"]
    assert len(replies) > 2 and all(replies[i] in replies[i + 1] for i in range(len(replies) - 1))
    kind, done = events[-1]
    assert kind == "done"
    assert done["assistant_message"]["text"] == replies[-1]
    assert done["user_message"]["corrections"][0]["right"] == "bought"
    assert done["usage"]["used"] == 2
    assert Message.objects.filter(conversation_id=cid).count() == 3


def test_problems_before_the_model_are_plain_json_errors(client, settings):
    cid = _start(client, settings)
    r = client.post(f"/api/chat/conversations/{cid}/messages/stream/", {"text": "drugs"}, format="json")
    assert r.status_code == 400 and r.json()["code"] == "filtered"
    settings.CHAT_DAILY_LIMIT = 1
    r = client.post(f"/api/chat/conversations/{cid}/messages/stream/", {"text": "Hello"}, format="json")
    assert r.status_code == 429


def test_an_unavailable_tutor_ends_the_stream_with_an_error(client, settings, monkeypatch):
    cid = _start(client, settings)

    def broken(**kwargs):
        raise llm.TutorUnavailable("api_error")
        yield  # a generator, like the real one

    monkeypatch.setattr("chat.views.stream_tutor", broken)
    events = _events(client.post(f"/api/chat/conversations/{cid}/messages/stream/", {"text": "Hi"}, format="json"))
    assert events == [("error", {"detail": llm.UNAVAILABLE_TEXT, "code": "unavailable", "status": 503})]
    assert not Message.objects.filter(conversation_id=cid, role="user").exists()


class FakeStream:
    """Stands in for client.beta.messages.stream(): text deltas of the JSON, then the parsed message."""

    def __init__(self, chunks, final):
        self.chunks, self.final = chunks, final

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        for chunk in self.chunks:
            if chunk is None:  # a fallback model takes over and starts its own text block
                yield NS(type="content_block_start", content_block=NS(type="text"))
            else:
                yield NS(type="content_block_delta", delta=NS(type="text_delta", text=chunk))

    def get_final_message(self):
        return NS(stop_reason="end_turn", parsed_output=self.final)


def test_the_reply_is_read_from_the_streamed_json_and_restarts_on_a_fallback(settings, monkeypatch):
    settings.ANTHROPIC_API_KEY = "test-key"
    final = llm.offline_reply([])
    chunks = ['{"reply": "Wh', None, '{"reply": "Hello', ' there! \\"Hi\\"', '", "reply_kk": "Сәлем"']
    client = NS(beta=NS(messages=NS(stream=lambda **kw: FakeStream(chunks, final))))
    monkeypatch.setattr(llm, "_client", lambda: client)
    out = list(llm.stream_tutor(system="s", history=[]))
    assert [v for k, v in out if k == "reply"] == ["Wh", "Hello", 'Hello there! "Hi"']
    assert out[-1] == ("final", final)

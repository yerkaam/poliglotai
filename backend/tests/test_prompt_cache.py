"""Prompt caching: the request prefix must stay byte-identical from turn to turn of a chat."""

import json
from types import SimpleNamespace as NS

import pytest

from chat import llm
from chat.models import Conversation
from srs.models import UserVocabulary
from vocabulary.models import Vocabulary

pytestmark = pytest.mark.django_db


class Recorder:
    """A fake Anthropic client that records each request and answers with the offline tutor."""

    def __init__(self):
        self.requests = []
        self.beta = NS(messages=NS(parse=self.parse))

    def parse(self, **kwargs):
        self.requests.append(kwargs)
        usage = NS(input_tokens=10, cache_read_input_tokens=0, cache_creation_input_tokens=0, output_tokens=5)
        return NS(stop_reason="end_turn", parsed_output=llm.offline_reply(kwargs["messages"][1:]), usage=usage)


@pytest.fixture
def recorder(settings, monkeypatch):
    settings.ANTHROPIC_API_KEY = "test-key"
    rec = Recorder()
    monkeypatch.setattr(llm, "_client", lambda: rec)
    return rec


def _dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def test_request_puts_the_shared_core_first_with_a_breakpoint():
    request = llm._request("LEARNER BLOCK", [{"role": "assistant", "content": "Hi!"}])
    core, learner = request["system"]
    assert core == {"type": "text", "text": llm.CORE_PROMPT, "cache_control": {"type": "ephemeral"}}
    assert learner == {"type": "text", "text": "LEARNER BLOCK"}
    assert request["cache_control"] == {"type": "ephemeral"}  # automatic breakpoint at the end of the dialog
    # the core has nothing learner-specific or unformatted in it
    assert "{" not in llm.CORE_PROMPT and "A0" not in llm.CORE_PROMPT


def test_each_turn_extends_the_previous_request_without_changing_it(client, user, recorder):
    cid = client.post("/api/chat/conversations/", {"mode": "free"}, format="json").json()["id"]
    for text in ["I like tea.", "I buyed a phone.", "We will go home."]:
        assert client.post(f"/api/chat/conversations/{cid}/messages/", {"text": text}, format="json").status_code == 201
        # a word learned in between must not change the instructions of this chat
        verb, _ = Vocabulary.objects.get_or_create(word=f"verb{len(text)}", defaults={"is_verb": True})
        UserVocabulary.objects.get_or_create(user=user, vocabulary=verb)

    assert len(recorder.requests) == 4
    for before, after in zip(recorder.requests, recorder.requests[1:], strict=False):
        assert _dump(after["system"]) == _dump(before["system"])
        assert _dump(after["messages"][: len(before["messages"])]) == _dump(before["messages"])
        assert len(after["messages"]) == len(before["messages"]) + 2


def test_the_learner_block_is_stored_once_per_chat(client, user, recorder):
    cid = client.post("/api/chat/conversations/", {"mode": "free"}, format="json").json()["id"]
    stored = Conversation.objects.get(pk=cid).system_prompt
    assert stored and stored == recorder.requests[0]["system"][1]["text"]


def test_verbs_are_listed_in_a_stable_order(client, user, recorder):
    for word in ["swim", "ask", "make"]:
        verb, _ = Vocabulary.objects.get_or_create(word=word, defaults={"is_verb": True})
        UserVocabulary.objects.get_or_create(user=user, vocabulary=verb)
    first = client.post("/api/chat/conversations/", {"mode": "free"}, format="json").json()["id"]
    second = client.post("/api/chat/conversations/", {"mode": "free"}, format="json").json()["id"]
    a, b = (Conversation.objects.get(pk=pk).system_prompt for pk in (first, second))
    assert a == b
    listed = a.split("Verbs they are learning now: ")[1].split(".")[0].split(", ")
    assert listed == sorted(listed)

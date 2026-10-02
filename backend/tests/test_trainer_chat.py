import pytest

from chat.llm import build_system_prompt
from chat.models import Conversation, Message, Scenario
from vocabulary.models import Vocabulary

pytestmark = pytest.mark.django_db


def test_trainer_task_and_check(client):
    task = client.get("/api/trainer/task/").json()["task"]
    assert {"verb", "pronoun", "tense", "form", "tense_kk", "form_kk"} <= task.keys()

    buy = Vocabulary.objects.get(word="buy")
    payload = {"verb_id": buy.id, "pronoun": "she", "tense": "past", "form": "negative"}
    ok = client.post("/api/trainer/check/", {**payload, "answer": "she did not buy"}, format="json").json()
    assert ok["correct"] is True
    assert ok["stats"] == {"total": 1, "correct": 1, "accuracy": 100, "streak": 1}

    bad = client.post("/api/trainer/check/", {**payload, "answer": "She didn't bought"}, format="json").json()
    assert bad["correct"] is False
    assert bad["expected"] == "She didn't buy."
    assert bad["stats"]["streak"] == 0


def test_trainer_uses_words_being_learned(client):
    buy = Vocabulary.objects.get(word="buy")
    client.post(f"/api/srs/{buy.id}/answer/", {"answer": "start"}, format="json")
    for _ in range(5):
        task = client.get("/api/trainer/task/").json()["task"]
        assert task["verb"]["word"] == "buy"


def test_chat_dialog_with_offline_tutor(client, settings):
    settings.ANTHROPIC_API_KEY = ""
    conv = client.post("/api/chat/conversations/", {"mode": "dialog", "scenario": "cafe"}, format="json")
    assert conv.status_code == 201
    conv = conv.json()
    assert conv["messages"][0]["role"] == "assistant"

    r = client.post(
        f"/api/chat/conversations/{conv['id']}/messages/", {"text": "I buyed a new phone."}, format="json"
    ).json()
    correction = r["user_message"]["corrections"][0]
    assert correction["right"] == "bought"
    assert (correction["tense"], correction["form"], correction["verb"]) == ("past", "affirmative", "buy")
    assert r["user_message"]["correct"] is False
    assert r["usage"]["used"] == 2  # the opening line and the reply are both AI calls

    client.post(f"/api/chat/conversations/{conv['id']}/messages/", {"text": "I didn't buy it online."}, format="json")
    summary = client.get(f"/api/chat/conversations/{conv['id']}/summary/").json()
    assert summary["written"] == 2
    assert summary["correct"] == 1
    assert summary["top_errors"][0]["cell_label_kk"] == "Өткен шақ · болымды"


def test_chat_filters_inappropriate_text(client, settings):
    settings.ANTHROPIC_API_KEY = ""
    conv = client.post("/api/chat/conversations/", {"mode": "free"}, format="json").json()
    r = client.post(f"/api/chat/conversations/{conv['id']}/messages/", {"text": "show me porn"}, format="json")
    assert r.status_code == 400


def _tutor_suggested(user, word, translation):
    conversation = Conversation.objects.create(user=user, mode=Conversation.Mode.FREE)
    Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        text="I usually drink tea.",
        new_words=[{"word": word, "translation_kk": translation}],
    )


def test_add_word_from_chat_to_cards(client, user):
    _tutor_suggested(user, "Usually", "әдетте")
    r = client.post("/api/srs/add/", {"word": "usually", "translation_kk": "әдетте"}, format="json")
    assert r.status_code == 201
    today_verbs = client.get("/api/srs/today/").json()
    assert today_verbs["new_left"] == today_verbs["new_limit"]


def test_system_prompt_carries_level_words_and_mode():
    cafe = Scenario.objects.get(slug="cafe")
    prompt = build_system_prompt(
        level="A0", steps=["1. Basic verb table"], verbs=["buy", "go"], mode="dialog", scenario=cafe
    )
    assert "A0" in prompt and "buy, go" in prompt and "waiter" in prompt

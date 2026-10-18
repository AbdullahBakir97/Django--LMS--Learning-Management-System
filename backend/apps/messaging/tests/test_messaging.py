import json
from unittest import mock

import pytest
from asgiref.sync import async_to_sync
from asgiref.testing import ApplicationCommunicator
from rest_framework.test import APIClient

from apps.messaging.models import Conversation
from apps.network.models import Connection
from config.asgi import application
from conftest import UserFactory


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


def connect(a, b):
    Connection.objects.create(requester=a, addressee=b, status="accepted")


@pytest.fixture
def run_events(django_capture_on_commit_callbacks):
    return lambda: django_capture_on_commit_callbacks(execute=True)


@pytest.fixture
def friend(user):
    f = UserFactory(username="sami", first_name="Sami", last_name="Odeh")
    connect(user, f)
    return f


@pytest.mark.django_db
def test_only_connections_and_one_direct_conversation_per_pair(user, auth_client, friend):
    stranger = UserFactory(username="nobody")
    refused = auth_client.post("/api/conversations/", {"usernames": ["nobody"]}, format="json")
    assert refused.status_code == 403 and "nobody" in refused.data["detail"]
    assert (
        auth_client.post("/api/conversations/", {"usernames": ["ghost"]}, format="json").status_code
        == 404
    )
    assert (
        auth_client.post(
            "/api/conversations/", {"usernames": [user.username]}, format="json"
        ).status_code
        == 400
    )

    first = auth_client.post(
        "/api/conversations/", {"usernames": ["sami"], "body": "Hi"}, format="json"
    ).data
    again = (
        client_for(friend)
        .post("/api/conversations/", {"usernames": [user.username]}, format="json")
        .data
    )
    assert first["id"] == again["id"], "the pair shares one direct conversation"
    assert [p["username"] for p in first["people"]] == ["sami"]
    assert first["last_message"]["body"] == "Hi"
    assert Conversation.objects.count() == 1
    assert client_for(stranger).get(f"/api/conversations/{first['id']}/").status_code == 404


@pytest.mark.django_db
def test_messages_unread_and_read(user, auth_client, friend, run_events):
    cid = auth_client.post("/api/conversations/", {"usernames": ["sami"]}, format="json").data["id"]
    fc = client_for(friend)
    with mock.patch("apps.messaging.services.publish_to_user") as push, run_events():
        sent = fc.post(
            f"/api/conversations/{cid}/messages/", {"body": "  Are you coming tonight?  "}
        )
    assert sent.status_code == 201 and sent.data["body"] == "Are you coming tonight?"
    pushed = {(c.args[0], c.args[1]) for c in push.call_args_list}
    assert pushed == {(user.id, "message.created"), (friend.id, "message.created")}

    fc.post(f"/api/conversations/{cid}/messages/", {"body": "Six o'clock"})
    assert auth_client.get("/api/conversations/unread/").data == {"count": 2}
    assert fc.get("/api/conversations/unread/").data == {"count": 0}, "your own messages are read"
    listed = auth_client.get("/api/conversations/").data
    assert listed[0]["unread"] == 2 and listed[0]["last_message"]["body"] == "Six o'clock"

    page = auth_client.get(f"/api/conversations/{cid}/messages/").data["results"]
    assert [m["body"] for m in page] == ["Six o'clock", "Are you coming tonight?"], "newest first"
    with mock.patch("apps.messaging.services.publish_to_user") as push, run_events():
        assert auth_client.post(f"/api/conversations/{cid}/read/").status_code == 204
    assert {c.args[1] for c in push.call_args_list} == {"conversation.read"}
    assert auth_client.get("/api/conversations/unread/").data == {"count": 0}


@pytest.mark.django_db
def test_privacy_edit_and_remove(user, auth_client, friend):
    cid = auth_client.post("/api/conversations/", {"usernames": ["sami"]}, format="json").data["id"]
    mid = auth_client.post(f"/api/conversations/{cid}/messages/", {"body": "draft"}).data["id"]
    outsider = client_for(UserFactory())
    assert outsider.get(f"/api/conversations/{cid}/messages/").status_code == 404
    assert outsider.post(f"/api/conversations/{cid}/messages/", {"body": "x"}).status_code == 404
    assert outsider.patch(f"/api/messages/{mid}/", {"body": "x"}).status_code == 404
    assert client_for(friend).patch(f"/api/messages/{mid}/", {"body": "x"}).status_code == 403

    edited = auth_client.patch(f"/api/messages/{mid}/", {"body": "final"}).data
    assert edited["body"] == "final" and edited["edited"]
    removed = auth_client.delete(f"/api/messages/{mid}/").data
    assert removed["deleted"] and removed["body"] == ""
    assert (
        client_for(friend).get(f"/api/conversations/{cid}/messages/").data["results"][0]["body"]
        == ""
    )


@pytest.mark.django_db
def test_group_threads_need_connections_with_everyone(user, auth_client, friend):
    other = UserFactory(username="lina")
    refused = auth_client.post(
        "/api/conversations/", {"usernames": ["sami", "lina"]}, format="json"
    )
    assert refused.status_code == 403
    connect(other, user)
    group = auth_client.post(
        "/api/conversations/",
        {"usernames": ["sami", "lina"], "title": "Study group"},
        format="json",
    ).data
    assert group["is_group"] and group["title"] == "Study group"
    assert sorted(p["username"] for p in group["people"]) == ["lina", "sami"]
    second = auth_client.post("/api/conversations/", {"usernames": ["sami", "lina"]}, format="json")
    assert second.data["id"] != group["id"], "group threads are separate"


@pytest.mark.django_db(transaction=True)
def test_typing_goes_to_the_other_participants(user, auth_client, friend):
    cid = auth_client.post("/api/conversations/", {"usernames": ["sami"]}, format="json").data["id"]
    ticket = client_for(friend).post("/api/realtime/ticket/").data["ticket"]
    mine = auth_client.post("/api/realtime/ticket/").data["ticket"]

    async def socket(t):
        scope = {
            "type": "websocket",
            "path": "/ws/events/",
            "query_string": f"ticket={t}".encode(),
            "headers": [(b"host", b"localhost"), (b"origin", b"http://localhost")],
            "subprotocols": [],
        }
        c = ApplicationCommunicator(application, scope)
        await c.send_input({"type": "websocket.connect"})
        assert (await c.receive_output(timeout=3))["type"] == "websocket.accept"
        return c

    async def scenario():
        sami, me = await socket(ticket), await socket(mine)
        await me.send_input(
            {
                "type": "websocket.receive",
                "text": json.dumps({"type": "typing", "conversation": cid}),
            }
        )
        got = json.loads((await sami.receive_output(timeout=3))["text"])
        assert got == {
            "event": "conversation.typing",
            "data": {
                "conversation": cid,
                "username": user.username,
                "name": user.get_full_name() or user.username,
            },
        }
        await me.send_input(
            {
                "type": "websocket.receive",
                "text": json.dumps({"type": "typing", "conversation": 999}),
            }
        )
        await me.send_input({"type": "websocket.receive", "text": "not json"})
        assert await sami.receive_nothing(timeout=0.3), "unknown conversations and junk are ignored"
        for c in (sami, me):
            await c.send_input({"type": "websocket.disconnect", "code": 1000})
            await c.wait(timeout=3)

    async_to_sync(scenario)()


@pytest.mark.django_db
def test_removing_a_connection_stops_the_direct_conversation(user, auth_client, friend):
    conversation = auth_client.post("/api/conversations/", {"usernames": ["sami"]}).json()
    url = f"/api/conversations/{conversation['id']}/messages/"
    assert auth_client.post(url, {"body": "hi"}).status_code == 201
    Connection.objects.all().delete()
    assert client_for(friend).post(url, {"body": "still here"}).status_code == 403

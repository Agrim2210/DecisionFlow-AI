import asyncio
from types import SimpleNamespace

from app.domains.identity.api import auth_router
from app.domains.identity.api.schemas import ForgotPasswordRequest


class FakeService:
    def __init__(self) -> None:
        self.cmd = None
        self.reset_result = None
        self.validation_status = "valid"

    async def request_password_reset(self, cmd):
        self.cmd = cmd
        return SimpleNamespace(
            user=SimpleNamespace(email="user@example.com", name="Test User"),
            raw_token="raw-token",
        )

    async def validate_password_reset_token(self, raw_token):
        return self.validation_status

    async def reset_password(self, cmd):
        self.reset_result = cmd
        return SimpleNamespace(status="reset")


class CaptureBackgroundTasks:
    def __init__(self) -> None:
        self.calls = []

    def add_task(self, func, *args, **kwargs) -> None:
        self.calls.append((func, args, kwargs))


class FakeDB:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


def test_forgot_password_sends_reset_email(monkeypatch) -> None:
    captured = {}

    class FakeEmailAdapter:
        async def send_password_reset_email(self, *, recipient_email, recipient_name, reset_url):
            captured["recipient_email"] = recipient_email
            captured["recipient_name"] = recipient_name
            captured["reset_url"] = reset_url
            return True

    fake_service = FakeService()
    monkeypatch.setattr(auth_router, "_build_auth_service", lambda db: fake_service)
    monkeypatch.setattr(auth_router, "EmailAdapter", FakeEmailAdapter)

    background_tasks = CaptureBackgroundTasks()
    fake_db = FakeDB()
    result = asyncio.run(
        auth_router.forgot_password_request(
            request=SimpleNamespace(client=SimpleNamespace(host="127.0.0.1")),
            background_tasks=background_tasks,
            body=ForgotPasswordRequest(email="user@example.com"),
            db=fake_db,
        )
    )

    assert result.message == "If an account exists for that email, a reset link has been sent."
    assert len(background_tasks.calls) == 1
    func, args, kwargs = background_tasks.calls[0]
    asyncio.run(func(*args, **kwargs))
    assert captured["recipient_email"] == "user@example.com"
    assert captured["recipient_name"] == "Test User"
    assert "forgot-password?token=raw-token" in captured["reset_url"]
    assert fake_db.committed is True


def test_forgot_password_page_renders_token_form(monkeypatch) -> None:
    fake_service = FakeService()
    monkeypatch.setattr(auth_router, "_build_auth_service", lambda db: fake_service)

    response = asyncio.run(auth_router.forgot_password_page(token="abc-token", db=object()))

    assert response.status_code == 200
    assert "name=\"token\"" in response.body.decode("utf-8")
    assert "New password" in response.body.decode("utf-8")


def test_forgot_password_confirm_resets_password(monkeypatch) -> None:
    fake_service = FakeService()
    monkeypatch.setattr(auth_router, "_build_auth_service", lambda db: fake_service)

    response = asyncio.run(
        auth_router.forgot_password_confirm(token="abc-token", new_password="NewPass123!", db=object())
    )

    assert response.status_code == 200
    assert "Password reset complete" in response.body.decode("utf-8")
    assert fake_service.reset_result.raw_token == "abc-token"
    assert fake_service.reset_result.new_password == "NewPass123!"

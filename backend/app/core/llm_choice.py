"""The student's model choice: an encrypted cookie in their browser, decrypted per request
into a context variable. The key is never written anywhere on the server."""

import base64
import hashlib
import json
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from http.cookies import SimpleCookie
from typing import Iterator, Literal

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

COOKIE = "paet_llm"
COOKIE_PATH = "/api"
_DAY = 24 * 60 * 60


@dataclass(frozen=True)
class Choice:
    provider: str
    model: str
    base_url: str
    api_key: str = ""
    source: Literal["own", "server"] = "own"

    @property
    def key_hint(self) -> str:
        return self.api_key[-4:] if len(self.api_key) >= 8 else ""

    def __repr__(self) -> str:
        return f"Choice(provider={self.provider!r}, model={self.model!r}, source={self.source!r})"


_current: ContextVar[Choice | None] = ContextVar("llm_choice", default=None)


def current_choice() -> Choice | None:
    return _current.get()


@contextmanager
def use_choice(choice: Choice | None) -> Iterator[None]:
    token = _current.set(choice)
    try:
        yield
    finally:
        _current.reset(token)


def paet_default():
    return use_choice(None)


def has_server_model() -> bool:
    return bool(settings.DEFAULT_LLM_PROVIDER or settings.NVIDIA_API_KEY)


def server_choice() -> Choice | None:
    if not settings.DEFAULT_LLM_PROVIDER:
        return None
    from app.core.llm_providers import PROVIDERS

    provider = PROVIDERS.get(settings.DEFAULT_LLM_PROVIDER)
    base_url = settings.DEFAULT_LLM_BASE_URL or (provider.base_url if provider else "")
    return Choice(settings.DEFAULT_LLM_PROVIDER, settings.DEFAULT_LLM_MODEL, base_url,
                  settings.DEFAULT_LLM_API_KEY, "server")


def _fernet() -> Fernet:
    secret = settings.LLM_COOKIE_SECRET or settings.SECRET_KEY
    digest = hashlib.sha256(f"paet-llm:{secret}".encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encode(choice: Choice) -> str:
    body = json.dumps({"p": choice.provider, "m": choice.model, "b": choice.base_url,
                       "k": choice.api_key})
    return _fernet().encrypt(body.encode()).decode()


def decode(token: str) -> Choice | None:
    try:
        body = json.loads(_fernet().decrypt(token.encode()))
        return Choice(body["p"], body["m"], body["b"], body["k"])
    except (InvalidToken, ValueError, KeyError, TypeError):
        return None


def is_local() -> bool:
    return settings.DEPLOY_MODE == "local"


def cookie_kwargs() -> dict:
    return {"httponly": True, "samesite": "strict", "path": COOKIE_PATH,
            "secure": not is_local(), "max_age": (365 if is_local() else 30) * _DAY}


def set_cookie(response, choice: Choice) -> None:
    response.set_cookie(COOKIE, encode(choice), **cookie_kwargs())


def clear_cookie(response) -> None:
    kwargs = cookie_kwargs()
    response.delete_cookie(COOKIE, path=kwargs["path"], secure=kwargs["secure"],
                           httponly=True, samesite="strict")


def _cookie_from(scope) -> str | None:
    for name, value in scope.get("headers", ()):
        if name == b"cookie":
            jar = SimpleCookie()
            try:
                jar.load(value.decode("latin-1"))
            except Exception:
                return None
            if COOKIE in jar:
                return jar[COOKIE].value
    return None


class LLMChoiceMiddleware:
    """Pure ASGI so the context variable reaches sync endpoints and their threads."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        token = _cookie_from(scope)
        choice = decode(token) if token else None
        stale = token is not None and choice is None

        async def send_clearing(message):
            if message["type"] == "http.response.start":
                kwargs = cookie_kwargs()
                header = (f"{COOKIE}=\"\"; Max-Age=0; Path={kwargs['path']}; HttpOnly; "
                          f"SameSite=Strict{'; Secure' if kwargs['secure'] else ''}")
                message = {**message, "headers": [*message.get("headers", []),
                                                  (b"set-cookie", header.encode())]}
            await send(message)

        with use_choice(choice):
            await self.app(scope, receive, send_clearing if stale else send)

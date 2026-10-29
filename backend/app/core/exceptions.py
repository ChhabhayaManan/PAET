from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AitaError(Exception):
    status_code = 500

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class SubmissionNotFound(AitaError):
    status_code = 404


class ProblemNotFound(AitaError):
    status_code = 404


class ThreadNotFound(AitaError):
    """A chat thread that does not exist or is not this user's: one answer for both,
    so thread ids cannot be probed."""

    status_code = 404


class SessionNotFound(AitaError):
    status_code = 404


class TurnInProgress(AitaError):
    status_code = 409


class OnboardingConflict(AitaError):
    status_code = 409


class InvalidAnswer(AitaError):
    status_code = 422


class ExecutorUnavailable(AitaError):
    status_code = 503


class LLMUnavailable(AitaError):
    status_code = 503


class ModelKeyError(AitaError):
    """The student's own key or model failed. Never an LLMUnavailable, so no caller
    degrades it into a template: the student must see why."""

    status_code = 424

    def __init__(self, code: str, detail: str, provider_message: str = ""):
        super().__init__(detail)
        self.code = code
        self.provider_message = provider_message


class ModelChoiceRejected(AitaError):
    status_code = 422


class LanguageNotExecutable(AitaError):
    status_code = 422


class LanguageCheckRequired(AitaError):
    status_code = 428


class UnverifiableSubmission(AitaError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AitaError)
    def handle(_: Request, exc: AitaError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(ModelKeyError)
    def handle_model_key(_: Request, exc: ModelKeyError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={
            "detail": exc.detail, "code": exc.code, "provider_message": exc.provider_message})

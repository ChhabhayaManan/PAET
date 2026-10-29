from app.core.config import settings
from app.core.exceptions import ModelChoiceRejected, ModelKeyError
from app.core.llm_choice import Choice, is_local, server_choice
from app.core.llm_providers import PROVIDERS, build_client, classify, label, list_models
from app.features.model_settings.schemas import ChoiceIn, ModelSettingsOut, ProviderOut


def view(choice: Choice | None) -> ModelSettingsOut:
    providers = [ProviderOut(id=p.id, label=p.label, base_url=p.base_url, needs_key=p.needs_key,
                             local_only=p.local_only)
                 for p in PROVIDERS.values() if is_local() or not p.local_only]
    if choice is None:
        default = server_choice()
        provider = default.provider if default else "nvidia"
        model = default.model if default else settings.NVIDIA_MODEL
        source, hint = "default", ""
    else:
        provider, model, hint = choice.provider, choice.model, choice.key_hint
        source = "local" if PROVIDERS[provider].local_only else "own"
    return ModelSettingsOut(source=source, provider=provider, provider_label=label(provider),
                            model=model, key_hint=hint, deploy_mode=settings.DEPLOY_MODE,
                            providers=providers)


def resolve(data: ChoiceIn, existing: Choice | None) -> Choice:
    provider = PROVIDERS.get(data.provider)
    if provider is None:
        raise ModelChoiceRejected("Unknown provider.")
    if provider.local_only and not is_local():
        raise ModelChoiceRejected("Local models are only available when you run PAET yourself.")
    base_url = provider.base_url
    if provider.local_only:
        base_url = data.base_url.strip() or provider.base_url
        if not base_url.startswith(("http://", "https://")):
            raise ModelChoiceRejected("Enter the server address, starting with http:// or https://.")
    key = data.api_key.strip()
    if not key and existing is not None and existing.provider == provider.id:
        key = existing.api_key
    if provider.needs_key and not key:
        raise ModelChoiceRejected(f"Enter your {provider.label} API key.")
    return Choice(provider.id, data.model.strip(), base_url.rstrip("/"), key)


def check(choice: Choice) -> list[str]:
    """Lists the account's models, then sends one tiny request when a model is chosen.
    Listing alone does not prove a key on every provider (OpenRouter's list is public)."""
    try:
        models = list_models(choice)
    except ModelKeyError as error:
        if not choice.model or error.code not in ("model_not_found", "provider_error"):
            raise
        models = []
    if choice.model:
        try:
            build_client(choice, temperature=0.0, max_tokens=16, timeout=30).invoke("Reply with OK.")
        except ModelKeyError:
            raise
        except Exception as exc:
            raise classify(exc, choice) from exc
    return models

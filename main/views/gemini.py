from __future__ import annotations

import logging

import google.generativeai as genai
from django.conf import settings
from google.api_core import exceptions as google_exceptions

LOG = logging.getLogger(__name__)

# Configure Gemini API
try:
    genai.configure(api_key=getattr(settings, "GEMINI_API_KEY", ""))
except Exception as exc:  # pragma: no cover - configuration should succeed
    LOG.warning("Gemini API configuration failed: %s", exc)

FALLBACK_MODEL_SEQUENCE = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.0-flash",
]


def _expand_model_candidates(primary: str | None, fallbacks: list[str]) -> list[str]:
    candidates: list[str] = []

    def add_variant(name: str | None) -> None:
        if not name:
            return
        variants = [name]
        if name.startswith("models/"):
            stripped = name[len("models/") :]
            if stripped:
                variants.append(stripped)
        else:
            variants.append(f"models/{name}")
        for variant in variants:
            if variant and variant not in candidates:
                candidates.append(variant)

    add_variant(primary)
    for fallback in fallbacks:
        add_variant(fallback)

    return candidates


def ask_gemini(
    prompt: str,
    model_name: str = "gemini-2.5-flash",
    system_prompt: str | None = None,
    timeout: int = 30,
) -> str:
    """Query Gemini, falling back to supported models when necessary."""

    tried_models: list[str] = []
    errors: list[str] = []

    model_candidates = _expand_model_candidates(model_name, FALLBACK_MODEL_SEQUENCE)

    for candidate in model_candidates:
        tried_models.append(candidate)
        try:
            model = genai.GenerativeModel(candidate)

            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2000,
                    temperature=0.7,
                ),
            )

            if getattr(response, "text", None):
                if candidate != model_name:
                    LOG.info(
                        "Gemini model %s unavailable, fell back to %s",
                        model_name,
                        candidate,
                    )
                return response.text.strip()

            return "Sorry, I couldn't generate a response."

        except google_exceptions.NotFound as nf_err:
            LOG.warning("Gemini model %s not found: %s", candidate, nf_err)
            errors.append(str(nf_err))
            continue
        except google_exceptions.GoogleAPICallError as api_err:
            LOG.warning("Gemini API call error on %s: %s", candidate, api_err)
            errors.append(str(api_err))
            continue
        except Exception as exc:  # pragma: no cover - defensive guard
            LOG.exception("Unexpected Gemini error using %s: %s", candidate, exc)
            errors.append(str(exc))
            continue

    if any("API_KEY" in err.upper() for err in errors):
        return "Gemini API key is invalid or has been disabled. Please contact your admin to verify the API key."
    if any("QUOTA" in err.upper() or "LIMIT" in err.upper() for err in errors):
        return "Quota exceeded. Please try again later."

    if errors:
        merged = "; ".join(errors[-2:])
        return (
            "Sorry, I'm temporarily unable to generate a response. "
            f"Please try again in a moment or contact your admin if the problem persists."
        )

    return "Sorry, there was an unexpected error with the AI service."


def get_gemini_embedding(text, model_name: str = "text-embedding-004"):
    """Return an embedding vector for the supplied text."""
    try:
        import numpy as np

        result = genai.embed_content(
            model=model_name,
            content=text,
            task_type="retrieval_document",
        )

        if result and "embedding" in result:
            return np.array(result["embedding"], dtype=np.float32)
        return None

    except Exception as exc:  # pragma: no cover - defensive guard
        LOG.exception("Gemini embedding error: %s", exc)
        return None


def list_available_models() -> list[str]:
    """List Gemini models that support generateContent."""
    try:
        models = genai.list_models()
        available = []
        for model in models:
            if "generateContent" in getattr(model, "supported_generation_methods", []):
                available.append(model.name)
        return available
    except Exception as exc:  # pragma: no cover - defensive guard
        LOG.exception("Error listing models: %s", exc)
        return []

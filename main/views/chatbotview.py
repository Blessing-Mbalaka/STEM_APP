from __future__ import annotations

import hashlib
import json
import re
from datetime import timedelta
from typing import Any, Dict, List
from urllib.parse import quote_plus

import requests
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .gemini import ask_gemini
from main.utils.resources import snapshot_resource_links
from main.utils.yaml_logger import (
    CHATBOT_HISTORY_FILE,
    append_yaml_record,
    load_yaml_records,
    log_student_search,
    write_yaml_records,
)

try:
    from main.models import (
        ChatbotCache,
        ChatbotConversation,
        ChatbotResponse,
        PDFChunk,
    )
except ImportError:
    ChatbotCache = None  # type: ignore
    ChatbotConversation = None  # type: ignore
    ChatbotResponse = None  # type: ignore
    PDFChunk = None  # type: ignore


# ---------------------------------------------------------------------------
# Arithmetic seeding
# ---------------------------------------------------------------------------

def _seed_arithmetic_history(max_operand: int = 12) -> None:
    try:
        records = load_yaml_records(CHATBOT_HISTORY_FILE)
    except Exception:
        records = []

    existing_keys = set()
    for entry in records:
        meta = entry.get("metadata") or {}
        if meta.get("kind") == "arithmetic_fact":
            operands = tuple(meta.get("operands") or [])
            operation = meta.get("operation")
            existing_keys.add((operation, operands))

    new_entries: List[Dict[str, Any]] = []

    def _maybe_add(a: int, b: int, operation: str, answer: int, symbol: str) -> None:
        operands = (a, b)
        if (operation, operands) in existing_keys:
            return
        existing_keys.add((operation, operands))
        question = f"What is {a} {symbol} {b}?"
        new_entries.append(
            {
                "timestamp": timezone.now().isoformat(),
                "user": {"id": None, "username": "seed"},
                "question": question,
                "answer": str(answer),
                "sources": [],
                "response_type": "arithmetic_seed",
                "metadata": {
                    "kind": "arithmetic_fact",
                    "operation": operation,
                    "operands": [a, b],
                },
            }
        )

    for a in range(max_operand + 1):
        for b in range(max_operand + 1):
            _maybe_add(a, b, "addition", a + b, "+")
            _maybe_add(a, b, "multiplication", a * b, "×")

    if new_entries:
        write_yaml_records(CHATBOT_HISTORY_FILE, records + new_entries)


try:  # pragma: no cover - best effort seeding
    _seed_arithmetic_history()
except Exception:
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coerce_sources(raw_sources: Any) -> List[Dict[str, Any]]:
    if not raw_sources:
        return []
    if isinstance(raw_sources, str):
        try:
            data = json.loads(raw_sources)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            return [{"title": raw_sources}]
    if isinstance(raw_sources, list):
        return raw_sources
    return [raw_sources]


def _log_chatbot_event(
    *,
    user,
    question: str,
    answer: str,
    sources: Any = None,
    response_type: str = "",
    conversation=None,
    conversation_id=None,
    metadata: Dict[str, Any] | None = None,
) -> None:
    if not question and not answer:
        return

    user_payload = {
        "id": getattr(user, "id", None) if getattr(user, "is_authenticated", False) else None,
        "username": getattr(user, "username", "anonymous") if getattr(user, "is_authenticated", False) else "anonymous",
    }

    payload = {
        "timestamp": timezone.now().isoformat(),
        "user": user_payload,
        "question": question,
        "answer": answer,
        "sources": _coerce_sources(sources),
        "response_type": response_type,
    }
    if conversation is not None:
        payload["conversation_id"] = getattr(conversation, "id", None)
    elif conversation_id is not None:
        payload["conversation_id"] = conversation_id
    if metadata:
        payload["metadata"] = metadata

    append_yaml_record(
        CHATBOT_HISTORY_FILE,
        payload,
        max_entries=1000,
    )


def _compute_basic_arithmetic(question: str):
    """Return tuple (response_text, sources, metadata) for simple addition/multiplication."""
    cleaned = question.strip().lower().replace("?", "")
    replacements = [
        ("plus", "+"),
        ("added to", "+"),
        ("add to", "+"),
        (" add ", " + "),
        (" and ", " + "),
        ("times", "*"),
        ("multiplied by", "*"),
        ("multiply by", "*"),
        ("x", "*"),
        ("×", "*"),
    ]
    for old, new in replacements:
        cleaned = cleaned.replace(old, new)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"^what is ", "", cleaned)

    arithmetic_re = re.compile(r"^(-?\d+)\s*([+*])\s*(-?\d+)$")
    match = arithmetic_re.match(cleaned)
    if not match:
        return None

    left, operator, right = match.groups()
    a, b = int(left), int(right)

    if operator == "+":
        result = a + b
        operation = "addition"
        symbol = "+"
    else:
        result = a * b
        operation = "multiplication"
        symbol = "×"

    response = f"{a} {symbol} {b} = {result}"
    metadata = {
        "kind": "arithmetic_fact",
        "operation": operation,
        "operands": [a, b],
    }
    sources = [
        {
            "title": "Basic arithmetic fact",
            "snippet": response,
        }
    ]
    return response, sources, metadata


# ---------------------------------------------------------------------------
# Core chatbot API
# ---------------------------------------------------------------------------

@csrf_exempt
def chatbot_api(request):
    """Enhanced chatbot API with RAG, caching and optional internet search."""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    user_question = (
        data.get("question")
        or data.get("prompt")
        or data.get("message")
        or ""
    ).strip()

    if not user_question:
        return JsonResponse({"error": "Question is required"}, status=400)

    try:
        conversation = None
        if ChatbotConversation and request.user.is_authenticated:
            conversation = ChatbotConversation.objects.create(
                user=request.user,
                question=user_question,
                created_at=timezone.now(),
            )

        arithmetic_hit = _compute_basic_arithmetic(user_question)
        if arithmetic_hit:
            response_text, sources, metadata = arithmetic_hit
            response_payload = {
                "response": response_text,
                "sources": sources,
                "conversation_id": conversation.id if conversation else None,
                "from_cache": False,
                "from_arithmetic": True,
            }

            cache_response(user_question, response_text, sources, request.user)

            if ChatbotResponse and conversation:
                ChatbotResponse.objects.create(
                    conversation=conversation,
                    response=response_text,
                    sources=json.dumps(sources),
                    response_type="arithmetic",
                )

            _log_chatbot_event(
                user=request.user,
                question=user_question,
                answer=response_text,
                sources=sources,
                response_type="arithmetic",
                conversation=conversation,
                metadata=metadata,
            )

            return JsonResponse(response_payload)

        # 1. Cache lookup (per user)
        cached_response = check_cache(user_question, request.user)
        if cached_response:
            response_data = {
                "response": cached_response["answer"],
                "sources": cached_response.get("sources", []),
                "from_cache": True,
                "conversation_id": conversation.id if conversation else None,
            }
            if ChatbotResponse and conversation:
                ChatbotResponse.objects.create(
                    conversation=conversation,
                    response=cached_response["answer"],
                    sources=json.dumps(cached_response.get("sources", [])),
                    response_type="cached",
                )
            _log_chatbot_event(
                user=request.user,
                question=user_question,
                answer=cached_response["answer"],
                sources=cached_response.get("sources", []),
                response_type="cached",
                conversation=conversation,
                metadata={"from_cache": True},
            )
            return JsonResponse(response_data)

        # 2. Knowledge base lookup
        rag_result = search_pdf_knowledge(user_question)
        if rag_result["found"]:
            response = generate_rag_response(user_question, rag_result["context"])
            response_data = {
                "response": response,
                "sources": rag_result["sources"],
                "from_cache": False,
                "has_sources": True,
                "conversation_id": conversation.id if conversation else None,
            }
            cache_response(user_question, response, rag_result["sources"], request.user)
            if ChatbotResponse and conversation:
                ChatbotResponse.objects.create(
                    conversation=conversation,
                    response=response,
                    sources=json.dumps(rag_result["sources"]),
                    response_type="rag",
                )
            _log_chatbot_event(
                user=request.user,
                question=user_question,
                answer=response,
                sources=rag_result["sources"],
                response_type="rag",
                conversation=conversation,
                metadata={"source": "rag"},
            )
            return JsonResponse(response_data)

        # 3. No match – surface local resources and perform internet search automatically
        resource_links = snapshot_resource_links()
        suggested_links = resource_links[:8]
        search_payload = run_internet_search_flow(
            user_question,
            request.user,
            conversation=conversation,
            local_resources=suggested_links,
            metadata={"auto_search": True},
        )
        return JsonResponse(search_payload)

    except Exception as exc:  # pragma: no cover - defensive
        return JsonResponse({"error": str(exc)}, status=500)


# ---------------------------------------------------------------------------
# Knowledge base helpers
# ---------------------------------------------------------------------------

def check_cache(question: str, user) -> Dict[str, Any] | None:
    """Return cached answer when available for authenticated users."""
    if not ChatbotCache or not getattr(user, "is_authenticated", False):
        return None

    question_hash = hashlib.md5(question.lower().encode()).hexdigest()
    cutoff = timezone.now() - timedelta(days=7)
    cache_entry = (
        ChatbotCache.objects.filter(
            question_hash=question_hash,
            created_at__gte=cutoff,
            user=user,
        )
        .order_by("-created_at")
        .first()
    )
    if not cache_entry:
        return None
    return {
        "answer": cache_entry.answer,
        "sources": json.loads(cache_entry.sources) if cache_entry.sources else [],
    }


def search_pdf_knowledge(question: str) -> Dict[str, Any]:
    """Lightweight keyword-based retrieval from uploaded PDF chunks."""
    if not PDFChunk:
        return {"found": False, "context": "", "sources": []}

    keywords = [kw for kw in question.lower().split() if len(kw) > 2]
    if not keywords:
        return {"found": False, "context": "", "sources": []}

    matches: List[Dict[str, Any]] = []
    for chunk in PDFChunk.objects.select_related("document").all():
        text = chunk.content.lower()
        score = sum(1 for kw in keywords if kw in text)
        if score:
            matches.append(
                {
                    "chunk": chunk,
                    "score": score,
                    "preview": chunk.content[:600],
                }
            )

    if not matches:
        return {"found": False, "context": "", "sources": []}

    matches.sort(key=lambda item: item["score"], reverse=True)
    top_matches = matches[:3]

    context = "\n\n".join(m["preview"] for m in top_matches)
    sources = []
    for match in top_matches:
        chunk = match["chunk"]
        doc = chunk.document
        file_field = getattr(doc, "file", None)
        file_url = ""
        if file_field:
            try:
                file_url = file_field.url
            except Exception:
                file_url = ""
        sources.append(
            {
                "title": getattr(doc, "title", "Course Material"),
                "page": chunk.page_number,
                "url": file_url,
            }
        )

    return {"found": True, "context": context, "sources": sources}


def generate_rag_response(question: str, context: str) -> str:
    """Use Gemini helper to compose a response using retrieved context."""
    prompt = (
        "You are an academic tutor tasked with answering student questions concisely. "
        "Use the provided context to answer. If the context does not contain the answer, "
        "state that clearly. Limit the response to 2-3 sentences.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )
    return ask_gemini(prompt)


def cache_response(question: str, answer: str, sources: List[Dict[str, Any]], user) -> None:
    """Persist chatbot responses for authenticated users."""
    if not ChatbotCache or not getattr(user, "is_authenticated", False):
        return

    question_hash = hashlib.md5(question.lower().encode()).hexdigest()
    ChatbotCache.objects.create(
        question_hash=question_hash,
        question=question,
        answer=answer,
        sources=json.dumps(sources),
        user=user,
        created_at=timezone.now(),
    )


# ---------------------------------------------------------------------------
# Internet search
# ---------------------------------------------------------------------------

_RESULT_LINK_RE = re.compile(r'result__a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S)
_RESULT_SNIPPET_RE = re.compile(r'result__snippet[^>]*>(.*?)</div>', re.S)
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _duckduckgo_html_results(query: str) -> List[Dict[str, str]]:
    try:
        resp = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        resp.raise_for_status()
        html = resp.text
    except Exception:
        return []

    results: List[Dict[str, str]] = []
    snippets_iter = _RESULT_SNIPPET_RE.finditer(html)
    snippet_list = [re.sub(_HTML_TAG_RE, "", m.group(1)).strip() for m in snippets_iter]
    snippet_index = 0

    for match in _RESULT_LINK_RE.finditer(html):
        url = match.group(1)
        title = re.sub(_HTML_TAG_RE, "", match.group(2)).strip()
        snippet = ""
        if snippet_index < len(snippet_list):
            snippet = snippet_list[snippet_index]
            snippet_index += 1
        results.append(
            {
                "title": title[:120] or "DuckDuckGo Result",
                "url": url,
                "snippet": snippet[:280],
            }
        )
        if len(results) >= 6:
            break
    return results


def _fetch_page_excerpt(url: str, max_chars: int = 600) -> str:
    if not url:
        return ""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8,
        )
        resp.raise_for_status()
        text = resp.text[:200000]
        text = _SCRIPT_STYLE_RE.sub(" ", text)
        text = _HTML_TAG_RE.sub(" ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()[:max_chars]
    except Exception:
        return ""

def internet_search_api(request):
    """Perform an on-demand internet search when RAG content is missing."""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    search_query = (payload.get("query") or "").strip()
    conversation_id = payload.get("conversation_id")

    if not search_query:
        return JsonResponse({"error": "Search query is required"}, status=400)

    try:
        payload = run_internet_search_flow(
            search_query,
            request.user,
            conversation_id=conversation_id,
            metadata={"manual_search": True},
        )
        return JsonResponse(payload)
    except Exception as exc:  # pragma: no cover - defensive
        return JsonResponse({"error": str(exc)}, status=500)


def perform_internet_search(query: str) -> List[Dict[str, str]]:
    """DuckDuckGo API wrapper with graceful fallbacks."""
    search_url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1",
    }

    data: Dict[str, Any] = {}
    try:
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception:
        data = {}

    results: List[Dict[str, str]] = []

    def _append_entry(text: str, url: str = "", snippet: str | None = None) -> None:
        if not text and not snippet:
            return
        entry = {
            "title": text[:120] if text else (snippet or "")[:120],
            "url": url,
            "snippet": (snippet or text)[:280],
        }
        if entry not in results:
            results.append(entry)

    for item in data.get("Results", []):
        if item.get("Text"):
            _append_entry(item["Text"], item.get("FirstURL", ""))

    def _walk_topics(topics):
        for topic in topics:
            if "Topics" in topic:
                _walk_topics(topic["Topics"])
            elif topic.get("Text"):
                _append_entry(topic["Text"], topic.get("FirstURL", ""))

    _walk_topics(data.get("RelatedTopics", []))

    abstract_text = data.get("AbstractText")
    abstract_url = data.get("AbstractURL") or data.get("AbstractSource")
    if abstract_text:
        _append_entry(abstract_text, abstract_url or "")

    heading = data.get("Heading")
    answer = data.get("Answer") or data.get("Abstract")
    if answer and heading:
        _append_entry(f"{heading}: {answer}", abstract_url or "")

    if not results:
        results.extend(_duckduckgo_html_results(query))

    if not results:
        results.append(
            {
                "title": "View DuckDuckGo results",
                "url": f"https://duckduckgo.com/?q={quote_plus(query)}",
                "snippet": "Open the DuckDuckGo results page for more details.",
                "is_fallback": True,
            }
        )

    return results


def generate_search_response(
    query: str, search_results: List[Dict[str, str]]
) -> tuple[str, List[Dict[str, str]]]:
    if not search_results:
        fallback = (
            "I couldn't find relevant information online. "
            "Please try rephrasing your question or consult your instructor for more guidance."
        )
        return fallback, []

    enriched: List[Dict[str, str]] = []
    lines = [
        f"Here's what I found online for \"{query}\":",
        "",
    ]

    for idx, result in enumerate(search_results, start=1):
        snippet = (result.get("snippet") or "").strip()
        if (not snippet or len(snippet) < 60) and result.get("url"):
            snippet = _fetch_page_excerpt(result["url"])
        if not snippet:
            snippet = result.get("title", "").strip()
        excerpt = (snippet or "No preview available.")[:280].strip()

        enriched.append({**result, "excerpt": excerpt})

        if idx <= 3:
            lines.append(f"{idx}. {excerpt}")
            if result.get("url"):
                lines.append(f"   Source: {result['url']}")
            lines.append("")

    lines.append("Please verify this information against your course materials.")
    fallback_text = "\n".join(lines)

    top_context: List[str] = []
    for idx, result in enumerate(enriched[:3], start=1):
        if result.get("is_fallback"):
            continue
        context_excerpt = result.get("excerpt", "")
        context_url = result.get("url", "")
        context_title = result.get("title", "")
        top_context.append(
            f"Result {idx}:\nTitle: {context_title}\nURL: {context_url}\nExcerpt: {context_excerpt}"
        )

    try:
        if top_context:
            prompt = (
                "You are an academic tutor providing reliable answers based on the supplied web excerpts.\n"
                "Summarise the key points that answer the student's question in 2-3 sentences.\n"
                "If the information is unclear, state that instead of guessing.\n"
                f"Question: {query}\n"
                f"Context:\n{'\n\n'.join(top_context)}\n"
                "Answer:"
            )
        else:
            prompt = (
                "You are an academic tutor. Provide a concise, accurate answer to the student's question.\n"
                "You may rely on your pretrained knowledge base when no web excerpts are supplied.\n"
                "Limit the response to 2-3 sentences.\n"
                f"Question: {query}\n"
                "Answer:"
            )
        llm_response = ask_gemini(prompt).strip()
        if llm_response:
            fallback_text = llm_response
    except Exception:
        pass

    return fallback_text, enriched


def run_internet_search_flow(
    query: str,
    user,
    *,
    conversation=None,
    conversation_id=None,
    local_resources=None,
    metadata: Dict[str, Any] | None = None,
):
    log_meta: Dict[str, Any] = dict(metadata or {})
    if local_resources:
        log_meta["local_resources"] = local_resources
    if conversation is not None:
        log_meta["conversation_id"] = conversation.id
    elif conversation_id is not None:
        log_meta["conversation_id"] = conversation_id

    log_student_search(
        query,
        user=user if getattr(user, "is_authenticated", False) else None,
        source="chatbot_internet_search",
        metadata=log_meta,
    )

    results = perform_internet_search(query)
    response_text, enriched_results = generate_search_response(query, results)

    conv_id = conversation.id if conversation is not None else conversation_id
    cache_response(query, response_text, enriched_results, user)

    if ChatbotResponse:
        if conversation is not None:
            ChatbotResponse.objects.create(
                conversation=conversation,
                response=response_text,
                sources=json.dumps(enriched_results),
                response_type="internet_search",
            )
        elif conversation_id is not None:
            ChatbotResponse.objects.create(
                conversation_id=conversation_id,
                response=response_text,
                sources=json.dumps(enriched_results),
                response_type="internet_search",
            )

    log_metadata = {"from_internet": True}
    if metadata:
        log_metadata.update(metadata)
    if local_resources:
        log_metadata["local_resources"] = local_resources

    _log_chatbot_event(
        user=user,
        question=query,
        answer=response_text,
        sources=enriched_results,
        response_type="internet_search",
        conversation=conversation,
        conversation_id=conversation_id,
        metadata=log_metadata,
    )

    payload = {
        "response": response_text,
        "sources": enriched_results,
        "from_internet": True,
        "conversation_id": conv_id,
    }

    if local_resources:
        payload["local_resources"] = local_resources

    return payload


# ---------------------------------------------------------------------------
# Conversation history
# ---------------------------------------------------------------------------

@login_required
def chatbot_history_api(request):
    """Return recent chatbot conversations for the authenticated user."""
    if not ChatbotConversation:
        return JsonResponse({"conversations": []})

    conversations = (
        ChatbotConversation.objects.filter(user=request.user)
        .order_by("-created_at")[:20]
    )

    history = []
    for conversation in conversations:
        responses = []
        if ChatbotResponse:
            responses = [
                {
                    "response": resp.response,
                    "type": resp.response_type,
                    "sources": _coerce_sources(resp.sources),
                }
                for resp in ChatbotResponse.objects.filter(conversation=conversation)
            ]

        history.append(
            {
                "id": conversation.id,
                "question": conversation.question,
                "created_at": conversation.created_at.isoformat(),
                "responses": responses,
            }
        )

    return JsonResponse({"conversations": history})

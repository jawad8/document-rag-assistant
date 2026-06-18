import json
import os
import re

import numpy as np
import requests
from bs4 import BeautifulSoup
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from sentence_transformers import SentenceTransformer

from documents.models import DocumentChunk

model = SentenceTransformer("all-MiniLM-L6-v2")


def cosine_similarity(a, b):
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    if denominator == 0:
        return 0.0
    return float(np.dot(a, b) / denominator)


def extract_text_from_url(url):
    response = requests.get(
        url,
        timeout=10,
        headers={"User-Agent": "DocumentRAGAssistant/1.0"},
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text[:2_000_000], "html.parser")

    for element in soup(["script", "style", "noscript"]):
        element.extract()

    return soup.get_text(separator="\n")


def chunk_text(text, size=500):
    return [text[i : i + size] for i in range(0, len(text), size)]


def ollama_stream(prompt, sources):
    yield json.dumps({"sources": sources}) + "\n"

    response = requests.post(
        os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate"),
        json={
            "model": os.getenv("OLLAMA_MODEL", "llama3"),
            "prompt": prompt,
            "stream": True,
        },
        stream=True,
        timeout=120,
    )
    response.raise_for_status()

    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode())
            if "response" in data:
                yield data["response"]


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ask_question(request):
    question = request.data.get("question", "").strip()
    if not question:
        return Response({"error": "Question required"}, status=400)

    url_match = re.search(r"(https?://\S+)", question)

    if url_match:
        url = url_match.group(1)
        try:
            text = extract_text_from_url(url)
        except requests.RequestException as exc:
            return Response(
                {"error": f"Could not retrieve URL: {exc}"},
                status=400,
            )

        temporary_chunks = [
            (model.encode(chunk), chunk)
            for chunk in chunk_text(text)[:20]
            if chunk.strip()
        ]
        question_embedding = model.encode(question)
        scored = [
            (cosine_similarity(question_embedding, embedding), content)
            for embedding, content in temporary_chunks
        ]
        scored.sort(key=lambda item: item[0], reverse=True)

        context = "\n".join(content for _, content in scored[:4])
        sources = [url]
    else:
        question_embedding = model.encode(question)
        chunks = DocumentChunk.objects.filter(
            document__user=request.user
        ).exclude(embedding=None)

        if not chunks.exists():
            return Response({"error": "No documents uploaded"}, status=400)

        scored = [
            (
                cosine_similarity(
                    question_embedding,
                    np.asarray(chunk.embedding),
                ),
                chunk,
            )
            for chunk in chunks
        ]
        scored.sort(key=lambda item: item[0], reverse=True)

        top_chunks = scored[:4]
        context = "\n".join(chunk.content for _, chunk in top_chunks)
        sources = sorted({chunk.document.title for _, chunk in top_chunks})

    prompt = f"""
You are a document-grounded knowledge assistant.

Answer only from the supplied context. If the context is insufficient, say so
clearly rather than inventing information.

Context:
{context}

Question:
{question}

Answer:
"""

    return StreamingHttpResponse(
        ollama_stream(prompt, sources),
        content_type="text/plain",
    )

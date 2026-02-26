from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse
from rest_framework.response import Response

from documents.models import Document, DocumentChunk
from sentence_transformers import SentenceTransformer

import numpy as np
import requests
import json
import re
from bs4 import BeautifulSoup

model = SentenceTransformer("all-MiniLM-L6-v2")


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def extract_text_from_url(url):
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    for s in soup(["script", "style", "noscript"]):
        s.extract()

    return soup.get_text(separator="\n")


def chunk_text(text, size=500):
    return [text[i:i+size] for i in range(0, len(text), size)]


def ollama_stream(prompt, sources):
    yield json.dumps({"sources": sources}) + "\n"

    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": True,
        },
        stream=True,
    )

    for line in r.iter_lines():
        if line:
            data = json.loads(line.decode())
            if "response" in data:
                yield data["response"]


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ask_question(request):
    question = request.data.get("question")

    if not question:
        return Response({"error": "Question required"}, status=400)

    # Detect URL
    url_match = re.search(r"(https?://\S+)", question)

    if url_match:
        url = url_match.group(1)

        text = extract_text_from_url(url)
        chunks = chunk_text(text)

        temp_chunks = []

        for c in chunks[:20]:
            emb = model.encode(c)
            temp_chunks.append((emb, c))

        q_emb = model.encode(question)

        scored = []
        for e, c in temp_chunks:
            scored.append((cosine_similarity(q_emb, e), c))

        scored.sort(reverse=True)

        context = "\n".join([s[1] for s in scored[:4]])
        sources = [url]

    else:
        q_emb = model.encode(question)

        chunks = DocumentChunk.objects.filter(
            document__user=request.user
        ).exclude(embedding=None)

        if not chunks.exists():
            return Response({"error": "No documents uploaded"}, status=400)

        scored = []
        for c in chunks:
            scored.append((cosine_similarity(q_emb, np.array(c.embedding)), c))

        scored.sort(reverse=True)

        top = scored[:4]
        context = "\n".join([c[1].content for c in top])
        sources = list(set([c[1].document.title for c in top]))

    prompt = f"""
You are Synapse — a universal knowledge AI.

Answer ONLY from context.

Context:
{context}

Question:
{question}

Answer:
"""

    return StreamingHttpResponse(
        ollama_stream(prompt, sources),
        content_type="text/plain"
    )
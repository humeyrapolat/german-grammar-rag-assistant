"""Run the German Grammar RAG Assistant's pipeline directly from Python,
bypassing the n8n UI, against the question set in eval/questions.py.

WHY THIS BYPASSES N8N: the workflow's chat trigger only runs inside n8n
(cloud or self-hosted); there's no way to batch-run 34 questions through
the n8n chat UI by hand. This script re-implements the exact same request
shape the workflow's "Pinecone Vector Store2" -> "Code in JavaScript1" ->
"Basic LLM Chain" nodes build (same index, same top-k, same context
format, same system prompt — copied from workflow.json, not reworded) and
calls the same Pinecone index + Groq model directly. It does NOT touch or
modify the live n8n workflow or the Pinecone index's data.

### Before running

This needs three things this script cannot verify for you:

1. **The embedding model.** workflow.json leaves the "Embeddings Google
   Gemini" node's Model field on n8n's default, which isn't recorded in
   the exported JSON. Open that node in the n8n editor and read the exact
   Model value, then set GEMINI_EMBEDDING_MODEL to match — otherwise the
   query embedding won't live in the same vector space as the indexed
   book pages and every retrieval will be meaningless, even though nothing
   will visibly error. This script does one sanity check it CAN do
   automatically: it compares the embedding vector's length against the
   live Pinecone index's configured dimension and refuses to continue on
   a mismatch — but a same-dimension wrong model can still pass that
   check silently, so don't skip reading the node.

2. **Network access.** Needs to reach api.pinecone.io, generativelanguage
   googleapis.com, and api.groq.com. The sandbox this script was written
   in blocks all three (org egress policy) — run this on a machine with
   normal internet access.

3. **Dependencies**: pip install -r eval/requirements.txt

### Run

    export PINECONE_API_KEY=...
    export GOOGLE_API_KEY=...       # Gemini
    export GROQ_API_KEY=...
    python eval/run_eval.py

### What this does and does not grade

Automatically checked, for every answer:
- **Citation sanity**: for questions marked expect_citation, does the
  answer contain a "Quellen: Sayfa N" line, and is every cited page
  number within 1-80 (the book's indexed range per test-cases.md)? A
  citation pointing outside that range is a concrete, catchable error
  (exactly the kind of bug test-cases.md's debugging log already found
  once, with a stray "15" in a footer).
- **Refusal check**, for hallucination-category questions: does the
  answer contain a refusal-style phrase instead of a confident, specific
  answer?

NOT automatically graded: whether a non-refusal answer is factually
correct against the actual book page it cites. Nobody has the source PDF
loaded in this script to check that against, so — same as the original
test-cases.md — a human still needs to skim the "basic" and "synthesis"
category answers. This script automates the mechanical, catchable half of
the job (citation sanity + hallucination honesty across 34 questions
instead of 14 manual copy-pastes), not the half that needs a human who
knows the book.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.questions import QUESTIONS  # noqa: E402

INDEX_NAME = "german-notes"
TOP_K = 4
GROQ_MODEL = "openai/gpt-oss-20b"
INDEXED_PAGE_RANGE = (1, 80)

# Copied verbatim from workflow.json's "Basic LLM Chain" node.
SYSTEM_PROMPT = (
    "Du bist ein hilfreicher Deutschlehrer-Assistent. Antworte ausschließlich "
    "basierend auf dem gegebenen Kontext.  Der Kontext besteht aus mehreren "
    "Textabschnitten, die jeweils mit [Sayfa X] gekennzeichnet sind (X ist die "
    "Seitenzahl im Quellbuch). Wenn du für deine Antwort Informationen aus "
    "einem bestimmten Abschnitt verwendest, gib am Ende deiner Antwort an, "
    "welche Seiten du verwendet hast, im folgenden Format:  Quellen: Sayfa X, "
    "Sayfa Y  Wenn die Antwort nicht im gegebenen Kontext enthalten ist, sage "
    "das klar und erfinde keine Informationen.  Wichtig: Nicht jeder "
    "bereitgestellte Textabschnitt ist automatisch relevant für die gestellte "
    "Frage. Die Abschnitte wurden per Ähnlichkeitssuche ausgewählt und können "
    "auch thematisch nicht passende Treffer enthalten (z. B. zufällige "
    "Zahlen- oder Wortübereinstimmungen, etwa eine Seitenangabe oder "
    "Kapitelnummer in einer Fußzeile, die rein äußerlich zur Frage passt, "
    "inhaltlich aber nicht). Prüfe für jeden Abschnitt kritisch, ob er "
    "inhaltlich wirklich zur Frage passt, bevor du ihn verwendest. Wenn kein "
    "Abschnitt inhaltlich passt — auch wenn einzelne Wörter oder Zahlen "
    "zufällig übereinstimmen — sage klar, dass du dazu keine Information im "
    "Kontext findest.Du erhältst außerdem den Abschnitt \"Bisherige "
    "Konversation\" mit den vorangegangenen Fragen und Antworten dieser "
    "Unterhaltung. Nutze ihn, um zu verstehen, worauf sich die aktuelle Frage "
    "bezieht, besonders wenn sie unvollständig ist oder sich erkennbar auf "
    "ein vorheriges Thema bezieht (z. B. \"und was ist mit...\"). Die "
    "inhaltliche Antwort selbst darf aber ausschließlich auf dem Abschnitt "
    "\"Kontext\" basieren, nicht auf der Konversationshistorie — erfinde auch "
    "hier keine Informationen, die nicht im Kontext stehen."
)

USER_TEMPLATE = "Bisherige Konversation:\n{chat_history}\n\nFrage: {question}\n\nKontext:\n{context}"

REFUSAL_MARKERS = [
    "nicht im kontext",
    "nicht im gegebenen kontext",
    "keine information",
    "kann ich nicht",
    "weiß ich nicht",
    "nicht angegeben",
    "nicht enthalten",
    "finde ich dazu keine",
    "steht nicht im",
    "nicht bekannt",
]


def get_embedding(text: str, model: str):
    from google import genai

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    response = client.models.embed_content(model=model, contents=text)
    return response.embeddings[0].values


def _as_dict(obj):
    """Pinecone SDK responses are objects in some versions, plain dicts in
    others — normalize to a dict either way."""
    return obj.to_dict() if hasattr(obj, "to_dict") else obj


_warned_missing_text = False


def retrieve_chunks(pinecone_index, query_vector) -> list[dict]:
    global _warned_missing_text

    response = _as_dict(pinecone_index.query(vector=query_vector, top_k=TOP_K, include_metadata=True))
    chunks = []
    for match in response.get("matches", []):
        metadata = _as_dict(match).get("metadata", {})
        text = metadata.get("text", "")
        if not text and not _warned_missing_text:
            print(
                "WARNING: retrieved vector metadata has no non-empty 'text' field. "
                "n8n's Pinecone vector store node may store the chunk content under "
                "a different metadata key than assumed here — check one vector's "
                "metadata in the Pinecone console and adjust retrieve_chunks() if so.",
                file=sys.stderr,
            )
            _warned_missing_text = True
        chunks.append({"page": metadata.get("page"), "text": text})
    return chunks


def build_context(chunks: list[dict]) -> str:
    blocks = [f"[Sayfa {chunk['page']}]\n{chunk['text']}" for chunk in chunks]
    return "\n\n---\n\n".join(blocks)


def ask_groq(groq_client, question: str, context: str) -> str:
    user_message = USER_TEMPLATE.format(chat_history="", question=question, context=context)
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
    )
    return response.choices[0].message.content


def extract_cited_pages(answer: str) -> list[int]:
    import re

    match = re.search(r"Quellen:\s*(.+)", answer, re.IGNORECASE)
    if not match:
        return []
    return [int(n) for n in re.findall(r"\d+", match.group(1))]


def score_answer(item: dict, answer: str) -> dict:
    answer_lower = answer.lower()
    checks = {}

    if item["category"] == "hallucination":
        checks["refused"] = any(marker in answer_lower for marker in REFUSAL_MARKERS)

    if item.get("expect_citation"):
        cited_pages = extract_cited_pages(answer)
        checks["has_citation"] = len(cited_pages) > 0
        checks["citation_in_range"] = all(
            INDEXED_PAGE_RANGE[0] <= p <= INDEXED_PAGE_RANGE[1] for p in cited_pages
        ) if cited_pages else False

    return checks


def main() -> None:
    from groq import Groq
    from pinecone import Pinecone

    embedding_model = os.environ.get("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")

    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index = pc.Index(INDEX_NAME)
    groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

    stats = _as_dict(index.describe_index_stats())
    index_dimension = stats["dimension"]
    probe_vector = get_embedding("test", embedding_model)
    if len(probe_vector) != index_dimension:
        print(
            f"ABORTING: embedding model '{embedding_model}' produces "
            f"{len(probe_vector)}-dim vectors, but the '{INDEX_NAME}' index "
            f"expects {index_dimension}-dim vectors. Open the 'Embeddings "
            f"Google Gemini' node in n8n, read its exact Model value, and "
            f"set GEMINI_EMBEDDING_MODEL to match before re-running.",
            file=sys.stderr,
        )
        sys.exit(1)

    results = []
    category_totals: dict[str, list[dict]] = defaultdict(list)

    for item in QUESTIONS:
        question = item["question"]

        if not question.strip():
            # Mirror the workflow's own chat trigger: an empty/whitespace-only
            # message never reaches retrieval or the LLM.
            answer = "[no LLM call made: empty/whitespace-only input]"
            checks = {}
        else:
            query_vector = get_embedding(question, embedding_model)
            chunks = retrieve_chunks(index, query_vector)
            context = build_context(chunks)
            answer = ask_groq(groq_client, question, context)
            checks = score_answer(item, answer)

        record = {
            "id": item["id"],
            "category": item["category"],
            "question": question,
            "answer": answer,
            "checks": checks,
        }
        results.append(record)
        category_totals[item["category"]].append(record)

        status = "OK" if not checks or all(checks.values()) else "CHECK"
        print(f"[{status}] #{item['id']} ({item['category']}) {question[:60]!r}")

    summary = {
        "timestamp": datetime.now(UTC).isoformat(),
        "num_questions": len(results),
        "embedding_model_used": embedding_model,
        "pinecone_index": INDEX_NAME,
        "groq_model": GROQ_MODEL,
        "scoring_method": (
            "Automatic: citation-presence + cited-page-range sanity for "
            "expect_citation questions, refusal-phrase match for "
            "hallucination-category questions. Does NOT grade factual "
            "correctness of non-refusal answers against the source book — "
            "that still needs a human skim, same as test-cases.md originally "
            "required."
        ),
        "by_category": {
            category: len(items) for category, items in category_totals.items()
        },
        "results": results,
    }

    output_path = Path(__file__).resolve().parent / "results.json"
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWritten to {output_path}")


if __name__ == "__main__":
    main()

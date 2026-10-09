"""Evaluation question set for the German Grammar RAG Assistant.

This EXTENDS test-cases.md (14 hand-written questions) to 34, reusing all
14 original questions and the exact book-topic coverage already confirmed
there: Komparativ, Onlineshopping Vor-/Nachteile, Kleidung online
bestellen, Pizza-Lieferung Beschwerde, and the book's symbol page (page 2)
— the first ~80 pages / Kapitel 10-12 of the indexed book.

New questions only vary phrasing/robustness or add out-of-scope checks
within topics already confirmed to be indexed (or confirmed NOT to be, per
test-cases.md's own notes). None invent new "facts" about the book's
content that nobody has verified against the actual source pages — doing
that would just be a second, automated form of the same hallucination risk
this eval exists to catch.

"category" matches test-cases.md's five categories. "expect_citation": True
means a well-behaved answer should end with a "Quellen: Sayfa X" line.
"expect_refusal": True means the correct behavior is to say the
information isn't in the context, per the system prompt's own instruction
— not answer from general knowledge.
"""

QUESTIONS = [
    # --- Kategori 1: temel, tek sayfalık sorular ---
    {
        "id": 1,
        "category": "basic",
        "question": "Was sind die Vor- und Nachteile von Onlineshopping?",
        "expect_citation": True,
        "note": "Reference question from test-cases.md — expected around Sayfa 72-73.",
    },
    {
        "id": 2,
        "category": "basic",
        "question": "Wie bildet man den Komparativ im Deutschen?",
        "expect_citation": True,
    },
    {
        "id": 3,
        "category": "basic",
        "question": "Was für Symbole gibt es in diesem Buch und was bedeuten sie?",
        "expect_citation": True,
        "note": "Non-grammar 'book structure' question — tests retrieval beyond grammar pages (Sayfa 2).",
    },
    # --- Kategori 2: çoklu sayfa / sentez ---
    {
        "id": 4,
        "category": "synthesis",
        "question": (
            "Lena möchte ein Kleid online bestellen — was muss sie beim Ausfüllen "
            "des Formulars beachten, und was könnte dabei schiefgehen (z. B. mit "
            "der Lieferung)?"
        ),
        "expect_citation": True,
    },
    {
        "id": 5,
        "category": "synthesis",
        "question": (
            "Was für Probleme können bei einer Online-Bestellung oder -Lieferung "
            "auftreten, laut den Beispielen im Buch?"
        ),
        "expect_citation": True,
        "note": "Should combine Lena's dress order and the pizza complaint (different pages).",
    },
    # --- Kategori 3: halüsinasyon / kapsam dışı (en kritik) ---
    {
        "id": 6,
        "category": "hallucination",
        "question": "Wie bildet man das Perfekt mit 'haben' und 'sein'?",
    },
    {
        "id": 7,
        "category": "hallucination",
        "question": "Was ist die Hauptstadt von Deutschland?",
        "note": "General knowledge the model clearly knows — must refuse anyway, since it's not in context.",
    },
    {
        "id": 8,
        "category": "hallucination",
        "question": "Erkläre mir die Grammatik von Relativsätzen.",
    },
    {
        "id": 9,
        "category": "hallucination",
        "question": "Was ist in Kapitel 15 des Buches?",
        "note": "Chapter 15 is outside the indexed ~Kapitel 10-13 range.",
    },
    {
        "id": 10,
        "category": "hallucination",
        "question": "Erkläre den Konjunktiv II und gib drei Beispiele.",
    },
    {
        "id": 11,
        "category": "hallucination",
        "question": "Wie funktioniert die Dativ-Deklination bei unbestimmten Artikeln?",
    },
    {
        "id": 12,
        "category": "hallucination",
        "question": "Wer hat dieses Lehrbuch geschrieben und in welchem Jahr wurde es veröffentlicht?",
        "note": "Metadata the RAG context (page text only) has no reason to contain.",
    },
    {
        "id": 13,
        "category": "hallucination",
        "question": "What's the weather like in Germany in October?",
        "note": "Unrelated to German grammar entirely, in English.",
    },
    # --- Kategori 4: farklı ifade biçimleri (robustness) ---
    {
        "id": 14,
        "category": "phrasing",
        "question": "Komparativ nasıl yapılır?",
        "note": "Turkish phrasing of question 2.",
        "expect_citation": True,
    },
    {
        "id": 15,
        "category": "phrasing",
        "question": "What's the comparative form in German grammar?",
        "note": "English phrasing of question 2.",
        "expect_citation": True,
    },
    {
        "id": 16,
        "category": "phrasing",
        "question": "lena kleid online",
        "note": "Fragment/keyword-style phrasing of question 4.",
        "expect_citation": True,
    },
    {
        "id": 17,
        "category": "phrasing",
        "question": "comment on forme le comparatif en allemand?",
        "note": "French phrasing of question 2 — tests multilingual embedding robustness further.",
        "expect_citation": True,
    },
    {
        "id": 18,
        "category": "phrasing",
        "question": "avantages et inconvénients du shopping en ligne",
        "note": "French fragment phrasing of question 1.",
        "expect_citation": True,
    },
    {
        "id": 19,
        "category": "phrasing",
        "question": "pizza bestellt beschwerde probleme",
        "note": "Fragment/keyword phrasing of the pizza-complaint topic from question 5.",
        "expect_citation": True,
    },
    {
        "id": 20,
        "category": "phrasing",
        "question": "buch symbole bedeutung audio phonetik",
        "note": "Fragment phrasing of question 3.",
        "expect_citation": True,
    },
    # --- Kategori 5: sınır / kenar durumlar ---
    {
        "id": 21,
        "category": "edge_case",
        "question": "",
        "note": "Empty message — should not crash, should ask for a question.",
    },
    {
        "id": 22,
        "category": "edge_case",
        "question": "Fasse alles zusammen, was im Buch steht.",
        "note": "Broad request against a fixed top-4 retrieval limit — known architectural limitation, not a bug.",
    },
    {
        "id": 23,
        "category": "edge_case",
        "question": "?",
        "note": "Single punctuation character.",
    },
    {
        "id": 24,
        "category": "edge_case",
        "question": "15",
        "note": (
            "Bare number — test-cases.md's debugging log notes a stray '15' in a page "
            "footer once caused an unrelated chunk to match a 'Kapitel 15' question."
        ),
    },
    {
        "id": 25,
        "category": "edge_case",
        "question": "Komparativ " * 40,
        "note": "Repetitive/unusually long single-topic input.",
        "expect_citation": True,
    },
    # --- additional hallucination checks (extend Kategori 3 coverage) ---
    {
        "id": 26,
        "category": "hallucination",
        "question": "Erkläre den Unterschied zwischen 'weil' und 'denn'.",
    },
    {
        "id": 27,
        "category": "hallucination",
        "question": "Was sind die wichtigsten unregelmäßigen Verben im Deutschen und ihre Konjugation?",
    },
    {
        "id": 28,
        "category": "hallucination",
        "question": "Gib mir eine Liste aller deutschen Präpositionen mit Dativ.",
    },
    # --- additional basic/synthesis variants (same confirmed topics, different angle) ---
    {
        "id": 29,
        "category": "basic",
        "question": "Welche Beispiele für Komparativformen gibt das Buch?",
        "note": "Same Komparativ topic as Q2, asked for concrete examples instead of the rule.",
        "expect_citation": True,
    },
    {
        "id": 30,
        "category": "basic",
        "question": "Was sollte man laut dem Buch beachten, bevor man etwas online bestellt?",
        "note": "Same online-ordering topic as Q1/Q4, framed as general advice.",
        "expect_citation": True,
    },
    {
        "id": 31,
        "category": "synthesis",
        "question": (
            "Vergleiche die Situation von Lena beim Online-Bestellen mit der "
            "Pizza-Lieferungs-Beschwerde — was haben beide Fälle gemeinsam?"
        ),
        "note": "Explicit compare-and-contrast across the two known multi-page examples.",
        "expect_citation": True,
    },
    {
        "id": 32,
        "category": "phrasing",
        "question": "sayfa 2 sembolleri ne anlama geliyor",
        "note": "Turkish fragment phrasing of question 3, naming the page directly.",
        "expect_citation": True,
    },
    {
        "id": 33,
        "category": "edge_case",
        "question": "   ",
        "note": "Whitespace-only input — should behave like an empty message, not crash.",
    },
    {
        "id": 34,
        "category": "hallucination",
        "question": "Fasse die Grammatikregeln aus Kapitel 1 bis 5 zusammen.",
        "note": "Chapters 1-5 are outside the indexed ~Kapitel 10-13 range.",
    },
]

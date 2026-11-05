from app.rag.rerank import query_terms, relevance, rerank


def test_rare_and_unknown_words_weigh_more_and_noise_is_ignored():
    terms = {t: w for t, w, _ in query_terms("What happens to MIT students below 75 percent attendance at biryani?")}
    assert "mit" not in terms and "happen" not in terms and "below" not in terms
    assert terms["biryani"] > terms["attendance"] > 0  # a word the corpus never uses weighs most


def test_relevance_counts_synonyms_and_is_absolute():
    terms = query_terms("when is the cultural fest")
    assert relevance(terms, {"text": "REVELS: 2027-02-17 to 2027-02-20"}) == 1.0  # "cultural fest" -> REVELS
    assert relevance(terms, {"text": "Hostel mess timings"}) == 0.0


def test_rerank_puts_the_passage_that_covers_the_question_first():
    matches = [
        {"id": "a", "text": "Placement drives and company tests.", "score": 1.0},
        {"id": "b", "text": "A student with less than 75% attendance is detained from the end semester exam.", "score": 0.6},
    ]
    ranked = rerank("minimum attendance for end semester exam", matches)
    assert ranked[0]["id"] == "b" and ranked[0]["relevance"] > ranked[1]["relevance"]

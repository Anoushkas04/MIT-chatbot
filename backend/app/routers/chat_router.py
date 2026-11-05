import datetime
import re
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.answer_verifier import verify_answer
from app.community_knowledge import search_dataset_posts
from app.faculty_directory import lookup_faculty
from app.citations import select_citations
from app.conversational import small_talk_reply
from app.followups import split_model_followups, suggest
from app.multilingual import LOW_CONFIDENCE, NO_INFO, answer_language, search_query
from app.rag.entities import extract as extract_entities
from app.rag.rerank import best_relevance, rerank
from app.rag.spelling import correct_query
from app.structured_lookup import calendar_evidence, club_evidence
from app.prompts import build_system_prompt
from app.providers import GenerationRequest, GenerationResult, generate_answer
from app.rag.hybrid import hybrid_search
from app.routers.auth_router import get_current_user
from app.schemas import ChatRequest, ChatResponse, CitationDetail
from app.session_memory import add_turn, get_history, restore as restore_history
from app.database import SessionLocal
from app import models

router = APIRouter(prefix="/api/chat", tags=["2. AI Copilot & RAG Retrieval"])

COMMON_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him",
    "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't",
    "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some",
    "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've",
    "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who",
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll",
    "you're", "you've", "your", "yours", "yourself", "yourselves", "tell", "show", "give", "list", "please",
    "available", "right", "now", "official", "mit", "manipal", "mahe", "campus", "university",
    "institution", "institutional", "policy", "information", "details"
}

ACADEMIC_KEYWORDS = {
    "branch", "branches", "program", "programs", "course", "courses", "curriculum", "syllabus",
    "admission", "admissions", "eligibility", "regulation", "regulations", "fee", "fees",
    "department", "departments", "faculty", "hod", "professor", "cabin", "exam", "exams",
    "examination", "result", "results", "attendance", "mlc", "sgpa", "cgpa", "credit", "credits",
    "guidelines", "sop", "placement", "placements", "internship", "cutoff", "cutoffs", "rank", "ranks"
}

COMMUNITY_KEYWORDS = {
    "mess", "food", "hostel", "room", "canteen", "revels", "techtatva", "club", "clubs",
    "xerox", "printing", "leave", "outing", "auto", "fare", "closest", "near", "vibe", "opinion", "better"
}


def classify_intent(query: str) -> str:
    """Classifies query intent into 'academic_official' vs 'community_experience'."""
    words = set(re.findall(r'\b\w+\b', query.lower()))
    academic_matches = words.intersection(ACADEMIC_KEYWORDS)
    community_matches = words.intersection(COMMUNITY_KEYWORDS)

    if academic_matches and not community_matches:
        return "academic_official"
    elif community_matches and not academic_matches:
        return "community_experience"
    elif len(academic_matches) >= len(community_matches):
        return "academic_official"
    else:
        return "community_experience"


def detect_query_type(query: str) -> str:
    """Categorizes user query complexity:

    'simple_factual' | 'procedural' | 'comparison' | 'explanation' | 'complex_research'
    """
    q = query.lower()
    if any(w in q for w in ["how to", "steps", "procedure", "process", "apply for", "guidelines to"]):
        return "procedural"
    elif any(w in q for w in ["compare", "vs", "versus", "difference between", "better than"]):
        return "comparison"
    elif any(w in q for w in ["why", "explain", "describe", "reason for"]):
        return "explanation"
    elif any(w in q for w in ["branches", "branch", "hod", "fee", "fees", "when do", "who is", "cutoff", "cutoffs", "rank", "where is"]):
        return "simple_factual"
    elif len(q.split()) > 14:
        return "complex_research"
    else:
        return "simple_factual"


def extract_query_features(query: str, intent: str, query_type: str, confidence: str, source_type: str) -> dict:
    """Extracts structured features and internal sentiment from interaction telemetry."""
    q = query.lower()

    # Sentiment (VADER polarity plus urgency/confusion/frustration cues, app/sentiment.py)
    from app.sentiment import classify as classify_sentiment

    sentiment = classify_sentiment(query)

    # Topic classification
    if any(w in q for w in ["mess", "food", "hostel", "room", "canteen"]):
        topic = "Hostel & Mess"
    elif any(w in q for w in ["fee", "tuition", "payment", "scholarship", "cost"]):
        topic = "Fees & Finance"
    elif any(w in q for w in ["branch", "branches", "course", "syllabus", "exam", "grade", "attendance"]):
        topic = "Academics"
    elif any(w in q for w in ["admission", "cutoff", "rank", "counseling", "seat"]):
        topic = "Admissions"
    elif any(w in q for w in ["placement", "company", "package", "internship", "recruiter"]):
        topic = "Placements"
    else:
        topic = "General Campus Operations"

    return {
        "topic": topic,
        "sentiment": sentiment,
        "intent": intent,
        "query_type": query_type,
        "confidence": confidence,
        "source_type": source_type,
    }


def filter_chunk_relevance(vector_matches: list, query: str, query_type: str, limit: int = 4) -> list:
    """Relevance Filtering: Filters out raw bibliography lines, unrelated faculty directories,

    and handbook fluff, retaining only chunks containing entities relevant to the query.
    """
    if not vector_matches:
        return []

    q = query.lower()
    words = [w for w in re.findall(r'\b\w+\b', q) if len(w) >= 3 and w not in COMMON_STOPWORDS]

    if not words:
        return vector_matches[:3]

    filtered = []
    for m in vector_matches:
        text = " ".join(str(value) for value in (
            m.get("source", ""),
            m.get("department_code", ""),
            m.get("department", ""),
            m.get("academic_year", ""),
            m.get("retrieval_text", ""),
            m.get("text", ""),
        )).lower()
        score = float(m.get("score", 0.0))

        # Check keyword/entity match count
        match_count = sum(1 for w in words if w in text)

        # Exclude raw bibliography or handbook reference chunk dumps if query isn't about books
        if "references:" in text or "isbn" in text or "publisher" in text:
            if not any(b in q for b in ["book", "author", "textbook", "reference"]):
                score *= 0.5

        if match_count >= 1:
            m_copy = dict(m)
            m_copy["score"] = min(1.0, score + (match_count * 0.05))
            filtered.append(m_copy)

    filtered.sort(key=lambda x: x["score"], reverse=True)
    return filtered[:limit]


def merge_evidence(
    official_matches: list[dict],
    community_matches: list[dict],
    *,
    prefer_community: bool,
    limit: int = 4,
    structured: list[dict] | None = None,
) -> list[dict]:
    """Keep both knowledge partitions represented without crowding out sources.

    Structured evidence (calendar entries, club records) goes first; document passages
    still follow it so the answer can add context.
    """
    if structured:
        rest = merge_evidence(official_matches, community_matches, prefer_community=prefer_community, limit=limit)
        keys = {m.get("id") for m in structured}
        return structured + [m for m in rest if m.get("id") not in keys][: max(2, limit - len(structured))]
    if official_matches and community_matches:
        if prefer_community:
            merged = community_matches[:2] + official_matches[:2]
        else:
            merged = official_matches[:3] + community_matches[:1]
    else:
        merged = official_matches or community_matches
    return merged[:limit]


# Re-ranking (app/rag/rerank.py): candidates fetched, and the coverage thresholds. Chosen on a
# calibration set kept apart from the evaluation (rag_queries.jsonl as answerable,
# dev_unanswerable.jsonl): answerable questions' best passage covered >= 0.47 of the question,
# unanswerable ones <= 0.40.
RERANK_CANDIDATES = 10
NO_ANSWER_BELOW = 0.30
LOW_CONFIDENCE_BELOW = 0.44

# Who the answer is written for (prompts.ROLE_PERSONAS). Any student can ask on behalf of a
# parent or a prospective student; the faculty persona is for faculty accounts.
OPEN_PERSONAS = {"student", "parent", "prospective"}


def _persona(requested: str, me: models.User) -> str:
    if requested in OPEN_PERSONAS or (requested == "faculty" and me.role == "faculty"):
        return requested
    return "student"


def _stored_history(db, session_id: str) -> list[dict]:
    """The conversation's recent turns from the database, put back into memory."""
    from app.config import MAX_HISTORY_TURNS

    rows = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.id.desc())
        .limit(MAX_HISTORY_TURNS * 2)
        .all()
    )
    turns = [{"role": "user" if r.sender_role == "user" else "model", "text": r.text} for r in reversed(rows)]
    return restore_history(session_id, turns) if turns else []


def _save_exchange(db, me, req, persona, reply_text, confidence, confidence_type, citations) -> int | None:
    """Store the question and answer; returns the answer's id (sent back with a 👍/👎)."""
    message_id = None
    try:
        session_rec = db.query(models.ChatSession).filter(models.ChatSession.id == req.session_id).first()
        if not session_rec:
            session_rec = models.ChatSession(id=req.session_id, user_id=me.id, role=persona, title=req.message[:40])
            db.add(session_rec)
        elif session_rec.user_id is None:
            session_rec.user_id = me.id
        session_rec.updated_at = datetime.datetime.utcnow()  # drives "active this week" on Monitoring
        db.commit()

        msg_user = models.ChatMessage(
            session_id=req.session_id,
            sender_role="user",
            text=req.message,
            timestamp="Just now",
        )
        db.add(msg_user)
        db.commit()

        msg_ai = models.ChatMessage(
            session_id=req.session_id,
            sender_role="assistant",
            text=reply_text,
            confidence=confidence,
            confidence_type=confidence_type,
            timestamp="Just now",
        )
        db.add(msg_ai)
        db.flush()
        message_id = msg_ai.id
        for citation in citations:
            page_suffix = f"#page={citation.page_number}" if citation.page_number else ""
            db.add(models.MessageCitation(
                message_id=msg_ai.id,
                source_name=f"{citation.source}{page_suffix}",
                snippet=citation.snippet,
                similarity_score=citation.score,
            ))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning DB chat save error: {e}")

    return message_id


def _safely(lookup, query: str):
    """A structured lookup is an extra; if it fails, answer from document search instead."""
    try:
        return lookup(query)
    except Exception as exc:
        print(f"{lookup.__name__} failed: {exc}")
        return None


def _citation(index: int, m: dict, src: str, faculty_lookup: dict | None) -> CitationDetail:
    """One citation per evidence item ([E<index>]), with where clicking it should go."""
    text = m.get("text", "")
    kind, url, title = m.get("kind"), m.get("url"), m.get("source") or src
    if faculty_lookup:
        kind = "faculty"
        people = faculty_lookup.get("records") or []
        target = people[0]["name"] if faculty_lookup.get("kind") == "person" and people else (people[0]["dept"] if people else "")
        url = f"/utilities?section=professors&q={quote(target)}"
        title = "MIT faculty directory"
    elif str(m.get("source_type", "")).startswith("community"):
        kind = "community"
        url = f"/community?q={quote(m.get('post_title') or '')}"
    elif not kind:
        kind = "document"
    if kind == "calendar":
        title = "Academic Calendar 2026-27"
    elif kind == "document" and str(src).lower().endswith((".pdf", ".docx", ".csv", ".md", ".txt")):
        title = re.sub(r"\s+", " ", re.sub(r"\.(pdf|docx|csv|md|txt)$", "", str(src), flags=re.I).replace("_", " ")).strip()
    return CitationDetail(
        index=index,
        source=src,
        title=title,
        kind=kind,
        snippet=text[:280] + ("..." if len(text) > 280 else ""),
        score=round(float(m.get("score", 0.0)), 3),
        document_id=m.get("document_id"),
        page_number=m.get("page_number"),
        retrieval_method=m.get("retrieval_method"),
        # A web page (club) or an in-app page; documents open from source + page_number
        source_url=url,
    )


@router.post("", response_model=ChatResponse, summary="Query the configured AI provider with RAG grounding")
def chat_query(req: ChatRequest, me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        # Conversations belong to one account: another user's session id can't be appended to.
        if not req.session_id or len(req.session_id) > 64:
            raise HTTPException(status_code=400, detail="Invalid conversation id.")
        owner = db.query(models.ChatSession.user_id).filter(models.ChatSession.id == req.session_id).scalar()
        if owner is not None and owner != me.id:
            raise HTTPException(status_code=403, detail="That conversation belongs to someone else.")

        # Documents are in English: Hindi/Kannada questions are searched in translation
        language = answer_language(req.language, req.message)
        persona = _persona(req.role, me)

        # Greetings, thanks and the like need no documents: no retrieval, no sources
        small_talk = small_talk_reply(req.message, language)
        if small_talk:
            add_turn(req.session_id, req.message, small_talk)
            return ChatResponse(
                text=small_talk,
                sources=[],
                citations=[],
                confidence="conversational",
                confidence_type="conversational",
                provider="local",
                model="small-talk",
                message_id=_save_exchange(db, me, req, persona, small_talk, "conversational", "conversational", []),
            )
        # In-memory history is lost when the server restarts or sleeps; the messages are in the database
        history = get_history(req.session_id) or _stored_history(db, req.session_id)
        query = search_query(req.message, language, history)
        query = _safely(correct_query, query) or query  # misspellings match nothing in the documents
        intent = classify_intent(query)
        query_type = detect_query_type(query)
        entities = extract_entities(query)
        # "List subjects in BTech CSE" is a curriculum question, not a request for the CSE professors
        faculty_lookup = None if "curriculum" in entities.intents and "person" not in entities.intents else _safely(lookup_faculty, query)
        structured = [] if faculty_lookup else (_safely(calendar_evidence, query) or []) + (_safely(club_evidence, query) or [])

        # 1. Hybrid search over dense, BM25, and optional ColPali-style page vectors.
        if faculty_lookup:
            vector_matches = [faculty_lookup["evidence"]]
        else:
            try:
                # A department named in the question replaces the profile's (a CSE student asking about
                # Mech gets Mech pages), but doesn't add a department boost the search didn't have:
                # that would lift every page of the department above the one that answers.
                vector_matches = hybrid_search(
                    query,
                    department=(entities.department or req.department) if req.department else None,
                    academic_year=entities.academic_year or req.academic_year,
                    semester=req.semester,
                    entities=entities,
                    final_k=RERANK_CANDIDATES,
                )
            except Exception as e:
                print("Vector search error:", e)
                vector_matches = []

        # Filter & Rerank Vector Matches
        relevance_query = " ".join(
            value for value in (
                query,
                req.department,
                req.academic_year,
                req.semester,
            )
            if value
        )
        relevant_official_matches = (
            vector_matches
            if faculty_lookup
            else rerank(query, filter_chunk_relevance(vector_matches, relevance_query, query_type, limit=RERANK_CANDIDATES))[:4]
        )
        # How much of the question the best passage covers (absolute, unlike the fused rank
        # scores). Structured lookups are exact matches, so they're exempt.
        coverage = None
        if not faculty_lookup and not structured:
            coverage = best_relevance(query, relevant_official_matches)
            if coverage < NO_ANSWER_BELOW:
                relevant_official_matches = []  # nothing in the documents answers this

        # 2. Database search for Community Q&A — only admin-verified, high-upvote posts
        # that have actually been promoted into the dataset (app/community_knowledge.py).
        community_matches = [] if faculty_lookup else search_dataset_posts(query, db, limit=4)
        relevant_community_matches = [cm for cm in community_matches if cm["score"] >= 0.50]

        # Calculate live community counts dynamically from DB
        question_count = len(relevant_community_matches)
        response_count = 0
        for cm in relevant_community_matches:
            text_str = cm.get("text", "")
            if "Answers:" in text_str:
                replies_part = text_str.split("Answers:")[1]
                response_count += len([line for line in replies_part.split("\n") if line.strip().startswith("•")])

        demand_count = question_count
        sample_size = response_count

        # 3. Intent-Aware Source Prioritization
        has_community_query_signal = any(w in query.lower() for w in ["student", "students", "reddit", "say", "saying", "opinion", "review", "recommend", "advice", "peer", "experience", "best", "quietest", "fastest", "review"])
        all_matches = merge_evidence(
            relevant_official_matches,
            relevant_community_matches,
            prefer_community=(
                has_community_query_signal
                or intent == "community_experience"
            ),
            structured=structured,
        )

        # Evaluate Confidence
        from app.hallucination_guard import evaluate_confidence
        confidence, confidence_type, fallback_suffix = evaluate_confidence(all_matches)
        if coverage is not None and coverage < LOW_CONFIDENCE_BELOW and all_matches and confidence in ("high", "medium"):
            confidence, fallback_suffix = "low", LOW_CONFIDENCE["en"]  # weak match: answer with the warning

        # Feature & Internal Sentiment Extraction (Requirement 10 & 11)
        source_type_primary = all_matches[0].get("source_type", "official") if all_matches else "none"
        features = extract_query_features(query, intent, query_type, confidence, source_type_primary)

        # Log query features to SQLite analytics table
        try:
            analytics_log = models.QueryAnalyticsLog(
                query_text=req.message,
                topic=features["topic"],
                intent=intent,
                query_type=query_type,
                sentiment=features["sentiment"],
                confidence=confidence,
                source_type=source_type_primary,
            )
            db.add(analytics_log)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Warning analytics log error: {e}")

        # Active Learning & Knowledge Gap Pipeline (Requirement 8 & 9)
        if confidence in ["low", "no_evidence"] or features["sentiment"] in ["Frustrated", "Urgent"]:
            try:
                clean_q = req.message.strip()
                existing_gap = db.query(models.KnowledgeGap).filter(models.KnowledgeGap.query_text == clean_q).first()
                if existing_gap:
                    existing_gap.frequency += 1
                else:
                    new_gap = models.KnowledgeGap(
                        query_text=clean_q,
                        topic=features["topic"],
                        category=features["topic"],
                        frequency=1,
                        avg_confidence=0.45 if confidence == "low" else 0.10,
                        community_answers_count=question_count,
                        has_official_source=bool(relevant_official_matches),
                        status="unresolved",
                    )
                    db.add(new_gap)
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Warning knowledge gap log error: {e}")

        # Debug Logging
        print("==================================================")
        print(f"QUERY: \"{req.message}\"")
        print(f"INTENT: {intent} | QUERY TYPE: {query_type} | SENTIMENT: {features['sentiment']}")
        print(f"TOPIC: {features['topic']} | CONFIDENCE: {confidence}")
        print(f"MATCHES PASSED TO PROMPT: {len(all_matches)}")
        print("==================================================")

        system_prompt = build_system_prompt(
            role=persona,
            language=language,
            context_chunks=all_matches,
            department=req.department,
            academic_year=req.academic_year,
            semester=req.semester,
            query_type=query_type,
        )

        # The directory's fixed answer is English; other languages go through the model
        if not all_matches:
            # Nothing to answer from: don't spend a model call
            generation = GenerationResult(text=NO_INFO[language], provider="local", model="no-evidence")
        elif faculty_lookup and language == "en":
            generation = GenerationResult(
                text=faculty_lookup["answer"],
                provider="local",
                model="structured-faculty-directory-v1",
            )
        else:
            generation = generate_answer(GenerationRequest(
                question=req.message if query == req.message else f"{req.message}\n(The documents were searched for: {query})",
                system_prompt=system_prompt,
                evidence=all_matches,
                history=history,
            ))
        answer_text, model_followups = split_model_followups(generation.text)
        reply_text, verification_warnings = verify_answer(answer_text, all_matches)

        # Only passages the answer actually relies on become sources (app/citations.py):
        # unsupported or off-topic markers are dropped and the rest renumbered.
        reply_text, cited = select_citations(reply_text, all_matches, query)
        citations, sources = [], []
        for index, m in cited:
            src = m.get("source_file") or m.get("source") or "Institutional Knowledge Base"
            if src not in sources:
                sources.append(src)
            citations.append(_citation(index, m, src, faculty_lookup))

        if not all_matches:
            reply_text = NO_INFO[language]
            citations = []
            sources = []
        elif fallback_suffix:
            reply_text += LOW_CONFIDENCE[language]

        # Checked against the same evidence, so each one can be answered (app/followups.py)
        cited_evidence = [m for _, m in cited]
        followups = [] if not cited_evidence else (_safely(lambda q: suggest(q, cited_evidence, model_followups, faculty_lookup), query) or [])
        add_turn(req.session_id, req.message, reply_text)

        message_id = _save_exchange(db, me, req, persona, reply_text, confidence, confidence_type, citations)

        return ChatResponse(
            text=reply_text,
            sources=sources,
            citations=citations,
            confidence=confidence,
            confidence_type=confidence_type,
            followups=followups,
            question_count=question_count,
            response_count=response_count,
            demand_count=demand_count,
            sample_size=sample_size,
            provider=generation.provider,
            model=generation.model,
            verification_warnings=verification_warnings,
            # Shown under the answer when the search differed from what was typed
            message_id=message_id,
            searched_for=None if " ".join(query.lower().split()) == " ".join(req.message.lower().split()) else query,
        )
    except HTTPException:
        raise  # deliberate errors (e.g. 403 for someone else's conversation) keep their status
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Something went wrong answering that. Please try again.")
    finally:
        db.close()


class AnswerFeedback(BaseModel):
    message_id: int
    rating: int = Field(ge=-1, le=1)  # 1 helpful, -1 not helpful, 0 clears it


@router.post("/feedback", summary="Rate an answer helpful (1) or not (-1), or clear the rating (0)")
def answer_feedback(req: AnswerFeedback, me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        message = (
            db.query(models.ChatMessage)
            .join(models.ChatSession, models.ChatSession.id == models.ChatMessage.session_id)
            .filter(
                models.ChatMessage.id == req.message_id,
                models.ChatMessage.sender_role == "assistant",
                models.ChatSession.user_id == me.id,  # only your own answers
            )
            .first()
        )
        if not message:
            raise HTTPException(status_code=404, detail="That answer wasn't found.")
        message.rating = req.rating or None
        message.rated_at = datetime.datetime.utcnow() if req.rating else None
        db.commit()
        return {"status": "saved", "rating": message.rating}
    finally:
        db.close()

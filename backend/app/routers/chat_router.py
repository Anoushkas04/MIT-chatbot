import re
from urllib.parse import quote
from fastapi import APIRouter, HTTPException
from app.answer_verifier import verify_answer
from app.prompts import build_system_prompt
from app.providers import GenerationRequest, generate_answer
from app.rag.hybrid import hybrid_search
from app.schemas import ChatRequest, ChatResponse, CitationDetail
from app.session_memory import add_turn, get_history
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


def search_community_posts(user_query: str, db) -> list:
    """Searches student community posts with flexible keyword overlap & category matching."""
    words = [w.lower() for w in re.findall(r'\b\w+\b', user_query) if len(w) >= 3 and w.lower() not in COMMON_STOPWORDS]

    if not words:
        return []

    results = []
    posts = db.query(models.StudentPost).order_by(models.StudentPost.id.desc()).limit(100).all()

    for p in posts:
        post_text = f"{p.title} {p.content} {p.sub_community} {p.tag}".lower()
        comments_text = " ".join([c.content.lower() for c in p.comments]) if p.comments else ""
        full_text = f"{post_text} {comments_text}"

        matched_words = [w for w in words if w in full_text]
        matches_count = len(matched_words)

        if matches_count >= 1:
            score = round(min(0.98, 0.75 + (matches_count * 0.08)), 2)

            comment_str = ""
            if p.comments:
                comment_str = "\nCommunity Answers:\n" + "\n".join(
                    [f" • {c.author_name} ({'★ Accepted Answer' if c.is_helpful else 'Reply'}): \"{c.content}\"" for c in p.comments]
                )

            results.append({
                "source": f"Student Community Discussion: '{p.title.strip()}'",
                "source_type": "community",
                "text": f"Community Question by {p.author_name} ({p.sub_community}): \"{p.title.strip()}\"\nQuestion Context: {p.content}{comment_str}",
                "score": score,
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:3]


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

    # Sentiment analysis (internal intelligence layer)
    if any(w in q for w in ["frustrated", "broken", "nobody is helping", "terrible", "stuck", "3 days", "useless"]):
        sentiment = "Frustrated"
    elif any(w in q for w in ["urgent", "emergency", "asap", "deadline today", "immediately"]):
        sentiment = "Urgent"
    elif any(w in q for w in ["confused", "don't understand", "unclear", "doubt", "why is it"]):
        sentiment = "Confused"
    elif any(w in q for w in ["bad", "worst", "poor", "hate", "unhelpful"]):
        sentiment = "Negative"
    elif any(w in q for w in ["thanks", "thank you", "great", "helpful", "good", "awesome"]):
        sentiment = "Positive"
    else:
        sentiment = "Neutral"

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


def filter_chunk_relevance(vector_matches: list, query: str, query_type: str) -> list:
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
        text = f"{m.get('source', '')} {m.get('text', '')}".lower()
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
    return filtered[:4]


@router.post("", response_model=ChatResponse, summary="Query the configured AI provider with RAG grounding")
def chat_query(req: ChatRequest):
    db = SessionLocal()
    try:
        intent = classify_intent(req.message)
        query_type = detect_query_type(req.message)

        # 1. Hybrid search over dense, BM25, and optional ColPali-style page vectors.
        try:
            vector_matches = hybrid_search(req.message)
        except Exception as e:
            print("Vector search error:", e)
            vector_matches = []

        # Filter & Rerank Vector Matches
        relevant_official_matches = filter_chunk_relevance(vector_matches, req.message, query_type)

        # 2. Database Search for Community Discussions
        community_matches = search_community_posts(req.message, db)
        relevant_community_matches = [cm for cm in community_matches if cm["score"] >= 0.50]

        # Calculate live community counts dynamically from DB
        question_count = len(relevant_community_matches)
        response_count = 0
        for cm in relevant_community_matches:
            text_str = cm.get("text", "")
            if "Community Answers:" in text_str:
                replies_part = text_str.split("Community Answers:")[1]
                response_count += len([line for line in replies_part.split("\n") if line.strip().startswith("•")])

        demand_count = question_count
        sample_size = response_count

        # 3. Intent-Aware Source Prioritization
        has_community_query_signal = any(w in req.message.lower() for w in ["student", "students", "reddit", "say", "saying", "opinion", "review", "recommend", "advice", "peer", "experience", "best", "quietest", "fastest", "review"])
        if relevant_community_matches and (has_community_query_signal or intent == "community_experience"):
            all_matches = relevant_community_matches + relevant_official_matches
        elif intent == "academic_official":
            all_matches = relevant_official_matches + relevant_community_matches
        else:
            all_matches = relevant_community_matches + relevant_official_matches

        all_matches = all_matches[:4]

        # Evaluate Confidence
        from app.hallucination_guard import evaluate_confidence
        confidence, confidence_type, fallback_suffix = evaluate_confidence(all_matches)

        # Feature & Internal Sentiment Extraction (Requirement 10 & 11)
        source_type_primary = all_matches[0].get("source_type", "official") if all_matches else "none"
        features = extract_query_features(req.message, intent, query_type, confidence, source_type_primary)

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
            role=req.role,
            language=req.language,
            context_chunks=all_matches,
            department=req.department,
            academic_year=req.academic_year,
            semester=req.semester,
            query_type=query_type,
        )

        history = get_history(req.session_id)
        generation = generate_answer(GenerationRequest(
            question=req.message,
            system_prompt=system_prompt,
            evidence=all_matches,
            history=history,
        ))
        reply_text, verification_warnings = verify_answer(generation.text, all_matches)

        citations = []
        sources = []
        for m in all_matches:
            src = m.get("source", "Institutional Knowledge Base")
            if src not in sources:
                sources.append(src)
            citations.append(
                CitationDetail(
                    source=src,
                    snippet=m.get("text", "")[:280] + ("..." if len(m.get("text", "")) > 280 else ""),
                    score=round(float(m.get("score", 0.0)), 3),
                    document_id=m.get("document_id"),
                    page_number=m.get("page_number"),
                    retrieval_method=m.get("retrieval_method"),
                    source_url=(
                        f"/api/search/page/{quote(str(m['document_id']))}/{int(m['page_number'])}"
                        if m.get("document_id") and m.get("page_number")
                        else None
                    ),
                )
            )

        if not all_matches:
            reply_text = "I couldn't find reliable information about that in the MIT CampusOS official knowledge base."
            citations = []
            sources = []
        elif fallback_suffix:
            reply_text += fallback_suffix

        # Follow-up suggestions are intentionally empty until they can be generated
        # and verified against the same evidence set.
        followups = []
        add_turn(req.session_id, req.message, reply_text)

        # Save session & message to SQLite DB
        try:
            session_rec = db.query(models.ChatSession).filter(models.ChatSession.id == req.session_id).first()
            if not session_rec:
                session_rec = models.ChatSession(id=req.session_id, role=req.role, title=req.message[:40])
                db.add(session_rec)
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
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

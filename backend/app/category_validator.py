from typing import Tuple

CATEGORY_TOPIC_KEYWORDS = {
    "mess": ["mess", "food", "canteen", "dinner", "lunch", "breakfast", "paneer", "dosa", "thali", "food court", "fc-1", "fc-2", "eat", "meal", "paratha", "tea", "coffee"],
    "hostels": ["hostel", "room", "warden", "block", "leave form", "outstation", "gate pass", "curfew", "bed", "ac", "laundry", "clinic", "clean"],
    "academics": ["exam", "registration", "mid-sem", "end-sem", "marks", "grade", "cgpa", "course", "syllabus", "viva", "lab", "professor", "lecture", "assignment", "study", "library", "quiz", "test", "elective", "dsa", "operating systems"],
    "resources": ["print", "xerox", "pdf", "scan", "paper", "manual", "lab manual", "printer", "book", "library book", "soft copy"],
    "transportation": ["auto", "bus", "fare", "udupi", "station", "train", "taxi", "rickshaw", "tiger circle", "travel", "auto fare"],
    "lost & found": ["lost", "found", "airpods", "wallet", "key", "id card", "umbrella", "bag", "phone", "card"],
    "placements": ["placement", "interview", "company", "dsa", "resume", "package", "salary", "internship", "microsoft", "amazon", "tata"],
    "clubs": ["club", "techtatva", "revels", "workshop", "event", "society", "ieee", "acm", "project"],
    "events": ["fest", "revels", "techtatva", "concert", "dj", "cultural", "hackathon"],
}


def validate_post_category(title: str, content: str, category: str) -> Tuple[bool, str, float]:
    """Category Mismatch Validation Engine

    Evaluates semantic relationship between selected category and post title/content.
    Returns (is_valid, message, confidence_score).

    Thresholds:
    - High confidence mismatch (>= 0.80) -> REJECT
    - Ambiguous / Uncertain (0.30 - 0.79) -> ALLOW
    - Good match (< 0.30 mismatch) -> ALLOW
    """
    if not title or not title.strip():
        return False, "Title cannot be empty.", 1.0

    if not content or not content.strip():
        return False, "Content description cannot be empty.", 1.0

    cat_norm = category.lower().strip()
    
    # 1. 'General' and 'All' categories are open umbrella categories
    if cat_norm in ["general", "all", "advice", "campus life"]:
        return True, "General category allowed.", 0.0

    text_combined = f"{title} {content}".lower()

    # 2. Check keywords for selected category
    target_keywords = []
    for key, kw_list in CATEGORY_TOPIC_KEYWORDS.items():
        if key in cat_norm or cat_norm in key:
            target_keywords.extend(kw_list)

    has_target_keyword = any(kw in text_combined for kw in target_keywords)

    # 3. Check if text strongly belongs to another distinct category
    strong_other_category = None
    max_other_matches = 0

    for other_cat, kw_list in CATEGORY_TOPIC_KEYWORDS.items():
        if other_cat in cat_norm or cat_norm in other_cat:
            continue
        
        matches = sum(1 for kw in kw_list if kw in text_combined)
        if matches >= 2 and matches > max_other_matches:
            max_other_matches = matches
            strong_other_category = other_cat

    # 4. Evaluate Mismatch Confidence
    if not has_target_keyword and strong_other_category and max_other_matches >= 2:
        # High confidence mismatch
        suggested = strong_other_category.capitalize()
        if "academic" in strong_other_category:
            suggested = "Academics"
        elif "mess" in strong_other_category:
            suggested = "Mess & Food"
        elif "resource" in strong_other_category:
            suggested = "Facilities & Printing"
        
        msg = f"The question appears to be about '{suggested}' rather than '{category}'."
        return False, msg, 0.90

    # 5. Ambiguous or matching cases are allowed
    return True, "Valid category match.", 0.10

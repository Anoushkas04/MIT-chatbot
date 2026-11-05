"""Small talk that doesn't need the documents: greetings, thanks, "how are you", goodbyes,
"what can you do". These are answered directly, with no retrieval and no sources.

A message counts as small talk only if nothing is left once the small-talk phrases and
filler words are removed, so "hi, when is REVELS?" still goes to search.
"""
import re

# (kind, phrases), longest phrases first within each kind
PHRASES = {
    "how_are_you": ["how are you doing", "how are you", "how r u", "how's it going", "hows it going", "how is it going",
                    "what's up", "whats up", "wassup", "sup"],
    "capabilities": ["what can you do", "what do you do", "who are you", "what are you", "how can you help",
                     "what can i ask", "help me", "help"],
    "thanks": ["thank you so much", "thank you very much", "thanks a lot", "thank you", "thankyou", "thanks", "thank u",
               "thx", "ty", "much appreciated", "appreciate it", "धन्यवाद", "शुक्रिया", "ಧನ್ಯವಾದ", "ಧನ್ಯವಾದಗಳು"],
    "goodbye": ["good night", "goodbye", "good bye", "see you", "see ya", "bye", "cya", "take care"],
    "acknowledge": ["got it", "makes sense", "sounds good", "okay", "ok", "okk", "cool", "great", "nice", "awesome",
                    "perfect", "alright", "sure", "fine", "noted", "understood"],
    "greeting": ["good morning", "good afternoon", "good evening", "hello", "hey there", "hi there", "heyy", "hey",
                 "hii", "hi", "hiya", "yo", "namaste", "namaskara", "नमस्ते", "नमस्कार", "ನಮಸ್ಕಾರ", "ನಮಸ್ತೆ"],
}
FILLER = {"mitra", "there", "bot", "so", "much", "very", "please", "again", "guys", "everyone", "dear", "sir", "maam",
          "ma'am", "buddy", "bro", "friend", "and", "you", "too", "a", "lot", "ji", "today", "the", "for"}

REPLIES = {
    "en": {
        "greeting": "Hi! I'm MITra, your campus companion. Ask me about academics, exams and the calendar, clubs, faculty or campus life.",
        "how_are_you": "I'm doing well, thanks for asking! What would you like to know about MIT Manipal today?",
        "capabilities": "I answer questions from MIT Manipal's official documents: regulations, the academic calendar, "
                        "syllabi and course plans, fees and cutoffs, clubs and the faculty directory. Each answer lists its sources.",
        "thanks": "You're welcome! Ask me anything else about MIT Manipal whenever you need.",
        "acknowledge": "Glad that helps! Anything else you'd like to know?",
        "goodbye": "Bye! Come back anytime you have a question about campus.",
    },
    "hi": {
        "greeting": "नमस्ते! मैं MITra हूँ, आपका कैंपस साथी। पढ़ाई, परीक्षा और कैलेंडर, क्लब, फैकल्टी या कैंपस जीवन के बारे में पूछें।",
        "how_are_you": "मैं ठीक हूँ, पूछने के लिए धन्यवाद! आज MIT Manipal के बारे में क्या जानना चाहेंगे?",
        "capabilities": "मैं MIT Manipal के आधिकारिक दस्तावेज़ों से जवाब देता हूँ: नियम, अकादमिक कैलेंडर, सिलेबस, फीस और कटऑफ, क्लब और फैकल्टी। हर जवाब के साथ स्रोत दिए जाते हैं।",
        "thanks": "आपका स्वागत है! MIT Manipal के बारे में कुछ और पूछना हो तो कभी भी पूछें।",
        "acknowledge": "अच्छा लगा कि मदद हुई! और कुछ जानना चाहेंगे?",
        "goodbye": "अलविदा! कैंपस से जुड़ा कोई सवाल हो तो फिर आइए।",
    },
    "kn": {
        "greeting": "ನಮಸ್ಕಾರ! ನಾನು MITra, ನಿಮ್ಮ ಕ್ಯಾಂಪಸ್ ಸಂಗಾತಿ. ಓದು, ಪರೀಕ್ಷೆ ಮತ್ತು ಕ್ಯಾಲೆಂಡರ್, ಕ್ಲಬ್‌ಗಳು, ಅಧ್ಯಾಪಕರು ಅಥವಾ ಕ್ಯಾಂಪಸ್ ಜೀವನದ ಬಗ್ಗೆ ಕೇಳಿ.",
        "how_are_you": "ನಾನು ಚೆನ್ನಾಗಿದ್ದೇನೆ, ಕೇಳಿದ್ದಕ್ಕೆ ಧನ್ಯವಾದ! ಇಂದು MIT Manipal ಬಗ್ಗೆ ಏನು ತಿಳಿಯಬೇಕು?",
        "capabilities": "ನಾನು MIT Manipal ನ ಅಧಿಕೃತ ದಾಖಲೆಗಳಿಂದ ಉತ್ತರಿಸುತ್ತೇನೆ: ನಿಯಮಗಳು, ಅಕಾಡೆಮಿಕ್ ಕ್ಯಾಲೆಂಡರ್, ಪಠ್ಯಕ್ರಮ, ಶುಲ್ಕ ಮತ್ತು ಕಟ್‌ಆಫ್, ಕ್ಲಬ್‌ಗಳು ಮತ್ತು ಅಧ್ಯಾಪಕರು. ಪ್ರತಿ ಉತ್ತರದೊಂದಿಗೆ ಮೂಲಗಳಿರುತ್ತವೆ.",
        "thanks": "ಸ್ವಾಗತ! MIT Manipal ಬಗ್ಗೆ ಇನ್ನೇನಾದರೂ ಬೇಕಾದರೆ ಯಾವಾಗ ಬೇಕಾದರೂ ಕೇಳಿ.",
        "acknowledge": "ಸಹಾಯವಾಗಿದ್ದು ಖುಷಿ! ಇನ್ನೇನಾದರೂ ತಿಳಿಯಬೇಕೇ?",
        "goodbye": "ಬೈ! ಕ್ಯಾಂಪಸ್ ಬಗ್ಗೆ ಪ್ರಶ್ನೆ ಇದ್ದಾಗ ಮತ್ತೆ ಬನ್ನಿ.",
    },
}
# When several kinds appear ("hi, thanks!"), answer the most specific one
PRIORITY = ["capabilities", "how_are_you", "thanks", "goodbye", "acknowledge", "greeting"]


def small_talk_kind(message: str) -> str | None:
    """The kind of small talk the whole message is, or None if it asks for anything else."""
    text = " " + re.sub(r"[^\w\s'ऀ-ॿಀ-೿]", " ", (message or "").lower()) + " "
    text = " ".join(text.split())
    if not text or len(text) > 80:
        return None
    found = set()
    padded = f" {text} "
    for kind, phrases in PHRASES.items():
        for phrase in sorted(phrases, key=len, reverse=True):
            if f" {phrase} " in padded:
                found.add(kind)
                padded = padded.replace(f" {phrase} ", " ")
    leftover = [w for w in padded.split() if w not in FILLER]
    if not found or leftover:
        return None
    return next(kind for kind in PRIORITY if kind in found)


def small_talk_reply(message: str, language: str = "en") -> str | None:
    kind = small_talk_kind(message)
    if not kind:
        return None
    return REPLIES.get(language, REPLIES["en"])[kind]

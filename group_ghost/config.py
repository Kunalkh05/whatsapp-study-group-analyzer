"""
Config file containing all configuration values, weights, and keywords for Group Ghost.
This ensures centralized configuration management across the entire application.
"""

from pathlib import Path

# Paths
OUTPUT_JSON_PATH = "group_ghost_output.json"
OUTPUT_PDF_PATH = "group_ghost_report.pdf"

# Minimum messages required for a member to be included in scoring
MIN_MESSAGES_FOR_SCORING = 5

# Keywords for classifying academic content (includes Hinglish)
ACADEMIC_KEYWORDS = [
    # English keywords
    "exam", "test", "assignment", "submit", "deadline", "marks", "grade",
    "syllabus", "chapter", "notes", "study", "lecture", "professor", "sir",
    "ma'am", "practical", "lab", "viva", "internal", "external", "unit",
    "doubt", "question", "answer", "explain", "concept", "formula",
    "definition", "theorem", "proof", "derivation", "numericals",
    "reference", "textbook", "pdf", "slides", "ppt", "resources",
    "important", "topic", "revision", "schedule", "timetable", "class",
    # Hinglish keywords
    "padhai", "padhna", "exam", "notes bhejo", "kab hai", "kitna", 
    "syllabus", "doubt", "samajh", "explain karo", "bhejo", "tayari", 
    "taiari", "viva", "practical", "assignment", "marks", "grade",
    "sheet", "link", "gmeet", "zoom", "lecture", "class", "prof", "paper"
]

# Keywords for classifying noise/off-topic content (includes Hinglish)
NOISE_KEYWORDS = [
    # English/emojis noise
    "lol", "lmao", "haha", "😂", "🤣", "meme", "bro", "yaar", "bhai",
    "chill", "party", "game", "movie", "food", "canteen", "chai",
    "good morning", "gm", "good night", "gn", "happy birthday",
    "congratulations", "🎉", "❤️", "👍", "😭", "💀", "bye", "hey",
    "hi", "hello", "ok", "k", "okay", "cool", "nice", "awesome",
    # Hinglish noise
    "yaar", "bhai", "bro", "chill", "sahi hai", "haan", "nahi", "na",
    "ha", "party", "chai", "canteen", "kya chal raha", "mast", "badhiya",
    "ghoomne", "movie", "match", "cricket", "pubg", "valorant", "game",
    "bakwaas", "faltu", "timepass", "chhod", "hatao", "maje", "masti"
]

# Markers identifying questions (both English and Hinglish question words)
QUESTION_MARKERS = [
    "?", "kya", "kaise", "kyun", "when", "what", "how", "which",
    "where", "who", "doubt", "confused", "help", "please share",
    "can anyone", "does anyone", "anyone know", "kab", "kaha", 
    "kidhar", "kon", "kaun", "batao", "kisi ko pata", "kisi ko"
]

# Weights for the 5 dimensions of Contributor Score
SCORING_WEIGHTS = {
    "academic_signal_ratio": 0.30,
    "sentiment_score": 0.10,
    "topic_contribution": 0.25,
    "response_behavior": 0.20,
    "noise_penalty": 0.15
}

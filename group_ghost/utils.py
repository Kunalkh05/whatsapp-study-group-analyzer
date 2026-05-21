"""
Utility functions for text cleaning, keyword search, normalization,
and JSON data operations in the Group Ghost application.
"""

import re
import json
import datetime
from pathlib import Path

# Compile emoji regex covering common emoji Unicode blocks (Dingbats, Emoticons, Symbols, Flags, etc.)
EMOJI_PATTERN = re.compile(
    "["
    "\U00010000-\U0010FFFF"  # Emoji / symbols in non-BMP plane
    "\u2600-\u27BF"          # Dingbats & Miscellaneous Symbols in BMP plane
    "\u2300-\u23FF"          # Miscellaneous Technical
    "\u2B50"                 # Star symbol
    "\u2B06"                 # Arrow symbols
    "]+", flags=re.UNICODE
)

# URL regex
URL_PATTERN = re.compile(r'https?://\S+|www\.\S+')

# Special characters except ? and ! regex
SPECIAL_CHARS_PATTERN = re.compile(r'[^a-zA-Z0-9\s?!]')

def clean_text(text: str) -> str:
    """
    Cleans message text by performing the following:
      1. Converts text to lowercase
      2. Removes URLs
      3. Removes emojis using Unicode ranges
      4. Removes special characters except '?' and '!'
      5. Strips extra whitespace
    
    Args:
        text (str): Raw message text.
        
    Returns:
        str: Cleaned text.
    """
    if not text:
        return ""
    
    # 1. Lowercase
    cleaned = text.lower()
    
    # 2. Remove URLs
    cleaned = URL_PATTERN.sub('', cleaned)
    
    # 3. Remove emojis
    cleaned = EMOJI_PATTERN.sub('', cleaned)
    
    # 4. Remove special characters except ? and !
    cleaned = SPECIAL_CHARS_PATTERN.sub(' ', cleaned)
    
    # 5. Strip extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

def contains_any(text: str, keyword_list: list[str]) -> bool:
    """
    Performs a case-insensitive check to determine if any keyword in keyword_list 
    appears in the text.
    
    Args:
        text (str): Message text to search.
        keyword_list (list[str]): List of keywords to check.
        
    Returns:
        bool: True if any keyword matches as a substring, False otherwise.
    """
    if not text or not keyword_list:
        return False
    text_lower = text.lower()
    for kw in keyword_list:
        if kw.lower() in text_lower:
            return True
    return False

def count_keywords(text: str, keyword_list: list[str]) -> int:
    """
    Counts how many unique or total keywords from keyword_list appear in the text (case-insensitive).
    We count occurrences of keywords within the text.
    
    Args:
        text (str): Message text to search.
        keyword_list (list[str]): List of keywords to count.
        
    Returns:
        int: Number of times any keyword from the list is found in the text.
    """
    if not text or not keyword_list:
        return 0
    text_lower = text.lower()
    count = 0
    for kw in keyword_list:
        count += text_lower.count(kw.lower())
    return count

def normalize_scores(score_dict: dict[str, float]) -> dict[str, float]:
    """
    Normalizes all values in a score dictionary to a 0.0 - 1.0 scale using min-max scaling.
    If all values are identical, returns 0.5 for all keys.
    
    Args:
        score_dict (dict[str, float]): A dictionary mapping keys to raw scores.
        
    Returns:
        dict[str, float]: A new dictionary with normalized scores.
    """
    if not score_dict:
        return {}
    
    values = list(score_dict.values())
    min_val = min(values)
    max_val = max(values)
    
    normalized = {}
    range_val = max_val - min_val
    
    if range_val == 0:
        for k in score_dict:
            normalized[k] = 0.5
    else:
        for k, v in score_dict.items():
            normalized[k] = (v - min_val) / range_val
            
    return normalized

class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle datetime objects by converting them to ISO format.
    """
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return super().default(obj)

def save_json(data, path: str) -> None:
    """
    Saves python datatypes/objects to a JSON file at the path, indented by 2,
    handling datetime objects cleanly.
    
    Args:
        data: Python dict or list data to serialize.
        path (str): Filepath to save the JSON.
    """
    file_path = Path(path)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, cls=CustomJSONEncoder, indent=2, ensure_ascii=False)

def get_member_messages(messages: list[dict], member: str) -> list[dict]:
    """
    Filters chat messages to retrieve only those sent by a specific member.
    
    Args:
        messages (list[dict]): Full list of parsed message dictionaries.
        member (str): The name/sender to filter by.
        
    Returns:
        list[dict]: Filtered message list.
    """
    return [msg for msg in messages if msg.get("sender") == member]

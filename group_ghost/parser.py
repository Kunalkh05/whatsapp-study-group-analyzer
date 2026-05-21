"""
WhatsApp chat log parser supporting Android and iPhone formats.
Handles multi-line messages, system messages, media attachments, and timestamps.
"""

import re
from datetime import datetime, date
from pathlib import Path

def detect_format(raw_text: str) -> str:
    """
    Detects whether the file format is Android or iPhone based on the first few lines.
    iPhone format typically has square brackets enclosing the timestamp at the beginning of lines.
    
    Args:
        raw_text (str): A chunk or complete raw text from the WhatsApp export file.
        
    Returns:
        str: "iphone" or "android".
    """
    lines = raw_text.splitlines()[:50]
    iphone_count = 0
    android_count = 0
    
    # iPhone: [12/05/2024, 15:45:22] Ayush: ...
    # Android: 12/05/2024, 3:45 PM - Ayush: ...
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('[') and ']' in line:
            # Check if there is a date/time structure inside the brackets
            content = line[1:line.find(']')]
            if ',' in content and ('/' in content or '-' in content):
                iphone_count += 1
        elif re.match(r'^\d{1,2}/\d{1,2}/\d{2,4},', line):
            android_count += 1
            
    if iphone_count > android_count:
        return "iphone"
    elif android_count > iphone_count:
        return "android"
    else:
        # Fallback if counts are equal or zero
        if "[" in raw_text[:1000] and "]" in raw_text[:1000]:
            return "iphone"
        return "android"

def parse_datetime(date_str: str, time_str: str) -> datetime:
    """
    Tries multiple datetime formats to parse WhatsApp date and time strings.
    
    Args:
        date_str (str): Extracted date string.
        time_str (str): Extracted time string.
        
    Returns:
        datetime: Parsed datetime object.
        
    Raises:
        ValueError: If none of the formats match the datetime strings.
    """
    # Combine clean strings
    dt_str = f"{date_str.strip()} {time_str.strip()}"
    # Replace non-breaking spaces if any, and clean whitespace
    dt_str = re.sub(r'\s+', ' ', dt_str).replace('\u202f', ' ').replace('\u200e', '').replace('\u200f', '')
    
    # Formats to try
    formats = [
        # 12-hour with AM/PM
        "%d/%m/%Y %I:%M %p",
        "%d/%m/%y %I:%M %p",
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%y %I:%M %p",
        # 12-hour with seconds and AM/PM
        "%d/%m/%Y %I:%M:%S %p",
        "%d/%m/%y %I:%M:%S %p",
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%y %I:%M:%S %p",
        # 24-hour with seconds
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%y %H:%M:%S",
        # 24-hour without seconds
        "%d/%m/%Y %H:%M",
        "%d/%m/%y %H:%M",
        "%m/%d/%Y %H:%M",
        "%m/%d/%y %H:%M",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
            
    # Try one final check with standard ISO or replacing dots in PM/AM
    dt_str_clean = dt_str.replace('p.m.', 'PM').replace('a.m.', 'AM').replace('pm', 'PM').replace('am', 'AM')
    for fmt in formats:
        try:
            return datetime.strptime(dt_str_clean, fmt)
        except ValueError:
            continue
            
    raise ValueError(f"Could not parse date and time: '{date_str}', '{time_str}'")

def parse_chat(file_path: str) -> list[dict]:
    """
    Parses a WhatsApp chat export file (.txt) into a list of message dicts.
    Handles multi-line messages, system messages, media flags, and filters noise.
    
    Args:
        file_path (str): Path to the WhatsApp exported chat .txt file.
        
    Returns:
        list[dict]: A sorted list of message dictionaries.
        
    Raises:
        ValueError: If file is unrecognized or empty.
        FileNotFoundError: If the file does not exist.
    """
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    # Read file with UTF-8 first, fallback to Latin-1
    try:
        with open(p, 'r', encoding='utf-8') as f:
            raw_text = f.read()
    except UnicodeDecodeError:
        with open(p, 'r', encoding='latin-1') as f:
            raw_text = f.read()
            
    if not raw_text.strip():
        raise ValueError("The uploaded chat file is empty.")
        
    chat_format = detect_format(raw_text)
    messages = []
    
    # Regex definitions for message splits
    # Android format: 12/05/2024, 3:45 PM - Sender: Message
    android_pattern = re.compile(
        r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm|a\.m\.|p\.m\.))?)\s*-\s*(.*)$'
    )
    
    # iPhone format: [12/05/2024, 15:45:22] Sender: Message
    iphone_pattern = re.compile(
        r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm|a\.m\.|p\.m\.))?)\]\s*(.*)$'
    )
    
    # System patterns/phrases that indicate non-user messages
    system_indicators = [
        "Messages and calls are end-to-end encrypted",
        "You were added",
        "changed the subject",
        "changed the group description",
        "left",
        "added",
        "This message was deleted",
        "missed voice call",
        "missed video call",
        "created this group",
        "changed this group's icon",
        "changed their phone number",
        "joined using this group's invite link"
    ]
    
    lines = raw_text.splitlines()
    current_msg = None
    
    for line in lines:
        line_stripped = line.strip()
        # Skip empty lines that are not part of an ongoing multi-line message
        if not line_stripped and not current_msg:
            continue
            
        # Try to match the timestamp based on detected format
        match = None
        if chat_format == "iphone":
            match = iphone_pattern.match(line_stripped)
        else:
            match = android_pattern.match(line_stripped)
            
        if match:
            # If we had an active message, save it
            if current_msg:
                messages.append(current_msg)
                current_msg = None
                
            date_str, time_str, content_str = match.groups()
            
            try:
                dt = parse_datetime(date_str, time_str)
            except ValueError:
                # If timestamp parsing fails, treat it as a text continuation if possible
                if current_msg:
                    current_msg["message"] += "\n" + line
                    continue
                else:
                    # Skip or treat as system message if no previous message exists
                    continue
            
            # Split sender and message
            # Senders can contain characters and punctuation but usually end with ':'
            sender = "System"
            message_body = content_str
            is_system = False
            is_media = False
            
            colon_idx = content_str.find(':')
            if colon_idx != -1:
                potential_sender = content_str[:colon_idx].strip()
                # Check that sender doesn't match known system phrases and looks like a name or phone number
                # Phone numbers have digits, +, -, spaces. Names are characters.
                # A system message wouldn't normally have ':' unless it's like "changed the description to: ..."
                # If there are system indicator keywords inside the "potential_sender", it might be a system message
                is_potential_system = False
                for term in system_indicators:
                    if term in potential_sender:
                        is_potential_system = True
                        break
                
                if not is_potential_system:
                    sender = potential_sender
                    message_body = content_str[colon_idx + 1:].strip()
                else:
                    is_system = True
            else:
                is_system = True
                
            # Perform system message checks on message body
            for indicator in system_indicators:
                if indicator in message_body or indicator in content_str:
                    is_system = True
                    break
                    
            # Check for media omissions
            if "<Media omitted>" in message_body or "[media omitted]" in message_body.lower() or "image omitted" in message_body.lower():
                is_media = True
                
            word_count = len(message_body.split()) if not is_media and not is_system else 0
            char_count = len(message_body) if not is_media and not is_system else 0
            
            current_msg = {
                "timestamp": dt,
                "date": dt.date(),
                "hour": dt.hour,
                "sender": sender,
                "message": message_body,
                "is_system": is_system,
                "is_media": is_media,
                "word_count": word_count,
                "char_count": char_count
            }
        else:
            # This line does not match the timestamp regex.
            # If we are currently building a message, append this line as a multi-line continuation.
            if current_msg:
                # Update text, word count, and char count
                current_msg["message"] += "\n" + line
                if not current_msg["is_media"] and not current_msg["is_system"]:
                    current_msg["word_count"] = len(current_msg["message"].split())
                    current_msg["char_count"] = len(current_msg["message"])
            else:
                # Discard or keep if it's the very start of the file without a timestamp
                pass
                
    # Append the last message
    if current_msg:
        messages.append(current_msg)
        
    # Sort messages chronologically
    messages.sort(key=lambda x: x["timestamp"])
    
    if len(messages) < 10:
        raise ValueError(f"Chat contains too few messages ({len(messages)}). Minimum 10 required.")
        
    return messages

def get_members(messages: list[dict]) -> list[str]:
    """
    Returns a sorted list of unique non-system member names/senders.
    
    Args:
        messages (list[dict]): Extracted message list.
        
    Returns:
        list[str]: Sorted, unique sender names.
    """
    senders = set()
    for msg in messages:
        sender = msg.get("sender")
        if sender and sender != "System" and not msg.get("is_system"):
            senders.add(sender)
    return sorted(list(senders))

def get_date_range(messages: list[dict]) -> tuple[date, date]:
    """
    Extracts the date range covered by the chat log.
    
    Args:
        messages (list[dict]): Extracted message list.
        
    Returns:
        tuple[date, date]: Earliest and latest date objects.
    """
    if not messages:
        return date.today(), date.today()
    dates = [msg["date"] for msg in messages]
    return min(dates), max(dates)

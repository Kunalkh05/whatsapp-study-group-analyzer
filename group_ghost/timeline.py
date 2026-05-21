"""
Temporal analysis of group chat activity across hours of the day,
days of the week, calendar heatmaps, peak study hours, and exam panic days.
"""

from collections import Counter
import datetime
import numpy as np

import config
import utils

def messages_by_hour(messages: list[dict]) -> dict[int, int]:
    """
    Counts total messages sent during each hour of the day (0-23).
    Ensures all 24 hours are represented in the dictionary.
    
    Args:
        messages (list[dict]): Parsed list of messages.
        
    Returns:
        dict[int, int]: Mapping of hour (0-23) -> message count.
    """
    counts = Counter(msg["hour"] for msg in messages if not msg.get("is_system"))
    # Initialize all 24 hours with 0
    return {h: counts.get(h, 0) for h in range(24)}

def messages_by_day(messages: list[dict]) -> dict[str, int]:
    """
    Counts total messages sent on each day of the week (Monday-Sunday).
    Ensures all 7 weekdays are represented in chronological order.
    
    Args:
        messages (list[dict]): Parsed list of messages.
        
    Returns:
        dict[str, int]: Mapping of weekday name -> message count.
    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    counts = Counter(
        msg["timestamp"].strftime("%A") 
        for msg in messages 
        if not msg.get("is_system")
    )
    return {d: counts.get(d, 0) for d in days}

def academic_activity_by_hour(messages: list[dict]) -> dict[int, float]:
    """
    Computes the academic signal ratio for each hour of the day.
    
    Args:
        messages (list[dict]): Parsed list of messages.
        
    Returns:
        dict[int, float]: Mapping of hour (0-23) -> academic ratio.
    """
    hour_academic = {h: 0 for h in range(24)}
    hour_total = {h: 0 for h in range(24)}
    
    for msg in messages:
        if msg.get("is_system") or msg.get("is_media"):
            continue
        hour = msg["hour"]
        hour_total[hour] += 1
        if utils.contains_any(msg.get("message", ""), config.ACADEMIC_KEYWORDS):
            hour_academic[hour] += 1
            
    ratios = {}
    for h in range(24):
        total = hour_total[h]
        ratios[h] = float(hour_academic[h] / total) if total > 0 else 0.0
        
    return ratios

def messages_by_date(messages: list[dict]) -> dict[str, int]:
    """
    Counts messages per calendar date (formatted as YYYY-MM-DD strings).
    Useful for populating calendar timeline heatmaps.
    
    Args:
        messages (list[dict]): Parsed list of messages.
        
    Returns:
        dict[str, int]: Mapping of date string -> message count.
    """
    counts = Counter(
        msg["date"].isoformat() 
        for msg in messages 
        if not msg.get("is_system")
    )
    # Sort chronological
    return {k: v for k, v in sorted(counts.items())}

def get_peak_study_hours(messages: list[dict]) -> list[int]:
    """
    Identifies the top 3 hours of the day (0-23) with the highest academic ratio.
    Considers only hours that have a minimum threshold of 10 total messages to ensure significance.
    
    Args:
        messages (list[dict]): Parsed list of messages.
        
    Returns:
        list[int]: Top 3 peak hours sorted descending by academic ratio.
    """
    hour_academic = {h: 0 for h in range(24)}
    hour_total = {h: 0 for h in range(24)}
    
    for msg in messages:
        if msg.get("is_system") or msg.get("is_media"):
            continue
        hour = msg["hour"]
        hour_total[hour] += 1
        if utils.contains_any(msg.get("message", ""), config.ACADEMIC_KEYWORDS):
            hour_academic[hour] += 1
            
    hour_ratios = []
    for h in range(24):
        total = hour_total[h]
        if total >= 10:  # Significance threshold
            ratio = hour_academic[h] / total
            hour_ratios.append((h, ratio))
            
    # Sort by ratio descending
    hour_ratios.sort(key=lambda x: x[1], reverse=True)
    return [h for h, _ in hour_ratios[:3]]

def get_exam_panic_days(messages: list[dict]) -> list[str]:
    """
    Identifies "exam panic days" in the chat history.
    These are days where:
      1. Message volume is at least 2x the daily average message volume.
      2. The academic signal ratio for that day is greater than 0.5.
      
    Args:
        messages (list[dict]): Parsed list of messages.
        
    Returns:
        list[str]: Sorted list of date strings (YYYY-MM-DD).
    """
    # Group messages by date
    daily_msgs = {}
    for msg in messages:
        if msg.get("is_system"):
            continue
        d_str = msg["date"].isoformat()
        if d_str not in daily_msgs:
            daily_msgs[d_str] = []
        daily_msgs[d_str].append(msg)
        
    if not daily_msgs:
        return []
        
    # Calculate daily volumes
    volumes = [len(msgs) for msgs in daily_msgs.values()]
    avg_daily_volume = np.mean(volumes)
    
    panic_days = []
    
    for d_str, msgs in daily_msgs.items():
        volume = len(msgs)
        # Check volume is 2x the daily average
        if volume >= (2 * avg_daily_volume) and volume >= 5: # Guard min size
            # Calculate academic ratio
            valid_msgs = [m for m in msgs if not m.get("is_media")]
            if not valid_msgs:
                continue
            academic_count = sum(
                1 for m in valid_msgs 
                if utils.contains_any(m.get("message", ""), config.ACADEMIC_KEYWORDS)
            )
            ratio = academic_count / len(valid_msgs)
            
            if ratio > 0.5:
                panic_days.append(d_str)
                
    return sorted(panic_days)

"""
Scorer for individual WhatsApp group members across 5 dimensions:
1. Academic signal ratio
2. Sentiment score (VADER)
3. Topic contribution (introduction of topics)
4. Response behavior (replies to others' questions and own questions being answered)
5. Noise/meme penalty

Combines these dimensions into a single Contributor Score per member.
"""

import nltk
try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
except ImportError:
    # Handle if NLTK is not fully installed yet in early load phase
    pass

import config
import utils

# Global placeholder for VADER Sentiment Intensity Analyzer
_sia = None

def get_sentiment_analyzer():
    """
    Lazy loader for NLTK's VADER SentimentIntensityAnalyzer.
    Downloads the vader_lexicon corpus silently if it is not available.
    """
    global _sia
    if _sia is None:
        try:
            # Try to initialize
            _sia = SentimentIntensityAnalyzer()
        except (LookupError, NameError):
            # If not found or ImportError, download and initialize
            nltk.download('vader_lexicon', quiet=True)
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            _sia = SentimentIntensityAnalyzer()
    return _sia

def compute_academic_signal_ratio(member_messages: list[dict]) -> float:
    """
    Calculates the proportion of a member's messages that are study/academic related.
    Excludes media messages from the denominator as they are media files rather than texts.
    
    Args:
        member_messages (list[dict]): Filtered list of messages for a single member.
        
    Returns:
        float: Academic signal ratio between 0.0 and 1.0.
    """
    # Exclude system and media messages
    valid_msgs = [m for m in member_messages if not m.get("is_system") and not m.get("is_media")]
    if not valid_msgs:
        return 0.0
        
    academic_count = sum(
        1 for m in valid_msgs 
        if utils.contains_any(m.get("message", ""), config.ACADEMIC_KEYWORDS)
    )
    
    return float(academic_count / len(valid_msgs))

def compute_sentiment_score(member_messages: list[dict]) -> float:
    """
    Computes the average compound sentiment score across a member's non-media messages
    using NLTK's VADER SentimentIntensityAnalyzer. Normalizes from [-1.0, 1.0] to [0.0, 1.0].
    
    Args:
        member_messages (list[dict]): Filtered list of messages for a single member.
        
    Returns:
        float: Average sentiment score between 0.0 and 1.0.
    """
    valid_msgs = [m for m in member_messages if not m.get("is_system") and not m.get("is_media")]
    if not valid_msgs:
        return 0.5  # Neutral default
        
    sia = get_sentiment_analyzer()
    total_compound = 0.0
    
    for m in valid_msgs:
        score = sia.polarity_scores(m.get("message", ""))
        total_compound += score["compound"]
        
    avg_compound = total_compound / len(valid_msgs)
    
    # Normalize from [-1.0, 1.0] to [0.0, 1.0]
    normalized_score = (avg_compound + 1.0) / 2.0
    return float(normalized_score)

def compute_noise_penalty(member_messages: list[dict]) -> float:
    """
    Calculates the noise ratio in a member's messages based on NOISE_KEYWORDS.
    
    Args:
        member_messages (list[dict]): Filtered list of messages for a single member.
        
    Returns:
        float: Noise penalty ratio between 0.0 and 1.0.
    """
    valid_msgs = [m for m in member_messages if not m.get("is_system") and not m.get("is_media")]
    if not valid_msgs:
        return 0.0
        
    noise_count = sum(
        1 for m in valid_msgs 
        if utils.contains_any(m.get("message", ""), config.NOISE_KEYWORDS)
    )
    
    return float(noise_count / len(valid_msgs))

def compute_response_behavior(member: str, all_messages: list[dict]) -> float:
    """
    Computes a member's response behavior based on two factors:
      1. How often they reply to questions asked by other members (within a 10-message window).
      2. How often their own questions are answered by other members.
      
    Args:
        member (str): The name/sender to score.
        all_messages (list[dict]): The full list of parsed messages.
        
    Returns:
        float: Response behavior score between 0.0 and 1.0.
    """
    # 1. Replies to questions by others
    # Identify indices of questions by other members
    questions_by_others = []
    for idx, msg in enumerate(all_messages):
        if msg.get("is_system") or msg.get("is_media"):
            continue
        if msg.get("sender") != member and utils.contains_any(msg.get("message", ""), config.QUESTION_MARKERS):
            questions_by_others.append(idx)
            
    replies_given = 0
    if questions_by_others:
        for q_idx in questions_by_others:
            # Check if this member replied within the next 10 messages
            replied = False
            for r_idx in range(q_idx + 1, min(q_idx + 11, len(all_messages))):
                reply_msg = all_messages[r_idx]
                if reply_msg.get("is_system") or reply_msg.get("is_media"):
                    continue
                if reply_msg.get("sender") == member:
                    replied = True
                    break
            if replied:
                replies_given += 1
        response_rate = replies_given / len(questions_by_others)
    else:
        response_rate = 0.5  # Neutral default if no questions by others
        
    # 2. How often their own questions are answered by others
    own_questions = []
    for idx, msg in enumerate(all_messages):
        if msg.get("is_system") or msg.get("is_media"):
            continue
        if msg.get("sender") == member and utils.contains_any(msg.get("message", ""), config.QUESTION_MARKERS):
            own_questions.append(idx)
            
    answered_own = 0
    if own_questions:
        for q_idx in own_questions:
            answered = False
            for r_idx in range(q_idx + 1, min(q_idx + 11, len(all_messages))):
                reply_msg = all_messages[r_idx]
                if reply_msg.get("is_system") or reply_msg.get("is_media"):
                    continue
                if reply_msg.get("sender") != member:  # Answered by someone else
                    answered = True
                    break
            if answered:
                answered_own += 1
        own_question_solved_rate = answered_own / len(own_questions)
    else:
        own_question_solved_rate = 1.0  # Default to perfect if they never needed to ask a question
        
    # Combine both aspects (80% reply rate, 20% own questions answered rate)
    combined = (0.8 * response_rate) + (0.2 * own_question_solved_rate)
    return float(min(max(combined, 0.0), 1.0))

def compute_topic_contribution(member: str, all_messages: list[dict], topic_model_results: dict) -> float:
    """
    Computes a member's topic contribution score. Checks how many unique topics
    in the conversation were first introduced by this member.
    
    Args:
        member (str): The name/sender to score.
        all_messages (list[dict]): The full list of parsed messages.
        topic_model_results (dict): The output from the LDA topic modeling.
        
    Returns:
        float: Topic contribution score between 0.0 and 1.0.
    """
    topic_introducers = {}  # topic_key/id -> sender name
    
    academic_msgs = [
        msg for msg in all_messages 
        if not msg.get("is_system") and not msg.get("is_media") and utils.contains_any(msg.get("message", ""), config.ACADEMIC_KEYWORDS)
    ]
    
    # CASE 1: LDA active, doc-topic matrix is available
    if not topic_model_results.get("fallback") and topic_model_results.get("doc_topic_matrix"):
        doc_topic_matrix = topic_model_results["doc_topic_matrix"]
        num_topics = len(topic_model_results["topics"])
        
        # Guard check
        if len(doc_topic_matrix) == len(academic_msgs):
            for t_idx in range(num_topics):
                # Search chronologically for the first member who introduced the topic with probability > 0.3
                for doc_idx, msg in enumerate(academic_msgs):
                    prob = doc_topic_matrix[doc_idx][t_idx]
                    if prob > 0.3:
                        topic_introducers[t_idx] = msg["sender"]
                        break
                        
    # CASE 2: Fallback (LDA failed or too few messages)
    # We trace who first introduced the top 5 academic keywords in the chat.
    else:
        top_kws = [kw for kw, _ in topic_model_results.get("top_keywords", [])[:5]]
        if not top_kws:
            # Fallback to standard academic list
            top_kws = config.ACADEMIC_KEYWORDS[:5]
            
        for kw in top_kws:
            for msg in all_messages:
                if msg.get("is_system") or msg.get("is_media"):
                    continue
                if kw.lower() in msg.get("message", "").lower():
                    topic_introducers[kw] = msg["sender"]
                    break
                    
    if not topic_introducers:
        return 0.0
        
    introduced_count = sum(1 for sender in topic_introducers.values() if sender == member)
    total_topics = len(topic_introducers)
    
    return float(introduced_count / total_topics)

def compute_contributor_score(academic: float, sentiment: float, topic: float, response: float, noise: float) -> float:
    """
    Applies configuration weights to dimension scores and subtracts noise penalty.
    Clamps final output between 0.0 and 1.0.
    
    Args:
        academic (float): Academic signal ratio.
        sentiment (float): VADER sentiment score.
        topic (float): Topic contribution score.
        response (float): Response behavior score.
        noise (float): Noise penalty score.
        
    Returns:
        float: Calculated Contributor Score.
    """
    w = config.SCORING_WEIGHTS
    score = (
        (academic * w["academic_signal_ratio"]) +
        (sentiment * w["sentiment_score"]) +
        (topic * w["topic_contribution"]) +
        (response * w["response_behavior"]) -
        (noise * w["noise_penalty"])
    )
    # Clamp to [0.0, 1.0]
    return float(min(max(score, 0.0), 1.0))

def score_all_members(messages: list[dict], topic_results: dict) -> list[dict]:
    """
    Calculates 5-dimension scores and final Contributor Score for all qualifying members in the group.
    Qualifying members have at least MIN_MESSAGES_FOR_SCORING total messages.
    
    Args:
        messages (list[dict]): The full list of parsed messages.
        topic_results (dict): The output from the LDA topic model.
        
    Returns:
        list[dict]: Ranked list of dictionaries with scores, sorted descending by contributor_score.
    """
    import parser
    all_senders = parser.get_members(messages)
    scored_members = []
    
    for sender in all_senders:
        member_msgs = utils.get_member_messages(messages, sender)
        total_msg_count = len(member_msgs)
        
        # Skip members who fall below the activity threshold
        if total_msg_count < config.MIN_MESSAGES_FOR_SCORING:
            continue
            
        academic = compute_academic_signal_ratio(member_msgs)
        sentiment = compute_sentiment_score(member_msgs)
        noise = compute_noise_penalty(member_msgs)
        response = compute_response_behavior(sender, messages)
        topic = compute_topic_contribution(sender, messages, topic_results)
        
        final_score = compute_contributor_score(academic, sentiment, topic, response, noise)
        
        scored_members.append({
            "member": sender,
            "total_messages": total_msg_count,
            "academic_signal_ratio": float(round(academic, 4)),
            "sentiment_score": float(round(sentiment, 4)),
            "noise_penalty": float(round(noise, 4)),
            "response_behavior": float(round(response, 4)),
            "topic_contribution": float(round(topic, 4)),
            "contributor_score": float(round(final_score, 4))
        })
        
    # Sort members descending by contributor_score
    scored_members.sort(key=lambda x: x["contributor_score"], reverse=True)
    
    # Assign ranks and labels
    for idx, member_data in enumerate(scored_members):
        score = member_data["contributor_score"]
        member_data["rank"] = idx + 1
        
        if score > 0.7:
            member_data["label"] = "star"
        elif score > 0.4:
            member_data["label"] = "active"
        else:
            member_data["label"] = "lurker"
            
    return scored_members

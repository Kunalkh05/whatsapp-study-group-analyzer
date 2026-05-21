"""
Topic modeling and analysis using Spacy for tokenization/lemmatization
and Scikit-Learn LDA (Latent Dirichlet Allocation) for local unsupervised modeling.
"""

from collections import Counter
import spacy
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np

from config import ACADEMIC_KEYWORDS
import utils

# Global NLP engine placeholder for lazy loading
_nlp = None

def get_nlp_engine():
    """
    Lazy loads the Spacy English NLP model. If en_core_web_sm is not installed,
    falls back to a blank English model to prevent crashes.
    """
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
        except OSError:
            # Fallback if model not downloaded
            _nlp = spacy.blank("en")
    return _nlp

def preprocess_for_lda(messages: list[dict]) -> list[list[str]]:
    """
    Filters chat messages to academic-only content, cleans them, tokenizes,
    removes stopwords/punctuation/short words, and lemmatizes using Spacy.
    
    Args:
        messages (list[dict]): Parsed list of message dictionaries.
        
    Returns:
        list[list[str]]: A list of token lists (one token list per message).
    """
    # Filter academic messages only (excluding system/media)
    academic_msgs = [
        msg for msg in messages 
        if not msg.get("is_system") and not msg.get("is_media") and utils.contains_any(msg.get("message", ""), ACADEMIC_KEYWORDS)
    ]
    
    nlp = get_nlp_engine()
    token_lists = []
    
    # Process texts in batches for efficiency
    texts = [utils.clean_text(msg["message"]) for msg in academic_msgs]
    
    for doc in nlp.pipe(texts, batch_size=50):
        tokens = []
        for token in doc:
            # Keep only letters, remove stopwords, punctuation, and words under 3 chars
            if token.is_alpha and not token.is_stop and len(token.text) >= 3:
                # Use lemma if using en_core_web_sm, else standard text
                lemma = token.lemma_.lower() if token.lemma_ else token.text.lower()
                tokens.append(lemma)
        token_lists.append(tokens)
        
    return token_lists

def run_lda(token_lists: list[list[str]], n_topics: int = 5) -> dict:
    """
    Runs Latent Dirichlet Allocation (LDA) using CountVectorizer and Scikit-Learn.
    Handles fallbacks gracefully if there are too few words/messages.
    
    Args:
        token_lists (list[list[str]]): List of token lists.
        n_topics (int): Number of topics to build.
        
    Returns:
        dict: A dictionary containing details of detected topics and doc-topic matrix.
    """
    # Join tokens back to form "documents" for vectorizer
    docs = [" ".join(tokens) for tokens in token_lists if tokens]
    
    # Fallback check: if there are no valid documents or words, skip LDA
    if not docs or len(docs) < 3:
        return {
            "topics": [],
            "doc_topic_matrix": [],
            "fallback": True,
            "reason": "Too few academic messages to perform topic modeling."
        }
        
    try:
        # Build Vectorizer
        vectorizer = CountVectorizer(max_df=0.95, min_df=1, stop_words='english')
        tf = vectorizer.fit_transform(docs)
        
        feature_names = vectorizer.get_feature_names_out()
        if len(feature_names) < 3:
            return {
                "topics": [],
                "doc_topic_matrix": [],
                "fallback": True,
                "reason": "Vocabulary size is too small for topic extraction."
            }
            
        # Adjust n_topics if we have extremely few documents
        actual_topics = min(n_topics, len(docs))
        
        lda = LatentDirichletAllocation(
            n_components=actual_topics,
            max_iter=10,
            learning_method='online',
            random_state=42
        )
        doc_topic_matrix = lda.fit_transform(tf)
        
        topics_list = []
        for topic_idx, topic in enumerate(lda.components_):
            # Extract top 8 keywords
            top_kw_idxs = topic.argsort()[:-9:-1]
            keywords = [feature_names[i] for i in top_kw_idxs if i < len(feature_names)]
            
            # Autolabel using top 2 keywords
            label = " & ".join(keywords[:2]).upper() if len(keywords) >= 2 else f"TOPIC {topic_idx + 1}"
            
            topics_list.append({
                "topic_id": topic_idx,
                "keywords": keywords,
                "label": label
            })
            
        return {
            "topics": topics_list,
            "doc_topic_matrix": doc_topic_matrix.tolist(),
            "fallback": False
        }
        
    except Exception as e:
        return {
            "topics": [],
            "doc_topic_matrix": [],
            "fallback": True,
            "reason": f"LDA failed with error: {str(e)}"
        }

def get_member_topic_distribution(member: str, messages: list[dict], lda_results: dict) -> dict:
    """
    Computes a member's topic distribution based on their academic messages and the LDA matrix.
    
    Args:
        member (str): Name of the member.
        messages (list[dict]): Entire list of parsed messages.
        lda_results (dict): Output dict from run_lda.
        
    Returns:
        dict: Mapping of {topic_label: proportion} for this member.
    """
    # If LDA is fallback or doc_topic_matrix is empty, return empty dict
    if lda_results.get("fallback") or not lda_results.get("doc_topic_matrix"):
        return {}
        
    # Get all academic messages (the same filtering index used for doc_topic_matrix)
    academic_msgs = [
        msg for msg in messages 
        if not msg.get("is_system") and not msg.get("is_media") and utils.contains_any(msg.get("message", ""), ACADEMIC_KEYWORDS)
    ]
    
    # Filter academic messages that actually had non-empty tokens (matched docs in LDA)
    # The running index in run_lda was based on: docs = [" ".join(tokens) for tokens in token_lists if tokens]
    # We must replicate this precisely to align rows of doc_topic_matrix with senders
    token_lists = preprocess_for_lda(messages)
    
    valid_indices = []
    senders = []
    
    for i, tokens in enumerate(token_lists):
        if tokens:
            valid_indices.append(i)
            senders.append(academic_msgs[i]["sender"])
            
    doc_topic_matrix = lda_results["doc_topic_matrix"]
    
    # Check alignment safety
    if len(senders) != len(doc_topic_matrix):
        return {}
        
    # Aggregate topic vectors for the target member
    member_vectors = []
    for idx, sender in enumerate(senders):
        if sender == member:
            member_vectors.append(doc_topic_matrix[idx])
            
    if not member_vectors:
        return {}
        
    # Average the topic scores for this member
    mean_vector = np.mean(member_vectors, axis=0)
    
    dist_dict = {}
    for t_idx, topic_data in enumerate(lda_results["topics"]):
        label = topic_data["label"]
        dist_dict[label] = float(mean_vector[t_idx])
        
    return dist_dict

def get_top_academic_keywords(messages: list[dict], top_n: int = 20) -> list[tuple]:
    """
    Counts frequency of ACADEMIC_KEYWORDS across all messages and returns the top N.
    
    Args:
        messages (list[dict]): Parsed list of messages.
        top_n (int): Number of top keywords to return.
        
    Returns:
        list[tuple]: Sorted list of (keyword, count) tuples.
    """
    academic_words = []
    
    for msg in messages:
        if msg.get("is_system") or msg.get("is_media"):
            continue
        cleaned = utils.clean_text(msg.get("message", ""))
        words = cleaned.split()
        for word in words:
            if word in ACADEMIC_KEYWORDS:
                academic_words.append(word)
                
    counter = Counter(academic_words)
    return counter.most_common(top_n)

"""
Main entry point for Group Ghost. A Streamlit web application running completely 
on the local machine. Uploads WhatsApp chat logs, runs the processing pipelines,
and renders an interactive, beautifully styled, high-fidelity UI dashboard.
"""

import tempfile
import json
from datetime import datetime, date
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set up Streamlit Page Configuration (Must be the first Streamlit command)
st.set_page_config(
    page_title="Group Ghost — Study Group Analyzer",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Core imports from Group Ghost library
import config
import utils
import parser
import topic_analyzer
import scorer
import network_builder
import timeline
import report_generator

# Inject custom premium dark CSS styling for a state-of-the-art visual aesthetic
st.markdown("""
<style>
    /* Premium font imports */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Outfit:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    /* Elegant Title Styling */
    .app-title {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 50%, #FF4B2B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.1rem;
        animation: fadeIn 1s ease-in-out;
    }
    
    .app-subtitle {
        color: #A0AEC0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 300;
    }

    /* Custom Metric Cards */
    .metric-card {
        background: rgba(26, 32, 44, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        transition: transform 0.3s ease, border-color 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(255, 142, 83, 0.4);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #FFFFFF;
        background: linear-gradient(to right, #ffffff, #FF8E53);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #A0AEC0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    
    /* Custom Badges */
    .badge-star {
        background-color: rgba(29, 158, 117, 0.15);
        color: #1D9E75;
        border: 1px solid rgba(29, 158, 117, 0.3);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-block;
    }
    
    .badge-active {
        background-color: rgba(239, 159, 39, 0.15);
        color: #EF9F27;
        border: 1px solid rgba(239, 159, 39, 0.3);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-block;
    }
    
    .badge-lurker {
        background-color: rgba(136, 135, 128, 0.15);
        color: #888780;
        border: 1px solid rgba(136, 135, 128, 0.3);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-block;
    }

    /* Keyframe Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 1 — SIDEBAR & CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.sidebar.markdown("""
<div style='text-align: center; padding: 1rem 0;'>
    <h2 style='color: #FF8E53; font-size: 2.2rem; margin: 0;'>👻 Group Ghost</h2>
    <p style='color: #718096; font-size: 0.85rem;'>Study Group Intelligence Suite</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("Upload your chat")

uploaded_file = st.sidebar.file_uploader(
    "WhatsApp chat export (.txt)",
    type=["txt"],
    help="Android: Open group → three dots → More → Export chat → Without media\n"
         "iPhone: Open group → group name → Export chat → Without media"
)

# Sliders for parameters
min_msg_slider = st.sidebar.slider(
    "Minimum messages to include a member",
    min_value=1,
    max_value=20,
    value=config.MIN_MESSAGES_FOR_SCORING,
    help="Members with fewer messages than this will be categorized as inactive and skipped from leaderboard scoring."
)

n_topics_slider = st.sidebar.slider(
    "Number of topics to detect",
    min_value=2,
    max_value=8,
    value=5,
    help="Select how many distinct study topics LDA should search for in the chat text."
)

# Apply settings override to config dynamically
config.MIN_MESSAGES_FOR_SCORING = min_msg_slider

analyze_btn = st.sidebar.button("Analyze group", type="primary", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; color: #A0AEC0; font-size: 0.8rem;'>
    🔒 <b>Data Privacy Guarantee</b><br>
    Your chat data stays strictly inside this browser session on your local machine. 
    No internet servers are contacted.
</div>
""", unsafe_allow_html=True)

# Application Header in Main Area
st.markdown("<h1 class='app-title'>Group Ghost 👻</h1>", unsafe_allow_html=True)
st.markdown("<p class='app-subtitle'>Who actually contributes to this study group, and who just sends noise?</p>", unsafe_allow_html=True)

# Initialize Session State
if "chat_data" not in st.session_state:
    st.session_state.chat_data = None

# If user clicks "Analyze group", parse and trigger execution
if analyze_btn:
    if uploaded_file is not None:
        try:
            # Use temporary file helper to save uploader bytes to Path
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_path = temp_file.name

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # SECTION 2 — PROCESSING STATUS
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            with st.status("Analyzing WhatsApp group data locally...", expanded=True) as status:
                
                status.write("Step 1/5: Parsing chat export...")
                messages = parser.parse_chat(temp_path)
                status.update(label="Step 1/5 Completed! Parsing finished.", state="running")
                
                status.write("Step 2/5: Detecting topics with LDA...")
                token_lists = topic_analyzer.preprocess_for_lda(messages)
                topic_results = topic_analyzer.run_lda(token_lists, n_topics=n_topics_slider)
                # If LDA had fallback, include top academic keywords for the scorer/report
                if topic_results.get("fallback"):
                    topic_results["top_keywords"] = topic_analyzer.get_top_academic_keywords(messages)
                status.update(label="Step 2/5 Completed! Topic clustering finished.", state="running")
                
                status.write("Step 3/5: Running sentiment and scoring...")
                member_scores = scorer.score_all_members(messages, topic_results)
                status.update(label="Step 3/5 Completed! Member scoring completed.", state="running")
                
                status.write("Step 4/5: Building reply network...")
                edges = network_builder.detect_reply_chains(messages, window=3)
                network_html = network_builder.build_network_graph(edges, member_scores)
                status.update(label="Step 4/5 Completed! Interaction graph built.", state="running")
                
                status.write("Step 5/5: Generating timeline analysis...")
                peak_hours = timeline.get_peak_study_hours(messages)
                panic_days = timeline.get_exam_panic_days(messages)
                
                # Bundle everything into session state
                st.session_state.chat_data = {
                    "messages": messages,
                    "topic_results": topic_results,
                    "member_scores": member_scores,
                    "network_edges": edges,
                    "network_html_path": network_html,
                    "peak_hours": peak_hours,
                    "panic_days": panic_days,
                    "date_range": parser.get_date_range(messages),
                    "analysis_timestamp": datetime.now().isoformat()
                }
                status.update(label="Analysis 100% complete!", state="complete", expanded=False)
                
            # Clean up temp file safely
            try:
                Path(temp_path).unlink()
            except OSError:
                pass
                
        except Exception as e:
            st.error(f"❌ **Analysis Failed:** {str(e)}")
            st.exception(e)
    else:
        st.warning("⚠️ Please upload a WhatsApp chat export `.txt` file first.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DISPLAY RESULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if st.session_state.chat_data is not None:
    data = st.session_state.chat_data
    messages = data["messages"]
    member_scores = data["member_scores"]
    topic_results = data["topic_results"]
    edges = data["network_edges"]
    peak_hours = data["peak_hours"]
    panic_days = data["panic_days"]
    start_date, end_date = data["date_range"]
    
    total_messages = len(messages)
    active_count = len(member_scores)
    days_active = (end_date - start_date).days or 1
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 3 — SUMMARY METRICS ROW
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.markdown("### Executive Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Format display peak hours
    hour_labels = []
    for h in peak_hours:
        suffix = "PM" if h >= 12 else "AM"
        disp_h = h if h <= 12 else h - 12
        if disp_h == 0:
            disp_h = 12
        hour_labels.append(f"{disp_h} {suffix}")
    peak_hour_str = hour_labels[0] if hour_labels else "N/A"
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{total_messages:,}</div>
            <div class='metric-label'>Total Messages</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{active_count}</div>
            <div class='metric-label'>Active Contributors</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{days_active}</div>
            <div class='metric-label'>Days Analyzed</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{peak_hour_str}</div>
            <div class='metric-label'>Peak Study Hour</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.write("")
    
    # Dynamic text summary card
    star_members = [m["member"] for m in member_scores if m["label"] == "star"]
    stars_str = ", ".join(star_members[:3]) if star_members else "No single member"
    summary_text = (
        f"This study group has been active for **{days_active} days** (from {start_date} to {end_date}). "
        f"Study activity peaks at **{peak_hour_str}**. "
        f"**{stars_str}** carries the highest academic load as the star contributor of the group."
    )
    st.info(f"👻 **Group Ghost Summary:** {summary_text}")
    
    st.markdown("---")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 4 — LEADERBOARD & INDIVIDUAL CARDS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.subheader("🏆 Contributor Leaderboard")
    st.caption("Qualifying members ranked by overall academic contribution quality.")
    
    # Table column layout for leaderboard rows
    header_cols = st.columns([0.6, 2, 2.2, 1, 1, 1, 1, 1, 1.2])
    header_cols[0].markdown("**Rank**")
    header_cols[1].markdown("**Member**")
    header_cols[2].markdown("**Contributor Score**")
    header_cols[3].markdown("**Acad%**")
    header_cols[4].markdown("**Sent**")
    header_cols[5].markdown("**Topics**")
    header_cols[6].markdown("**Resp**")
    header_cols[7].markdown("**Noise**")
    header_cols[8].markdown("**Status**")
    
    st.markdown("<div style='margin-top: -10px; margin-bottom: 10px; border-bottom: 2px solid rgba(255,255,255,0.1);'></div>", unsafe_allow_html=True)
    
    for m in member_scores:
        row_cols = st.columns([0.6, 2, 2.2, 1, 1, 1, 1, 1, 1.2])
        
        # Rank and name
        row_cols[0].write(f"#{m['rank']}")
        row_cols[1].write(f"**{m['member']}**")
        
        # Progress bar representing score
        row_cols[2].progress(m["contributor_score"])
        
        # Metrics
        row_cols[3].write(f"{m['academic_signal_ratio'] * 100:.0f}%")
        row_cols[4].write(f"{m['sentiment_score']:.2f}")
        row_cols[5].write(f"{m['topic_contribution']:.2f}")
        row_cols[6].write(f"{m['response_behavior']:.2f}")
        row_cols[7].write(f"{m['noise_penalty']:.2f}")
        
        # Badge Label mapping
        badge_html = ""
        if m["label"] == "star":
            badge_html = "<span class='badge-star'>STAR</span>"
        elif m["label"] == "active":
            badge_html = "<span class='badge-active'>ACTIVE</span>"
        else:
            badge_html = "<span class='badge-lurker'>LURKER</span>"
            
        row_cols[8].markdown(badge_html, unsafe_allow_html=True)
        
        # Profile details inside expander underneath
        with st.expander(f"🔍 Expand Profile Card for {m['member']}"):
            card_col1, card_col2 = st.columns([2, 1])
            
            with card_col1:
                st.markdown(f"### Profile Scorecard: {m['member']}")
                
                # Metrics Row
                m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
                m_col1.metric("Academic Ratio", f"{m['academic_signal_ratio'] * 100:.1f}%")
                m_col2.metric("Sentiment Score", f"{m['sentiment_score']:.2f}")
                m_col3.metric("Topic Contribution", f"{m['topic_contribution']:.2f}")
                m_col4.metric("Response Rate", f"{m['response_behavior']:.2f}")
                m_col5.metric("Noise Penalty", f"{m['noise_penalty']:.2f}")
                
                # Fetch top topics
                st.write("")
                st.markdown("**Core Topic Influence:**")
                dist = topic_analyzer.get_member_topic_distribution(m["member"], messages, topic_results)
                if dist:
                    top_topics = sorted(dist.items(), key=lambda x: x[1], reverse=True)[:3]
                    topic_pills = " ".join([
                        f"<span style='background: rgba(43, 108, 176, 0.2); border: 1px solid rgba(43, 108, 176, 0.4); padding: 3px 8px; border-radius: 20px; font-size: 0.8rem; margin-right: 5px; color: #63B3ED;'>{lbl} ({val * 100:.0f}%)</span>" 
                        for lbl, val in top_topics
                    ])
                    st.markdown(topic_pills, unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:#718096;'>No topics linked to this user's contributions.</span>", unsafe_allow_html=True)
                
                # Plain English analysis
                st.write("")
                acad_desc = "predominantly academic content" if m['academic_signal_ratio'] > 0.6 else "a balanced mixture of learning and chat" if m['academic_signal_ratio'] > 0.3 else "mostly non-academic, administrative or chat contents"
                resp_desc = f"responds to over {m['response_behavior'] * 100:.0f}% of queries"
                noise_desc = "maintaining high clarity without spamming noise" if m['noise_penalty'] < 0.2 else "contributing substantial off-topic noise/memes"
                
                analysis_sentence = (
                    f"**{m['member']}** is ranked **#{m['rank']}** with a contributor index of **{m['contributor_score']:.2f}**. "
                    f"They send {acad_desc}, {resp_desc}, while {noise_desc}."
                )
                st.markdown(f"✍️ *{analysis_sentence}*")
                
            with card_col2:
                st.markdown("**Sample Academic Submissions:**")
                member_msgs = utils.get_member_messages(messages, m["member"])
                academic_samples = [
                    msg["message"] for msg in member_msgs 
                    if not msg["is_media"] and utils.contains_any(msg["message"], config.ACADEMIC_KEYWORDS)
                ][:3]
                
                if academic_samples:
                    for s in academic_samples:
                        # Truncate long messages for layout neatness
                        truncated = s[:100] + "..." if len(s) > 100 else s
                        st.markdown(f"> *\"{truncated}\"*")
                else:
                    st.markdown("<span style='color:#718096;'>No study sample texts found.</span>", unsafe_allow_html=True)
        
        st.markdown("<div style='border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 8px;'></div>", unsafe_allow_html=True)
        
    st.markdown("---")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 5 — REPLY NETWORK GRAPH
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.subheader("🕸️ Interaction & Reply Network")
    st.caption("Interactive graph mapping structural peer-to-peer replies. Node size corresponds to score, arrowheads show reply direction.")
    
    # Render interactive network graph HTML
    try:
        with open(data["network_html_path"], "r", encoding="utf-8") as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=520, scrolling=False)
    except Exception as e:
        st.warning(f"Unable to render Pyvis graph. Error details: {str(e)}")
        
    net_col1, net_col2 = st.columns(2)
    with net_col1:
        st.markdown("**Most Replied To (Authority/Leaders):**")
        most_replied = network_builder.get_most_replied_to(edges)[:5]
        for idx, (name, cnt) in enumerate(most_replied, 1):
            st.write(f"{idx}. **{name}** — received **{cnt}** replies")
            
    with net_col2:
        st.markdown("**Most Replies Given (Helpful Helpers):**")
        most_replies = network_builder.get_most_replies_given(edges)[:5]
        for idx, (name, cnt) in enumerate(most_replies, 1):
            st.write(f"{idx}. **{name}** — sent **{cnt}** replies")
            
    st.markdown("---")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 6 — TOPIC MAP
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.subheader("📚 Subject & Topic Analysis")
    
    if topic_results.get("fallback"):
        st.warning("⚠️ **Topic Modeling Notice:** Too few academic messages found for LDA. Showing keyword frequencies instead.")
        
        top_kws = topic_results.get("top_keywords", [])[:10]
        if top_kws:
            kw_df = pd.DataFrame(top_kws, columns=["Keyword", "Frequency"])
            fig_kw = px.bar(
                kw_df, 
                x="Keyword", 
                y="Frequency", 
                title="Top Academic Keyword Occurrences",
                color="Frequency",
                color_continuous_scale="Viridis",
                template="plotly_dark"
            )
            st.plotly_chart(fig_kw, use_container_width=True)
            
            # Show keyword list as pills
            st.markdown("**Prevalent study words found in text:**")
            pills = " ".join([f"<span style='background: rgba(29, 158, 117, 0.2); border: 1px solid rgba(29, 158, 117, 0.4); padding: 4px 10px; border-radius: 10px; font-size: 0.85rem; margin-right: 5px;'>{kw} ({cnt})</span>" for kw, cnt in top_kws])
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.info("No academic keywords detected in the chat log.")
            
    else:
        # Show topics in expandable UI cards
        topic_cols = st.columns(len(topic_results["topics"]))
        for idx, topic in enumerate(topic_results["topics"]):
            with topic_cols[idx]:
                st.markdown(f"""
                <div style='background: rgba(43, 108, 176, 0.15); border: 1px solid rgba(43, 108, 176, 0.3); padding: 15px; border-radius: 8px; height: 100%;'>
                    <h4 style='color: #63B3ED; margin-top:0;'>Topic #{topic['topic_id'] + 1}</h4>
                    <p style='font-size: 1.1rem; font-weight: bold; margin-bottom: 10px; color:#ffffff;'>{topic['label']}</p>
                    <p style='color:#CBD5E0; font-size:0.85rem; margin:0;'>{", ".join(topic['keywords'][:6])}</p>
                </div>
                """, unsafe_allow_html=True)
                
        st.write("")
        st.markdown("**Topic Share across Academic Conversations:**")
        
        # Calculate topic proportions across entire chat
        doc_topic_matrix = topic_results["doc_topic_matrix"]
        if doc_topic_matrix:
            mean_dist = pd.DataFrame(doc_topic_matrix).mean().tolist()
            labels = [t["label"] for t in topic_results["topics"]]
            
            topic_df = pd.DataFrame({"Topic": labels, "Average Share": mean_dist})
            fig_topic = px.pie(
                topic_df, 
                values="Average Share", 
                names="Topic", 
                title="Academic Theme Workload Proportions",
                color_discrete_sequence=px.colors.sequential.Plasma_r,
                template="plotly_dark"
            )
            fig_topic.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_topic, use_container_width=True)
            
    st.markdown("---")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 7 — TIMELINE ANALYSIS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.subheader("📅 Group Temporal Activity Patterns")
    
    time_col1, time_col2 = st.columns(2)
    
    with time_col1:
        # Hourly activity colored by academic ratio
        hr_counts = timeline.messages_by_hour(messages)
        hr_acads = timeline.academic_activity_by_hour(messages)
        
        hour_df = pd.DataFrame({
            "Hour of Day": list(hr_counts.keys()),
            "Total Messages": list(hr_counts.values()),
            "Academic Ratio": list(hr_acads.values())
        })
        
        # Formats for display X-axis
        hour_df["Hour Label"] = hour_df["Hour of Day"].apply(
            lambda x: f"{x if x <= 12 else x - 12} {'AM' if x < 12 else 'PM'}"
        )
        
        fig_hr = px.bar(
            hour_df, 
            x="Hour Label", 
            y="Total Messages", 
            color="Academic Ratio",
            color_continuous_scale="Viridis",
            title="Message Volumes by Hour (Colored by Academic Signal)",
            template="plotly_dark"
        )
        st.plotly_chart(fig_hr, use_container_width=True)
        
        # Display peak hours
        p_desc = ", ".join([hour_df.loc[hour_df["Hour of Day"] == ph, "Hour Label"].values[0] for ph in peak_hours])
        st.success(f"🟢 **Peak Study Hours (Highly Academic):** {p_desc}")
        
    with time_col2:
        # Weekday volume
        day_counts = timeline.messages_by_day(messages)
        day_df = pd.DataFrame({
            "Day of Week": list(day_counts.keys()),
            "Messages Count": list(day_counts.values())
        })
        
        fig_day = px.bar(
            day_df, 
            x="Day of Week", 
            y="Messages Count",
            title="Activity Volume by Day of the Week",
            color="Messages Count",
            color_continuous_scale="Plasma",
            template="plotly_dark"
        )
        st.plotly_chart(fig_day, use_container_width=True)
        
    # Date heat line with panic indicators
    st.write("")
    date_counts = timeline.messages_by_date(messages)
    
    if date_counts:
        date_df = pd.DataFrame({
            "Date": list(date_counts.keys()),
            "Message Count": list(date_counts.values())
        })
        date_df["Date"] = pd.to_datetime(date_df["Date"])
        
        fig_timeline = go.Figure()
        # Draw volume line
        fig_timeline.add_trace(go.Scatter(
            x=date_df["Date"], 
            y=date_df["Message Count"],
            mode='lines',
            name='Message Volume',
            line=dict(color='#FF8E53', width=2)
        ))
        
        # Add red markers for panic days
        if panic_days:
            panic_dates = pd.to_datetime(panic_days)
            panic_volumes = [date_counts.get(pd_str, 0) for pd_str in panic_days]
            
            fig_timeline.add_trace(go.Scatter(
                x=panic_dates,
                y=panic_volumes,
                mode='markers',
                name='Exam Panic Event',
                marker=dict(color='#E53E3E', size=12, symbol='triangle-up'),
                hovertext=[f"Panic Day: {pd_str}" for pd_str in panic_days]
            ))
            
        fig_timeline.update_layout(
            title="Chronological Conversation Volume Timeline",
            xaxis_title="Calendar Date",
            yaxis_title="Message Count per Day",
            template="plotly_dark",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        if panic_days:
            panic_str = ", ".join(panic_days)
            st.error(f"🚨 **Detected Exam Panic Dates:** {panic_str} (Double standard volumes + extremely high academic focus!)")
        else:
            st.info("ℹ️ **Exam Panic Analysis:** No specific exam panic anomalous spikes detected. Group maintains a steady cadence.")
            
    st.markdown("---")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 8 — DOWNLOADS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.subheader("💾 Export & Report Offline Sync")
    st.caption("Download structured results instantly in standard formats. Runs fully locally.")
    
    dl_col1, dl_col2 = st.columns(2)
    
    with dl_col1:
        # JSON bundle
        json_output = {
            "metadata": {
                "date_range": [start_date.isoformat(), end_date.isoformat()],
                "total_messages": total_messages,
                "active_members_scored": active_count,
                "analysis_timestamp": data["analysis_timestamp"]
            },
            "leaderboard": member_scores,
            "topic_analysis": {
                "topics": topic_results.get("topics", []),
                "fallback_active": topic_results.get("fallback", False),
                "top_academic_keywords": topic_results.get("top_keywords", [])
            },
            "timeline": {
                "peak_study_hours": peak_hours,
                "exam_panic_days": panic_days,
                "volume_by_date": date_counts
            },
            "reply_network_edges": edges
        }
        
        json_string = json.dumps(json_output, indent=2)
        st.download_button(
            label="Download Complete JSON Analysis",
            data=json_string,
            file_name=config.OUTPUT_JSON_PATH,
            mime="application/json",
            use_container_width=True
        )
        
    with dl_col2:
        # PDF compilation triggering
        try:
            # Bundle data for timeline pdf structures
            timeline_pdf_bundle = {
                "peak_hours": peak_hours,
                "panic_days": panic_days,
                "most_replied_to": network_builder.get_most_replied_to(edges),
                "most_replies_given": network_builder.get_most_replies_given(edges)
            }
            
            with st.spinner("Compiling ReportLab PDF Locally..."):
                pdf_path = report_generator.generate_pdf_report(
                    member_scores=member_scores,
                    topic_results=topic_results,
                    timeline_data=timeline_pdf_bundle,
                    network_edges=edges,
                    date_range=(start_date, end_date),
                    output_path=config.OUTPUT_PDF_PATH
                )
                
            with open(pdf_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
                
            st.download_button(
                label="Download Formatted PDF Report",
                data=pdf_bytes,
                file_name=config.OUTPUT_PDF_PATH,
                mime="application/pdf",
                use_container_width=True
            )
            
        except Exception as e:
            st.error(f"Could not build PDF Report. Error: {str(e)}")
            st.exception(e)

# Group Ghost 👻 — Study Group Intelligence Suite

🚀 **Live Secure Web App:** [https://construction-rider-lone-compressed.trycloudflare.com](https://construction-rider-lone-compressed.trycloudflare.com)

Group Ghost is a production-grade, 100% local WhatsApp study group analyzer that answers the core question: **"Who actually contributes to this study group, and who just sends noise?"** 

By processing chat exports, it evaluates each member across five distinct dimensions—Academic Signal Ratio, Sentiment Score, Topic Contribution, Response Behavior, and Noise/Meme Penalty—combining them into a single comprehensive **Contributor Score**.

The entire tool runs completely on-device. Your chat data never leaves your computer, requires no internet connection, and uses zero paid APIs or cloud dependencies.

---

## 📱 How to Export Your WhatsApp Chat

Follow these instructions exactly to export your chat as a `.txt` file:

### Android:
1. Open the WhatsApp study group.
2. Tap the **three dots** in the top-right corner.
3. Tap **More** → **Export chat**.
4. Select **Without media** (mandatory).
5. Save the resulting `.txt` file to your device or transfer it to your laptop.

### iPhone:
1. Open the WhatsApp study group.
2. Tap the **group name/header** at the top of the screen.
3. Scroll down and tap **Export chat**.
4. Select **Without media** (mandatory).
5. Tap **Save to Files** to save it as a `.txt` file.

---

## 🛠️ Installation & One-Time Setup

Make sure you have Python 3.10+ installed.

### 1. Install Dependencies
Navigate to the project folder and run:
```bash
pip install -r requirements.txt
```

### 2. Download Local Models
Group Ghost uses local, lightweight language models for NLP. Run these one-time download commands:
```bash
# Download local Spacy English tokenizer (12MB)
python -m spacy download en_core_web_sm

# Download VADER Sentiment lexicon
python -c "import nltk; nltk.download('vader_lexicon')"
```

---

## 🚀 How to Run the App

Launch the local interactive Streamlit server:
```bash
streamlit run main.py
```

Streamlit will automatically open a browser window at `http://localhost:8501`. 
Simply upload your exported WhatsApp `.txt` file, customize the filters in the sidebar, and hit **Analyze group**!

---

## 📊 Folder Structure Explanation

The application is structured into modular, single-responsibility files for cleanPair pair-programming and robust engineering:

```
group_ghost/
├── main.py              # Streamlit UI Dashboard & visualization entry point
├── parser.py            # Custom regex engine for parsing multi-format WhatsApp exports
├── scorer.py            # 5-dimension scoring and Contributor Score compilation
├── topic_analyzer.py    # Local Spacy processing + Sklearn LDA topic modeling
├── network_builder.py   # Reply-chain calculation & interactive Pyvis graph compiler
├── timeline.py          # Temporal hourly, daily, and anomalous date analytics
├── report_generator.py  # Page-budgeted ReportLab PDF report compiler
├── config.py            # Concentrated keywords, weights, and file configs
├── utils.py             # Shared text cleansers, normalizers, and JSON/file helpers
├── requirements.txt     # Locked project dependencies
└── README.md            # Setup guidelines, export steps, and manual
```

---

## 💡 What the Outputs Mean

### A) Contributor Leaderboard
Ranks members by their final **Contributor Score** (0.0 to 1.0). Members are classified into:
*   **Star (Score > 0.7):** Members who drive high academic conversations, frequently answer questions, and introduce topics.
*   **Active (Score 0.4 - 0.7):** Reliable members who participate balanced between study-talk and casual discussions.
*   **Lurker (Score <= 0.4):** Members who post very little study value or focus heavily on noise/off-topic.
*   *Note:* Members with fewer than 5 messages are skipped from scoring to avoid ranking bias.

### B) Interaction & Reply Network
An interactive network graph showing who replies to whom. Node sizes correspond to the Contributor Score. The thickness of connection lines represents how frequently one member replies to another. High-indegree members act as authorities/leaders.

### C) Subject & Topic Analysis
Runs Latent Dirichlet Allocation (LDA) mathematical modeling on study messages to group conversations into thematic topics. Shows what subjects dominated (e.g. "EXAMS & PAPERS", "PRACTICALS & LABS").

### D) Temporal Activity heatmap
Highlights when the group is active:
*   **Peak Study Hours:** Hours of the day where academic signal ratio peaks.
*   **Exam Panic Days:** Specific calendar dates where message volume was over 2x the group average AND the conversations were over 50% academic.

### E) PDF & JSON Exports
Download a comprehensive, formatted, multi-page PDF report with cover page and sorted tables for offline sharing, or grab the raw JSON data containing all calculated metrics.

---

## 🔒 Complete Local Privacy

Group Ghost is designed with absolute confidentiality in mind:
*   **Zero Internet Connections:** Once setup is complete, you can completely disconnect your Wi-Fi.
*   **Zero Database Footprints:** Data is parsed directly into the local dashboard memory.
*   **On-Device Models:** NLP (Spacy), Sentiment (VADER), and Topic Modeling (Sklearn) execute 100% locally.

---

## ⚠️ Known Limitations & Edge Cases

*   **Group Names vs Phone Numbers:** If a member is not saved in the contact list of the exporter, WhatsApp exports their phone number (e.g., `+91 99999 99999`). Group Ghost parses phone numbers as their display name automatically.
*   **Mixed Hinglish Language:** The system supports both English and Hinglish words. If messages contain mixed languages, the English/Hinglish keywords will be matched, but complex grammar sentences will rely on clean English chunks for sentiment parsing.
*   **Single-Member Groups:** If the chat has only one member, the reply network is skipped since no interactions are possible.
*   **LDA Fallback:** If a group chat has fewer than 10 highly academic messages, LDA modeling is skipped, and Group Ghost displays a fallback top academic keyword frequency chart instead.

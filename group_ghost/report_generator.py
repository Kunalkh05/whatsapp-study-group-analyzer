"""
Generates a highly structured, professional, multi-page PDF report 
summarizing study group metrics, leaderboard, topic map, timeline, and network relationships.
Uses ReportLab for fully local PDF rendering.
"""

from pathlib import Path
from datetime import date
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

import config

def generate_pdf_report(member_scores: list[dict],
                        topic_results: dict,
                        timeline_data: dict,
                        network_edges: list[dict],
                        date_range: tuple[date, date],
                        output_path: str) -> str:
    """
    Generates a 5-page localized PDF analysis report using ReportLab Flowables.
    
    Args:
        member_scores (list[dict]): Scored and ranked group members.
        topic_results (dict): Topic model results from topic_analyzer.
        timeline_data (dict): Peak hours, calendar counts, panic days.
        network_edges (list[dict]): Parsed social network edges.
        date_range (tuple[date, date]): Earliest and latest date of chat history.
        output_path (str): Filepath to write the finished PDF report.
        
    Returns:
        str: Absolute path of the generated PDF.
    """
    pdf_file = Path(output_path)
    
    # Page setup - Standard letter size with 0.75 in (54 points) margins
    doc = SimpleDocTemplate(
        str(pdf_file),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom high-premium style palette
    primary_color = colors.HexColor("#1A365D")   # Dark Navy
    secondary_color = colors.HexColor("#2B6CB0") # Steel Blue
    text_color = colors.HexColor("#2D3748")      # Charcoal
    accent_green = colors.HexColor("#1D9E75")    # Emerald Star
    accent_amber = colors.HexColor("#EF9F27")    # Amber Active
    accent_gray = colors.HexColor("#718096")     # Slate Lurker
    
    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=32,
        leading=38,
        textColor=primary_color,
        spaceAfter=15,
        alignment=1 # Centered
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=16,
        leading=22,
        textColor=secondary_color,
        spaceAfter=50,
        alignment=1 # Centered
    )
    
    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=26,
        textColor=primary_color,
        spaceAfter=15,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=secondary_color,
        spaceBefore=10,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_color,
        spaceAfter=10
    )
    
    table_text_style = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=text_color
    )
    
    table_header_style = ParagraphStyle(
        'TableHeaderText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )
    
    meta_label_style = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=primary_color
    )
    
    meta_val_style = ParagraphStyle(
        'MetaValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        textColor=text_color
    )

    story = []
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PAGE 1: COVER
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    story.append(Spacer(1, 100))
    # Elegant graphic accent
    title_bar = Table([[""]], colWidths=[504], rowHeights=[6])
    title_bar.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), primary_color),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(title_bar)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("GROUP GHOST", title_style))
    story.append(Paragraph("Study Group Contributor Scorecard & Analysis", subtitle_style))
    
    story.append(Spacer(1, 60))
    
    # Metadata Box
    total_messages = sum(m["total_messages"] for m in member_scores)
    start_date, end_date = date_range
    
    meta_data = [
        [Paragraph("Date Range:", meta_label_style), Paragraph(f"{start_date} to {end_date}", meta_val_style)],
        [Paragraph("Total Active Members:", meta_label_style), Paragraph(str(len(member_scores)), meta_val_style)],
        [Paragraph("Total Analyzed Messages:", meta_label_style), Paragraph(f"{total_messages:,}", meta_val_style)],
        [Paragraph("Generation Date:", meta_label_style), Paragraph(str(date.today()), meta_val_style)],
        [Paragraph("Privacy Framework:", meta_label_style), Paragraph("100% Local Compliance (Zero Cloud Outflow)", meta_val_style)]
    ]
    
    meta_table = Table(meta_data, colWidths=[180, 324])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
        ('PADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#EDF2F7")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    
    story.append(Spacer(1, 100))
    story.append(Paragraph("<font color='#718096'>Report generated completely on-device. Group Ghost AI 👻</font>", ParagraphStyle('CenterText', parent=body_style, alignment=1)))
    story.append(PageBreak())
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PAGE 2: LEADERBOARD TABLE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    story.append(Paragraph("Contributor Leaderboard", h1_style))
    story.append(Paragraph(
        "Members are graded based on their net contribution quality. Senders are skipped if they don't meet "
        f"the active threshold of at least {config.MIN_MESSAGES_FOR_SCORING} messages.",
        body_style
    ))
    
    # Table headers
    headers = ["Rank", "Member", "Score", "Acad %", "Sent", "Topics", "Resp", "Noise", "Label"]
    table_data = [[Paragraph(h, table_header_style) for h in headers]]
    
    for m in member_scores:
        lbl = m["label"]
        if lbl == "star":
            lbl_color = "#1D9E75"
        elif lbl == "active":
            lbl_color = "#EF9F27"
        else:
            lbl_color = "#718096"
            
        lbl_text = f"<b><font color='{lbl_color}'>{lbl.upper()}</font></b>"
        
        row = [
            Paragraph(str(m["rank"]), table_text_style),
            Paragraph(m["member"], table_text_style),
            Paragraph(f"{m['contributor_score']:.2f}", table_text_style),
            Paragraph(f"{m['academic_signal_ratio'] * 100:.1f}%", table_text_style),
            Paragraph(f"{m['sentiment_score']:.2f}", table_text_style),
            Paragraph(f"{m['topic_contribution']:.2f}", table_text_style),
            Paragraph(f"{m['response_behavior']:.2f}", table_text_style),
            Paragraph(f"{m['noise_penalty']:.2f}", table_text_style),
            Paragraph(lbl_text, table_text_style)
        ]
        table_data.append(row)
        
    lead_table = Table(table_data, colWidths=[35, 95, 45, 50, 45, 50, 45, 45, 95])
    lead_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    
    story.append(lead_table)
    story.append(PageBreak())
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PAGE 3: TOPIC MAP
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    story.append(Paragraph("Academic Topics Map", h1_style))
    
    if topic_results.get("fallback"):
        story.append(Paragraph(
            "<b>Note on topic modeling fallback:</b> There were too few highly academic messages in the chat log "
            "to perform standard Latent Dirichlet Allocation (LDA) mathematical modeling. The system has "
            "successfully fallen back to counting the occurrences of predefined academic keywords instead.",
            body_style
        ))
        
        story.append(Spacer(1, 10))
        story.append(Paragraph("Top Prevalent Academic Keywords", h2_style))
        
        kw_headers = ["Rank", "Academic Keyword", "Occurrences in Chat"]
        kw_data = [[Paragraph(h, table_header_style) for h in kw_headers]]
        
        top_kws = topic_results.get("top_keywords", [])[:15]
        for rank, (kw, count) in enumerate(top_kws, 1):
            kw_data.append([
                Paragraph(str(rank), table_text_style),
                Paragraph(kw, table_text_style),
                Paragraph(str(count), table_text_style)
            ])
            
        kw_table = Table(kw_data, colWidths=[60, 240, 204])
        kw_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(kw_table)
        
    else:
        story.append(Paragraph(
            "These represent the core thematic academic topics detected automatically in your study group via "
            "unsupervised Latent Dirichlet Allocation (LDA). They showcase what subjects dominated the conversations.",
            body_style
        ))
        
        story.append(Spacer(1, 10))
        
        topic_headers = ["Topic ID", "Topic Automated Title", "Core Structural Keywords"]
        topic_data = [[Paragraph(h, table_header_style) for h in topic_headers]]
        
        for topic in topic_results.get("topics", []):
            keywords_str = ", ".join(topic["keywords"])
            row = [
                Paragraph(f"Topic {topic['topic_id'] + 1}", table_text_style),
                Paragraph(topic["label"], ParagraphStyle('TopicLabel', parent=table_text_style, fontName='Helvetica-Bold', textColor=secondary_color)),
                Paragraph(keywords_str, table_text_style)
            ]
            topic_data.append(row)
            
        topic_table = Table(topic_data, colWidths=[70, 150, 284])
        topic_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('PADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(topic_table)
        
    story.append(PageBreak())
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PAGE 4: ACTIVITY & TIMELINE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    story.append(Paragraph("Timeline & Activity Insights", h1_style))
    story.append(Paragraph(
        "Understanding when the group is most active allows planners and educators to know when questions "
        "are answered quickest and when study collaboration reaches its highest threshold.",
        body_style
    ))
    
    # Peak Hours Table
    story.append(Paragraph("Peak Study Hours", h2_style))
    story.append(Paragraph("These hours of the day represent when the academic signal ratio (the percentage of study-related messages) is at its maximum:", body_style))
    
    peak_hours = timeline_data.get("peak_hours", [])
    hour_desc = []
    for h in peak_hours:
        am_pm = "AM" if h < 12 else "PM"
        display_h = h if h <= 12 else h - 12
        if display_h == 0:
            display_h = 12
        hour_desc.append(f"<b>{display_h} {am_pm}</b>")
        
    hours_string = ", ".join(hour_desc) if hour_desc else "No specific peak study hours met the message count threshold."
    
    hour_table_data = [[
        Paragraph("Peak Academic Activity Hour Window", table_header_style),
        Paragraph("Status", table_header_style)
    ], [
        Paragraph(hours_string, table_text_style),
        Paragraph("<font color='#1D9E75'><b>HIGH SIGNAL</b></font>", table_text_style)
    ]]
    hour_table = Table(hour_table_data, colWidths=[384, 120])
    hour_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), secondary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(hour_table)
    
    # Exam Panic Days Section
    story.append(Spacer(1, 20))
    story.append(Paragraph("Exam Panic Days", h2_style))
    story.append(Paragraph(
        "Exam Panic Days represent highly specific, anomalies in the calendar. These are dates where message volume spikes "
        "to at least <b>double</b> the group average, AND the conversation is predominantly academic (academic signal ratio > 0.5).",
        body_style
    ))
    
    panic_days = timeline_data.get("panic_days", [])
    if panic_days:
        panic_headers = ["No.", "Date of Panic Event", "Thematic Classification"]
        panic_table_data = [[Paragraph(ph, table_header_style) for ph in panic_headers]]
        
        for idx, p_day in enumerate(panic_days, 1):
            panic_table_data.append([
                Paragraph(str(idx), table_text_style),
                Paragraph(p_day, table_text_style),
                Paragraph("<b><font color='#E53E3E'>EXAM PANIC DETECTED</font></b>", table_text_style)
            ])
            
        panic_table = Table(panic_table_data, colWidths=[50, 200, 254])
        panic_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#FFF5F5")]), # Light pink background for panic
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#FED7D7")),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(panic_table)
    else:
        story.append(Paragraph("<i>No specific 'Exam Panic' dates detected. The group has maintained a stable or non-deviant study workload distribution.</i>", body_style))
        
    story.append(PageBreak())
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PAGE 5: INTERACTIONS & REPLY NETWORK
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    story.append(Paragraph("Interactions & Reply Network", h1_style))
    story.append(Paragraph(
        "By parsing chronological reply chains, Group Ghost analyzes who anchors the group’s social hierarchy. "
        "Below are the leaders in incoming queries answered and outgoing assistance provided.",
        body_style
    ))
    
    most_replied_to = timeline_data.get("most_replied_to", [])[:5]
    most_replies_given = timeline_data.get("most_replies_given", [])[:5]
    
    col1_data = [
        [Paragraph("Member (Replied To)", table_header_style), Paragraph("Replies Received", table_header_style)]
    ]
    for member, count in most_replied_to:
        col1_data.append([Paragraph(member, table_text_style), Paragraph(str(count), table_text_style)])
        
    col2_data = [
        [Paragraph("Member (Repliers)", table_header_style), Paragraph("Replies Sent", table_header_style)]
    ]
    for member, count in most_replies_given:
        col2_data.append([Paragraph(member, table_text_style), Paragraph(str(count), table_text_style)])
        
    # Wrap in tables
    table1 = Table(col1_data, colWidths=[160, 80])
    table1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), secondary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    
    table2 = Table(col2_data, colWidths=[160, 80])
    table2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), secondary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    
    # Outer side-by-side layout
    outer_data = [[table1, "", table2]]
    outer_table = Table(outer_data, colWidths=[240, 24, 240])
    outer_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(Paragraph("Social Hierarchy Tables", h2_style))
    story.append(outer_table)
    
    # Conclusion note
    story.append(Spacer(1, 40))
    story.append(Paragraph("Analysis Conclusion", h2_style))
    story.append(Paragraph(
        "Study groups thrive on peer support. Highly scored members act as 'Stars' by addressing queries, sharing materials, "
        "and reducing off-topic chatter. Conversely, high-noise members can dilute academic value. Use these metrics to encourage "
        "better structural peer-to-peer accountability inside your classroom or group study sessions.",
        body_style
    ))
    
    # Build document
    doc.build(story)
    return str(pdf_file.absolute())

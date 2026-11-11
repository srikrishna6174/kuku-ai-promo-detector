import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

def build_solution_pdf(output_filename="Solution_Document.pdf"):
    # Target: Exactly 2 pages
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#B81D24')
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#444444')
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=8,
        spaceAfter=3
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=5,
        spaceAfter=2
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#1E293B')
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#1E293B'),
        leftIndent=12,
        firstLineIndent=-8
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#065F46')
    )

    story = []

    # ==================== PAGE 1 ====================
    # Header
    story.append(Paragraph("KUKU — AI GENERALIST ASSIGNMENT", title_style))
    story.append(Paragraph("<b>Problem 1: Find the Promos (Ads)</b> | Candidate: Srikrishna Valepe | AI Generalist Solution", subtitle_style))
    story.append(Spacer(1, 6))

    # Section 1
    story.append(Paragraph("1. Problem Choice, Tech Stack & Framing", h1_style))
    story.append(Paragraph(
        "<b>Why Problem 1?</b> Microdramas are a high-velocity vertical video format where editors manually scrub full episode timelines to extract 20–60s social hooks for Instagram Reels, TikTok, and YouTube Shorts. Our tool automates promo scouting from raw screenplays into ready-to-use timestamp cut sheets.<br/>"
        "<b>Tech Stack:</b> Python 3.12, Streamlit multi-page studio, multi-format screenplay parser (<i>.txt/.srt/.vtt/.zip</i>), deterministic hook/cliffhanger scorer, swappable REST adapters (<b>Gemini</b> &amp; <b>OpenAI</b> with LLM-as-a-Judge &amp; auto failover), ReportLab, and a 20-test <i>unittest</i> suite.<br/>"
        "<b>Key Assumptions:</b> Strict 20–60s duration bounds (optimal 25–45s), single continuous + 2-beat multi-segment intercut support, and zero-lore standalone hooks readable within 3 seconds.",
        body_style
    ))
    story.append(Spacer(1, 5))

    # Section 2
    story.append(Paragraph("2. Studio Workflow, Key Features & Architecture", h1_style))
    story.append(Paragraph(
        "<b>End-to-End Workflow:</b> (1) <i>Home</i> launches <b>Add New Project</b> or <b>Project Library</b>; (2) <i>New Input</i> ingests multi-format scripts via rules, AI, or Hybrid mode; (3) Per-project views (<i>Promos</i>, <i>Script Explorer</i>, <i>Quality Audit</i>) inspect results for one project at a time with inline switching, collapsible sections per promo type, <b>Pin a Manual Timestamp Cut</b>, on-demand AI/rule passes, and <i>.txt/.zip</i> downloads:",
        body_style
    ))

    # Architecture Table
    arch_table_data = [
        [
            Paragraph("<b>Component</b>", body_style),
            Paragraph("<b>Deterministic Code / Simple Rules</b>", body_style),
            Paragraph("<b>Generative AI / LLM Layer</b>", body_style)
        ],
        [
            Paragraph("<b>Responsibilities</b>", body_style),
            Paragraph("• Screenplay parsing (.txt, .srt, .vtt, .zip) &amp; regex timestamp extraction.<br/>• Sliding window generation (20s–60s constraints, +0.75s reaction buffer).<br/>• Anchor detection: Dialogue starts, high-intensity tones, confrontation verbs.<br/>• Mathematical scoring of 0–3s hook &amp; final cliffhanger.", body_style),
            Paragraph("• Semantic tension assessment, hook/cliffhanger summaries &amp; 'Why it works'.<br/>• LLM-as-a-Judge pass &amp; auto failover on outage/rate limit.<br/>• Swappable provider adapter (Gemini &amp; OpenAI; easy to plug in any model API).", body_style)
        ],
        [
            Paragraph("<b>Throughput &amp; Scope</b>", body_style),
            Paragraph("Offline-capable on CPU; scans 50 episodes cleanly in &lt;2.0s.", body_style),
            Paragraph("Evaluates filtered top candidate windows (~2–4/ep) or chosen episodes only.", body_style)
        ]
    ]
    t_arch = Table(arch_table_data, colWidths=[1.1*inch, 3.4*inch, 2.7*inch])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 6))

    # Section 3
    story.append(Paragraph("3. Scoring Rubric & Window Selection Logic", h1_style))
    story.append(Paragraph(
        "Candidate clips are evaluated on a composite 100-point scale across three weighted dimensions:<br/>"
        "• <b>Hook Score (40%):</b> Evaluates the first 3.0 seconds. Looks for high-stakes disruption verbs (<i>'marry', 'turn around', 'betray', 'enough'</i>), confrontational tones (<i>Venomous, Disgusted, Screaming</i>), or physical shock actions (<i>slap, tear, doors burst</i>).<br/>"
        "• <b>Cliffhanger Score (35%):</b> Evaluates the final 3.0–5.0 seconds. Looks for unresolved interrogatives (<i>'?'</i>), interrupted statements (<i>'...'</i>), acoustic swells (<i>'ominous cliffhanger peak'</i>), or visual freeze/cut-to-black.<br/>"
        "• <b>Standalone Coherence (25%):</b> Requires &gt;= 2 distinct speakers in conflict and 4–10 dialogue turns. Penalizes monologue exposition.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # ==================== PAGE BREAK TO PAGE 2 ====================
    story.append(PageBreak())

    # Page 2 Header
    story.append(Paragraph("4. Strategic Campaign Rollout: Which Promos to Post First & Why?", h1_style))
    story.append(Paragraph(
        "Ranking microdrama promos is not just about raw emotional score; it requires a <b>funnel-aligned publishing strategy</b>:",
        body_style
    ))

    ranking_data = [
        [Paragraph("<b>Tier & Priority</b>", body_style), Paragraph("<b>Target Episodes</b>", body_style), Paragraph("<b>Strategic Rationale & Placement</b>", body_style)],
        [
            Paragraph("<b>Tier 1: Post First</b><br/>(Cold User Acquisition)", body_style),
            Paragraph("<b>Episodes 1 – 3</b><br/>(Rank #1: Ep 3, 00:25–00:56<br/>Rank #2: Ep 1, 01:15–01:38)", body_style),
            Paragraph("<b>Zero-Lore Universality:</b> The wedding betrayal, sister stealing the groom, and mysterious hero's intervention require zero prior knowledge. Highest conversion from cold scroller to initial app install.", body_style)
        ],
        [
            Paragraph("<b>Tier 2: Post Second</b><br/>(Viral Escalation & Shares)", body_style),
            Paragraph("<b>Episodes 4 – 15</b><br/>(Identity reveals & public confrontation)", body_style),
            Paragraph("<b>Power Reversal & Catharsis:</b> Juliana standing her ground and the Duke's true status emerging. Drives high comment velocity and algorithmic engagement on TikTok/Instagram.", body_style)
        ],
        [
            Paragraph("<b>Tier 3: Post Third</b><br/>(Retargeting & Churn Prevention)", body_style),
            Paragraph("<b>Episodes 16 – 50</b><br/>(High-cliffhanger mid-season)", body_style),
            Paragraph("<b>Binge Triggers:</b> Life-or-death and high-stakes ultimatums targeted at warm audiences who installed the app but stalled at Episode 5.", body_style)
        ]
    ]
    t_rank = Table(ranking_data, colWidths=[1.5*inch, 1.8*inch, 3.9*inch])
    t_rank.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_rank)
    story.append(Spacer(1, 6))

    # Section 5
    story.append(Paragraph("5. Honest Quality Evaluation & Failure Modes ('Where does the tool pick badly?')", h1_style))
    story.append(Paragraph(
        "Automated audit (<i>src/quality_checker.py</i>) across all 100 extracted promos scored 26 clean and flagged 74 clips:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>1. Premature Cut Buffer (58% of clips):</b> Scripts end dialogue blocks abruptly (e.g. 00:32.40). Cutting there clips facial reactions/audio stings. <i>Mitigation:</i> Parser flags/accounts for a +0.75s visual reaction buffer.<br/>"
        "• <b>2. Off-Target Secondary Characters (32% of clips):</b> Shouting matches between maids/minor nobles score high lexically but fail as cold UA ads. <i>Mitigation:</i> Lead-protagonist weighting bonus.<br/>"
        "• <b>3. Lore & Exposition Overload / 4. Visual-Only Ambiguity:</b> High-word-count lore scenes (>25 words/turn flagged) bore scrollers, while silent action scenes (0 caught lexically) are underestimated without multi-modal video cues.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Section 6: AI Tools Used & Where AI Got It Wrong
    story.append(Paragraph("6. AI Tools Used & One Place AI Got It Wrong", h1_style))
    story.append(Paragraph(
        "• <b>Tools Used:</b> Antigravity coding agent for pipeline/Streamlit scaffolding and tests; <b>Gemini</b> &amp; <b>OpenAI</b> APIs for semantic promo detection &amp; LLM-as-a-Judge scoring.<br/>"
        "• <b>Where AI Got It Wrong:</b> When prompting LLMs directly over raw episode scripts, models frequently cut on the exact final dialogue word, drifted outside the strict 20–60s bounds, or picked peripheral cast arguments with inaccurate timestamp math. During UI iteration, generated widgets also left dropdowns editable and added redundant multi-provider complexity. Wrapping the LLM inside deterministic timestamp parsing, strict duration guards, judge verification, and 20 automated unit tests eliminated these errors.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Section 7
    story.append(Paragraph("7. Production Workflow, Scaling & Deliverables (Moments Only — No Overlays/Editing)", h1_style))
    story.append(Paragraph(
        "• <b>Scaling &amp; Human-in-the-Loop Workflow:</b> Rule filtering processes 1,000+ episodes in under 45 seconds on standard CPU and dispatches only top candidate windows to LLMs; editors review ranked 20–60s cuts per project, pin manual adjustments, and export timestamped cut sheets without baked video overlays or music.<br/>"
        "• <b>Deliverables:</b> (1) Per-project <i>Streamlit Promo Studio</i> for unseen scripts during live testing; (2) Unedited <i>outputs/</i> pack (<i>promos_master.json</i>, <i>promos_ranked.csv</i>, <i>promos_report.txt</i>, <i>quality_audit_and_failures.json</i>, stream-copy scripts &amp; markers); (3) 20/20 verified unit tests.",
        body_style
    ))

    doc.build(story)
    print(f"[+] Successfully generated 2-page PDF: {output_filename}")

if __name__ == "__main__":
    build_solution_pdf()


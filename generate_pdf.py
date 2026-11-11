import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

def build_solution_pdf(output_filename="Solution_Document.pdf"):
    # Target: Exactly 2 pages
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=32
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#B81D24')
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#444444')
    )

    banner_style = ParagraphStyle(
        'LiveBanner',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#0F172A')
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=6,
        spaceAfter=2
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1E293B')
    )

    story = []

    # ==================== PAGE 1 ====================
    # Header
    story.append(Paragraph("KUKU — AI GENERALIST ASSIGNMENT", title_style))
    story.append(Paragraph("<b>Problem 1: Find the Promos (Ads)</b> | Candidate: Srikrishna Valepe | AI Generalist Solution", subtitle_style))
    story.append(Spacer(1, 4))

    # Live Deployment & Repo Links Banner
    banner_data = [[
        Paragraph(
            "<b>Live Prototype URL:</b> <font color='#0284C7'><u>https://kuku-promo-detector.onrender.com</u></font> &nbsp;|&nbsp; "
            "<b>GitHub Repo:</b> <font color='#0284C7'><u>https://github.com/srikrishna6174/kuku-ai-promo-detector</u></font><br/>"
            "<b>Status:</b> Deployed &amp; Live on Render Cloud &bull; 20/20 Passing Automated Unit Tests &bull; Multi-Format Universal Parser &bull; Multi-LLM Failover",
            banner_style
        )
    ]]
    t_banner = Table(banner_data, colWidths=[7.3*inch])
    t_banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F0FDF4')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#22C55E')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_banner)
    story.append(Spacer(1, 5))

    # Section 1: Problem Choice & How It Works
    story.append(Paragraph("1. Problem Choice, Framing & How the Project Works", h1_style))
    story.append(Paragraph(
        "<b>Why Problem 1?</b> Microdramas are a high-velocity vertical video format where editors manually scrub 50+ episode timelines to find 20–60s hooks for TikTok, IG Reels, and YouTube Shorts. Our production tool automates promo scouting from raw screenplays into exact timestamp cut sheets with zero hallucination.<br/>"
        "<b>How It Works End-to-End:</b><br/>"
        "<b>1. Ingestion:</b> Universal parser accepts `.txt`, `.srt`, `.vtt`, or zip archives of raw screenplays, normalizing dialogue cues, character names, and millisecond timestamps.<br/>"
        "<b>2. Deterministic Candidate Windows:</b> Sliding window generator extracts valid scene boundaries conforming strictly to 20s–60s duration constraints with +0.75s post-dialogue visual reaction buffer.<br/>"
        "<b>3. Multi-Tier Detection Engine:</b> Evaluates clips through 3 modes: (a) <i>Deterministic Rules</i> (0–3s hook disruption, conflict escalation, final cliffhanger peak); (b) <i>Generative AI</i> (semantic tension, dialogue punchline, 'Why it works' rationale); (c) <i>Hybrid</i> (LLM-as-a-Judge validation + auto failover between Gemini &amp; OpenAI).<br/>"
        "<b>4. Editor Studio:</b> Editors review collapsible promo categories, adjust/pin custom manual timestamp cuts, and export clean cut sheets, Premiere/FCP marker CSVs, and lossless FFmpeg stream-copy scripts.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Section 2: Architecture Table
    story.append(Paragraph("2. Architectural Division: Deterministic Rules vs Generative AI", h1_style))
    arch_table_data = [
        [
            Paragraph("<b>Component</b>", body_style),
            Paragraph("<b>Deterministic Code / Simple Rules</b>", body_style),
            Paragraph("<b>Generative AI / LLM Layer</b>", body_style)
        ],
        [
            Paragraph("<b>Responsibilities</b>", body_style),
            Paragraph("• Screenplay parsing (.txt, .srt, .vtt, .zip) &amp; timestamp extraction.<br/>• Sliding window generation (20s–60s bounds, +0.75s reaction buffer).<br/>• Anchor detection: Dialogue starts, high-intensity tones, confrontation verbs.<br/>• Mathematical scoring of 0–3s hook &amp; final cliffhanger.", body_style),
            Paragraph("• Semantic tension assessment, hook/cliffhanger summaries &amp; 'Why it works'.<br/>• LLM-as-a-Judge pass &amp; auto failover on outage/rate limit.<br/>• Swappable provider adapter (Gemini &amp; OpenAI; pluggable REST APIs).", body_style)
        ],
        [
            Paragraph("<b>Throughput &amp; Scope</b>", body_style),
            Paragraph("Offline-capable on CPU; scans 50 episodes in &lt;2.0s with zero API cost.", body_style),
            Paragraph("Evaluates filtered top candidate windows (~2–4/ep) or user-chosen episodes.", body_style)
        ]
    ]
    t_arch = Table(arch_table_data, colWidths=[1.1*inch, 3.4*inch, 2.8*inch])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 4))

    # Section 3: Scoring Rubric
    story.append(Paragraph("3. Scoring Rubric & Window Selection Logic", h1_style))
    story.append(Paragraph(
        "Candidate clips are evaluated on a composite 100-point scale across three weighted dimensions:<br/>"
        "• <b>Hook Score (40%):</b> Evaluates the first 3.0 seconds. Looks for high-stakes disruption verbs (<i>'marry', 'turn around', 'betray', 'enough'</i>), confrontational tones (<i>Venomous, Disgusted, Screaming</i>), or physical shock actions (<i>slap, tear, doors burst</i>).<br/>"
        "• <b>Cliffhanger Score (35%):</b> Evaluates the final 3.0–5.0 seconds. Looks for unresolved interrogatives (<i>'?'</i>), interrupted statements (<i>'...'</i>), acoustic swells (<i>'ominous cliffhanger peak'</i>), or visual freeze/cut-to-black.<br/>"
        "• <b>Standalone Coherence (25%):</b> Requires &gt;= 2 distinct speakers in conflict and 4–10 dialogue turns. Penalizes slow monologue exposition.",
        body_style
    ))

    # ==================== PAGE BREAK TO PAGE 2 ====================
    story.append(PageBreak())

    # Section 4: Campaign Rollout
    story.append(Paragraph("4. Strategic Campaign Rollout: Which Promos to Post First & Why?", h1_style))
    story.append(Paragraph(
        "Ranking microdrama promos is not just about raw emotional score; it requires a <b>funnel-aligned publishing strategy</b>:",
        body_style
    ))

    ranking_data = [
        [Paragraph("<b>Tier &amp; Priority</b>", body_style), Paragraph("<b>Target Episodes</b>", body_style), Paragraph("<b>Strategic Rationale &amp; Placement</b>", body_style)],
        [
            Paragraph("<b>Tier 1: Post First</b><br/>(Cold User Acquisition)", body_style),
            Paragraph("<b>Episodes 1 – 3</b><br/>(Rank #1: Ep 3, 00:25–00:56<br/>Rank #2: Ep 1, 01:15–01:38)", body_style),
            Paragraph("<b>Zero-Lore Universality:</b> The wedding betrayal, sister stealing the groom, and mysterious hero's intervention require zero prior knowledge. Highest conversion from cold scroller to initial app install.", body_style)
        ],
        [
            Paragraph("<b>Tier 2: Post Second</b><br/>(Viral Escalation &amp; Shares)", body_style),
            Paragraph("<b>Episodes 4 – 15</b><br/>(Identity reveals &amp; public confrontation)", body_style),
            Paragraph("<b>Power Reversal &amp; Catharsis:</b> Juliana standing her ground and the Duke's true status emerging. Drives high comment velocity and algorithmic engagement on TikTok/Instagram.", body_style)
        ],
        [
            Paragraph("<b>Tier 3: Post Third</b><br/>(Retargeting &amp; Churn Prevention)", body_style),
            Paragraph("<b>Episodes 16 – 50</b><br/>(High-cliffhanger mid-season)", body_style),
            Paragraph("<b>Binge Triggers:</b> Life-or-death and high-stakes ultimatums targeted at warm audiences who installed the app but stalled at Episode 5.", body_style)
        ]
    ]
    t_rank = Table(ranking_data, colWidths=[1.5*inch, 1.8*inch, 4.0*inch])
    t_rank.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_rank)
    story.append(Spacer(1, 4))

    # Section 5: Honest Quality Evaluation
    story.append(Paragraph("5. Honest Quality Evaluation & Failure Modes ('Where does the tool pick badly?')", h1_style))
    story.append(Paragraph(
        "Automated audit (<i>src/quality_checker.py</i>) across all extracted promos scored 26 clean and flagged 74 edge cases:<br/>"
        "• <b>1. Premature Cut Buffer (58% of clips):</b> Scripts end dialogue abruptly (e.g. 00:32.40). Cutting there clips visual reaction / audio sting. <i>Mitigation:</i> Parser accounts for +0.75s reaction buffer.<br/>"
        "• <b>2. Off-Target Secondary Characters (32% of clips):</b> Shouting matches between minor cast score high lexically but fail as cold UA ads. <i>Mitigation:</i> Lead-character weighting bonus.<br/>"
        "• <b>3. Lore &amp; Exposition Overload:</b> High-word-count scenes (>25 words/turn) bore scrollers. <i>Mitigation:</i> Turn density penalizer.<br/>"
        "• <b>4. Visual-Only Ambiguity:</b> Silent action beats (slaps, chases) are underestimated without multimodal vision.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Section 6: AI Tools Used & Where AI Got It Wrong
    story.append(Paragraph("6. AI Tools Used & One Place AI Got It Wrong", h1_style))
    story.append(Paragraph(
        "• <b>Tools Used:</b> Antigravity coding agent for full pipeline and Streamlit studio development; Gemini &amp; OpenAI REST APIs for semantic analysis, tension detection, and LLM-as-a-Judge validation.<br/>"
        "• <b>Where AI Got It Wrong:</b> Direct LLM prompting on screenplays caused 3 critical flaws: (1) Cutting on the exact final word, truncating audio tails; (2) Drifting beyond the 20–60s bounds; (3) Hallucinating timestamps not matching subtitle sync. Wrapping the LLMs inside deterministic window math, strict duration guards, and 20 automated unit tests eliminated these issues completely.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Section 7: Production Workflow, Scaling & Deliverables
    story.append(Paragraph("7. Production Workflow, Scaling & Deliverables (Moments Only — No Overlays/Editing)", h1_style))
    story.append(Paragraph(
        "• <b>Scaling &amp; Human-in-the-Loop Workflow:</b> Rule filtering scans 1,000+ episodes in &lt;45s on standard CPU, dispatching only top candidates to LLMs. Editors review ranked 20–60s cuts, pin manual adjustments, and export cut sheets without baked video overlays or artificial music.<br/>"
        "• <b>Deliverables:</b> (1) <b>Live Cloud App:</b> <u>https://kuku-promo-detector.onrender.com</u>; (2) <b>GitHub Repo:</b> <u>https://github.com/srikrishna6174/kuku-ai-promo-detector</u>; (3) <b>Outputs Pack:</b> Structured <i>outputs/promos/</i> (JSON, CSV, report, cut sheets), <i>outputs/quality_audit/</i>, and <i>outputs/editor_exports/</i>.",
        body_style
    ))

    doc.build(story)
    print(f"[+] Successfully generated 2-page PDF: {output_filename}")

if __name__ == "__main__":
    build_solution_pdf()

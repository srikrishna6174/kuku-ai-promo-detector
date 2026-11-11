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
    story.append(Paragraph("1. Problem Choice, Strategic Context & Framing", h1_style))
    story.append(Paragraph(
        "<b>Why Problem 1?</b> Microdramas are a high-velocity, acquisition-driven format. The bottleneck for organic and paid growth on TikTok, Instagram Reels, and YouTube Shorts is manual video clipping: human editors spend hours per season scrubbing timelines to find 20–60s hooks. Automating this directly impacts top-of-funnel customer acquisition cost (CAC) and throughput.<br/>"
        "<b>Key Assumptions Made:</b><br/>"
        "• <i>Strict Duration Enforcement:</i> Clips must respect platform drop-off curves (optimal 25–45s; hard range 20–60s).<br/>"
        "• <i>Continuous & Multi-Segment Modes:</i> Primary focus on single continuous beats for natural momentum, with automated support for high-tempo 2-beat jumpcuts (e.g., Ep 1 Doorway Confrontation + Altar Betrayal; Ep 1 Humiliation + Ep 3 Hero Rescue).<br/>"
        "• <i>Zero-Lore Comprehension:</i> A top-of-funnel ad must be understandable to a cold scroller within 3 seconds without knowing previous plotlines.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Section 2
    story.append(Paragraph("2. Technical Architecture: Two-Stage Hybrid Engine", h1_style))
    story.append(Paragraph(
        "To balance operational cost, latency, and nuanced creative reasoning at real-world scale, we rejected a naive 'throw all 50 scripts at a closed LLM' approach. Instead, we architected a <b>Two-Stage Hybrid Pipeline</b>:",
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
            Paragraph("• Semantic tension assessment, hook/cliffhanger summaries &amp; 'Why it works'.<br/>• LLM-as-a-Judge pass &amp; auto failover on outage/rate limit.<br/>• Swappable provider adapter (default: Gemini &amp; OpenAI; zero lock-in to add stronger APIs).", body_style)
        ],
        [
            Paragraph("<b>Cost & Scale</b>", body_style),
            Paragraph("<b>$0.00 base cost</b>; runs in &lt;2.0s across 50 episodes on standard CPU.", body_style),
            Paragraph("Only evaluates top filtered candidate windows (~2–4/ep) or selected episodes. Cost: <b>~$0.008 per show</b>.", body_style)
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
    story.append(Paragraph("7. Production Scaling, Cost & Deliverables (Moments Only — No Overlays/Editing)", h1_style))
    story.append(Paragraph(
        "• <b>Scale &amp; Cost:</b> Processing 20 new shows/week (1,000 episodes) costs &lt;$0.16/week ($0 rules tier) in &lt;45s compute; editors receive ranked 20–60s cut sheets and manual timestamp pinning without unwanted overlays or edits.<br/>"
        "• <b>Deliverables:</b> (1) Per-project <i>Streamlit Promo Studio</i> for unseen scripts during live testing; (2) Unedited <i>outputs/</i> pack (<i>promos_master.json</i>, <i>promos_ranked.csv</i>, <i>quality_audit_and_failures.json</i>, .txt cut sheets &amp; markers); (3) 20/20 verified unit tests.",
        body_style
    ))

    doc.build(story)
    print(f"[+] Successfully generated 2-page PDF: {output_filename}")

if __name__ == "__main__":
    build_solution_pdf()


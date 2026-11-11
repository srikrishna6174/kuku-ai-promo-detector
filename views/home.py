import streamlit as st

from views.ui_shared import (
    clean_html,
    get_all_inputs_index,
    navigate_to,
    render_active_header,
    resolve_active_bundle,
    stretch_kw,
)


def _render_hub_tiles(tiles, cols_count: int):
    cols = st.columns(cols_count, gap="medium")
    for col_idx, tile in enumerate(tiles):
        with cols[col_idx]:
            with st.container(border=True):
                tile_html = "".join(
                    [
                        '<div class="hub-tile-body">',
                        '<div class="hub-tile-top">',
                        f'<span class="hub-tile-step {tile["step_cls"]}">{clean_html(tile["step"])}</span>',
                        "</div>",
                        f'<div class="hub-tile-title">{clean_html(tile["title"])}</div>',
                        f'<div class="hub-tile-desc">{clean_html(tile["desc"])}</div>',
                        f'<div class="hub-tile-meta">{clean_html(tile["meta"])}</div>',
                        "</div>",
                    ]
                )
                st.markdown(tile_html, unsafe_allow_html=True)
                btn_type = "primary" if tile["primary"] else "secondary"
                if st.button(
                    tile["btn_label"],
                    type=btn_type,
                    icon=tile["icon"],
                    key=f"home_tile_{tile['key']}",
                    **stretch_kw(st.button),
                ):
                    navigate_to(tile["key"])


def render_home_page():
    active_bundle = resolve_active_bundle()
    all_inputs = get_all_inputs_index()
    promos_count = len(active_bundle.get("promos", []))
    ep_count = int(active_bundle.get("episode_count", 0))
    audit_report = active_bundle.get("audit_report", {})
    flagged_count = int(audit_report.get("flagged_promos_count", 0))
    stitched_count = len(active_bundle.get("stitched_promos", []))
    proj_name = active_bundle.get("title", "Active Project")

    st.markdown('<div class="page-title">Kuku Promo Studio</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Add or choose a project below, then inspect its detected promos, script timestamps, and quality audit.</div>',
        unsafe_allow_html=True,
    )

    project_tiles = [
        {
            "key": "new_input",
            "step": "01 · Create",
            "step_cls": "hub-step-0",
            "title": "Add New Project",
            "desc": "Upload episode scripts (.txt, .srt, .zip) or paste dialogue to find 20–60s hooks and cliffhanger cuts.",
            "meta": "Supports rules, Gemini & OpenAI",
            "btn_label": "Add Project",
            "icon": ":material/add_circle:",
            "primary": True,
        },
        {
            "key": "library",
            "step": "02 · Manage",
            "step_cls": "hub-step-1",
            "title": "Project Library",
            "desc": "Browse saved projects and session drafts, rename entries, or delete a project with all its promos.",
            "meta": f"{len(all_inputs)} project(s) in library",
            "btn_label": f"Open Library ({len(all_inputs)})",
            "icon": ":material/folder_open:",
            "primary": False,
        },
    ]

    _render_hub_tiles(project_tiles, 2)

    st.markdown("<div style='height: 0.45rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-heading">Selected Project Views — {clean_html(proj_name)}</div>',
        unsafe_allow_html=True,
    )
    render_active_header(active_bundle, allow_switch=True)

    workspace_tiles = [
        {
            "key": "promos",
            "step": "03 · Promos",
            "step_cls": "hub-step-2",
            "title": "Detected Promos",
            "desc": "Browse promos grouped by type, inspect intercut trailers, add AI or manual cuts, and download .txt sheets.",
            "meta": f"{promos_count} promos · {stitched_count} intercuts",
            "btn_label": f"View Promos ({promos_count})",
            "icon": ":material/movie:",
            "primary": True,
        },
        {
            "key": "explorer",
            "step": "04 · Scripts",
            "step_cls": "hub-step-3",
            "title": "Script Explorer",
            "desc": "Read episode scripts beat-by-beat with this project's detected promo windows highlighted inline.",
            "meta": f"{ep_count} episode(s) in this project",
            "btn_label": "Explore Scripts",
            "icon": ":material/description:",
            "primary": False,
        },
        {
            "key": "audit",
            "step": "05 · Audit",
            "step_cls": "hub-step-5",
            "title": "Quality Audit",
            "desc": "Inspect flagged edge cases for this project such as premature cut buffers, off-target cast, or exposition.",
            "meta": f"{flagged_count} clip(s) flagged for review",
            "btn_label": "View Audit",
            "icon": ":material/fact_check:",
            "primary": False,
        },
    ]

    _render_hub_tiles(workspace_tiles, 3)


import streamlit as st

from src.input_manager import (
    BUILTIN_INPUT_ID,
    delete_saved_bundle,
    is_builtin_hidden,
    load_saved_bundle,
    save_bundle_to_disk,
    set_builtin_hidden,
)
from views.ui_shared import (
    clean_html,
    get_all_inputs_index,
    navigate_to,
    resolve_active_bundle,
    select_kw,
    stretch_kw,
)


def _purge_project_state(project_id: str):
    """Clears all session state references and cached filter keys tied to a deleted project."""
    st.session_state.get("unsaved_inputs", {}).pop(project_id, None)
    for k in list(st.session_state.keys()):
        if k.endswith(f"_{project_id}"):
            st.session_state.pop(k, None)
    if st.session_state.get("active_input_id") == project_id:
        st.session_state.pop("active_input_id", None)
    st.session_state["promos_page_num"] = 1
    st.session_state["promos_filter_sig"] = None


def _render_project_card(item: dict, active_id: str):
    """Renders a single Project Library card with compact inline edit and top-right delete icons."""
    pid = item["id"]
    status = item["status"]
    is_act = pid == active_id

    if status == "Built-in":
        pill_cls, pill_lbl = "pill-builtin", "Built-in"
    elif status == "Saved":
        pill_cls, pill_lbl = "pill-saved", "Saved"
    else:
        pill_cls, pill_lbl = "pill-temp", "Draft"

    active_pill = '<span class="pill pill-active">Active</span>' if is_act else ""

    with st.container(border=True):
        with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center", gap="small"):
            with st.container(horizontal=True, width="content", vertical_alignment="center", gap="small"):
                st.markdown(
                    f'<span style="font-weight:650;font-size:1rem;color:#18181B;">{clean_html(item["title"])}</span>',
                    unsafe_allow_html=True,
                )
                if status in ("Saved", "Unsaved"):
                    edit_help = "Rename & save draft" if status == "Unsaved" else "Rename project"
                    with st.popover("", icon=":material/edit:", type="tertiary", help=edit_help, key=f"lib_edit_pop_{pid}"):
                        new_t = st.text_input("Project title", value=item["title"], key=f"ren_val_{pid}")
                        btn_lbl = "Save Project" if status == "Unsaved" else "Apply"
                        if st.button(btn_lbl, key=f"ren_apply_{pid}", type="primary", **stretch_kw(st.button)):
                            cleaned = new_t.strip()
                            if status == "Unsaved":
                                ub = st.session_state["unsaved_inputs"].get(pid)
                                if ub:
                                    ub["title"] = cleaned or ub["title"]
                                    saved_b = save_bundle_to_disk(ub)
                                    st.session_state["unsaved_inputs"].pop(pid, None)
                                    st.session_state["active_input_id"] = saved_b["id"]
                                    st.rerun()
                            else:
                                loaded = load_saved_bundle(pid)
                                if loaded and cleaned:
                                    loaded["title"] = cleaned
                                    save_bundle_to_disk(loaded)
                                    st.rerun()
                st.markdown(
                    f'<span class="pill {pill_cls}">{pill_lbl}</span>{active_pill}',
                    unsafe_allow_html=True,
                )

            del_help = (
                "Remove built-in benchmark & promos (restorable)"
                if status == "Built-in"
                else "Delete project & all its promos"
            )
            with st.popover("", icon=":material/delete:", type="tertiary", help=del_help, key=f"lib_del_pop_{pid}"):
                if status == "Built-in":
                    st.caption(
                        f"Remove **{item['title']}** and all **{item['promo_count']}** promo(s)? (Can be restored anytime.)"
                    )
                else:
                    st.caption(
                        f"Permanently delete **{item['title']}** and all **{item['promo_count']}** promo(s)?"
                    )
                if st.button("Delete Project & Promos", key=f"lib_del_{pid}", type="primary", **stretch_kw(st.button)):
                    if status == "Built-in":
                        set_builtin_hidden(True)
                    elif status == "Saved":
                        delete_saved_bundle(pid)
                    _purge_project_state(pid)
                    st.rerun()

        st.caption(f"{item['episode_count']} ep(s) · {item['promo_count']} promo(s) · {item['detection_label']}")
        st.caption(f"Created: {item['created_at']}")

        btn_type = "secondary" if is_act else "primary"
        if status == "Unsaved":
            b1, b2 = st.columns([1.45, 1.0])
            with b1:
                if st.button("View Promos" if is_act else "Open Promos", key=f"lib_open_{pid}", type=btn_type, **stretch_kw(st.button)):
                    st.session_state["active_input_id"] = pid
                    navigate_to("promos")
            with b2:
                if st.button("Save to Library", key=f"lib_quick_save_{pid}", **stretch_kw(st.button)):
                    ub = st.session_state["unsaved_inputs"].get(pid)
                    if ub:
                        saved_b = save_bundle_to_disk(ub)
                        st.session_state["unsaved_inputs"].pop(pid, None)
                        st.session_state["active_input_id"] = saved_b["id"]
                        st.rerun()
        else:
            if st.button("View Promos" if is_act else "Open Promos", key=f"lib_open_{pid}", type=btn_type, **stretch_kw(st.button)):
                st.session_state["active_input_id"] = pid
                navigate_to("promos")


def render_library_page():
    active_bundle = resolve_active_bundle()
    active_id = active_bundle["id"]
    builtin_hidden = is_builtin_hidden()

    if builtin_hidden:
        top_l, top_mid, top_r = st.columns([3.0, 1.3, 1.1])
    else:
        top_l, top_r = st.columns([3.8, 1.1])
        top_mid = None

    with top_l:
        st.markdown('<div class="page-title">Project Library</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="page-subtitle">Switch between projects, rename entries, or delete a project along with all of its detected promos.</div>',
            unsafe_allow_html=True,
        )
    if top_mid is not None:
        with top_mid:
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            if st.button("Restore Benchmark", key="lib_restore_builtin", **stretch_kw(st.button)):
                set_builtin_hidden(False)
                st.session_state["active_input_id"] = BUILTIN_INPUT_ID
                st.rerun()
    with top_r:
        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
        if st.button("Add Project", type="primary", icon=":material/add:", key="lib_new_btn", **stretch_kw(st.button)):
            navigate_to("new_input")

    all_items = get_all_inputs_index()

    if len(all_items) > 1:
        f1, f2 = st.columns([1.2, 2.2])
        with f1:
            status_filter = st.selectbox(
                "Filter by status",
                ["All Projects", "Built-in & Saved", "Session Drafts"],
                key="lib_status_filter",
                **select_kw(),
            )
        with f2:
            search_txt = st.text_input(
                "Search project",
                placeholder="Filter project titles...",
                key="lib_search",
            )
    else:
        status_filter = "All Projects"
        search_txt = ""

    filtered_items = list(all_items)
    if status_filter == "Built-in & Saved":
        filtered_items = [i for i in filtered_items if i["status"] in ("Built-in", "Saved")]
    elif status_filter == "Session Drafts":
        filtered_items = [i for i in filtered_items if i["status"] == "Unsaved"]

    if search_txt.strip():
        q = search_txt.strip().lower()
        filtered_items = [i for i in filtered_items if q in i["title"].lower()]

    unsaved_items = [i for i in filtered_items if i["status"] == "Unsaved"]
    saved_items = [i for i in filtered_items if i["status"] in ("Built-in", "Saved")]

    if not filtered_items:
        st.info("No projects in the library yet. Click **Add Project** to upload a script, or restore the built-in benchmark.")
        return

    # ---- Unsaved Session Drafts ----
    if unsaved_items:
        st.markdown('<div class="section-heading">Session Drafts (Unsaved)</div>', unsafe_allow_html=True)
        cols = st.columns(2)
        for idx, item in enumerate(unsaved_items):
            with cols[idx % 2]:
                _render_project_card(item, active_id)

    # ---- Saved & Built-in Projects ----
    if saved_items:
        st.markdown('<div class="section-heading">Saved Projects</div>', unsafe_allow_html=True)
        cols = st.columns(2)
        for idx, item in enumerate(saved_items):
            with cols[idx % 2]:
                _render_project_card(item, active_id)

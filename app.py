import streamlit as st

from views.audit import render_audit_page
from views.explorer import render_explorer_page
from views.home import render_home_page
from views.library import render_library_page
from views.new_input import render_new_input_page
from views.promos import render_promos_page
from views.ui_shared import (
    PAGE_REGISTRY,
    apply_global_styles,
    init_session_state,
    render_sidebar,
    resolve_active_bundle,
)

st.set_page_config(
    page_title="Kuku Promo Studio",
    page_icon=":material/movie:",
    layout="wide",
    initial_sidebar_state="auto",
)

apply_global_styles()
init_session_state()

home_page = st.Page(
    render_home_page, title="Home", icon=":material/home:", url_path="home", default=True
)
new_input_page = st.Page(
    render_new_input_page, title="New Input", icon=":material/add_circle:", url_path="new-input"
)
library_page = st.Page(
    render_library_page, title="Project Library", icon=":material/folder_open:", url_path="library"
)
promos_page = st.Page(
    render_promos_page, title="Promos", icon=":material/movie:", url_path="promos"
)
explorer_page = st.Page(
    render_explorer_page, title="Script Explorer", icon=":material/description:", url_path="explorer"
)
audit_page = st.Page(
    render_audit_page, title="Quality Audit", icon=":material/fact_check:", url_path="audit"
)

PAGE_REGISTRY.update(
    {
        "home": home_page,
        "new_input": new_input_page,
        "library": library_page,
        "promos": promos_page,
        "explorer": explorer_page,
        "audit": audit_page,
    }
)

pages = [
    home_page,
    new_input_page,
    library_page,
    promos_page,
    explorer_page,
    audit_page,
]

try:
    pg = st.navigation(pages, position="top")
except TypeError:
    pg = st.navigation(pages)

active_bundle = resolve_active_bundle()
render_sidebar(active_bundle)
pg.run()

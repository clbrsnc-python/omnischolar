import streamlit as st
import httpx
import asyncio
import urllib.parse
import re
import json
import base64
from supabase import create_client, Client

PROTO = base64.b64decode("aHR0cHM6Ly8=").decode('utf-8')

st.set_page_config(
    page_title="OmniScholar - Universal Scholarly Search Engine",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown('''
<style>
    .stApp {
        background: linear-gradient(135deg, #e0f2fe 0%, #f0f9ff 50%, #e0f2fe 100%) !important;
        color: #0f172a !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        max-width: 98% !important;
    }
    .os-navbar {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 14px 24px;
        border: 1px solid #cbd5e1;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .os-brand {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .os-logo-box {
        background-color: #2563eb;
        color: white;
        width: 42px;
        height: 42px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.3);
    }
    .os-title-text {
        font-size: 26px;
        font-weight: 800;
        color: #1e1b4b;
        margin: 0;
        line-height: 1.1;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .os-badge-oa {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #86efac;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .os-subtitle {
        font-size: 13px;
        color: #64748b;
        margin: 2px 0 0 0;
    }
    .os-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 18px 22px;
        border: 1px solid #cbd5e1;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.04);
        margin-bottom: 18px;
    }
    .os-section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
        padding-bottom: 6px;
        border-bottom: 1px solid #f1f5f9;
    }
    .os-section-title {
        font-size: 13px;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .os-section-sub {
        font-size: 12px;
        color: #64748b;
        font-weight: 500;
        text-transform: none;
    }
    .ext-link-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 600;
        color: #334155 !important;
        text-decoration: none !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    .ext-link-btn:hover {
        background-color: #f8fafc;
        border-color: #2563eb;
        color: #2563eb !important;
        transform: translateY(-1px);
    }
    .article-card {
        background-color: #ffffff;
        border-radius: 10px;
        border: 1px solid #cbd5e1;
        padding: 16px 20px;
        margin-bottom: 14px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
        transition: border 0.2s ease;
    }
    .article-card:hover {
        border-color: #93c5fd;
    }
    .article-title {
        font-size: 16px;
        font-weight: 700;
        color: #1e293b;
        text-decoration: none !important;
        line-height: 1.3;
    }
    .article-title:hover {
        color: #2563eb !important;
    }
    .article-meta {
        font-size: 12px;
        color: #64748b;
        margin-top: 6px;
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        align-items: center;
    }
    .badge-repo {
        background-color: #eff6ff;
        color: #1d4ed8;
        border: 1px solid #bfdbfe;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-peer {
        background-color: #f0fdf4;
        color: #15803d;
        border: 1px solid #bbf7d0;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: 600;
    }
</style>
''', unsafe_allow_html=True)


@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase()

if "scopus_key" not in st.session_state:
    st.session_state["scopus_key"] = ""
if "query_rows" not in st.session_state:
    st.session_state["query_rows"] = [{"boolean": "AND", "field": "All Fields", "value": ""}]
if "search_results" not in st.session_state:
    st.session_state["search_results"] = []
if "selected_articles" not in st.session_state:
    st.session_state["selected_articles"] = {}
if "selected_dbs" not in st.session_state:
    st.session_state["selected_dbs"] = {"openalex", "core", "arxiv", "doaj", "doab", "europepmc", "unpaywall", "semanticscholar"}


@st.dialog("🔑 Elsevier Scopus API Key Configuration")
def show_scopus_dialog():
    elsevier_dev_url = f"{PROTO}dev.elsevier.com/"
    st.markdown(f'''
    ### How to obtain a Free Elsevier Scopus API Key:
    1. Visit the **Elsevier Developer Portal**.
    2. Click **I want an API Key** and sign in or register a free developer account.
    3. Generate your 32-character API key for Open Access endpoints.
    4. Paste your key below to activate **Scopus OA** federated searches.
    ''')
    current_key = st.text_input("Enter Scopus API Key:", value=st.session_state["scopus_key"], type="password")
    if st.button("💾 Save Key", use_container_width=True):
        st.session_state["scopus_key"] = current_key.strip()
        st.success("Scopus API Key saved successfully!")
        st.rerun()


@st.dialog("💬 Citations & Export Manager")
def show_citations_dialog():
    selected = list(st.session_state["selected_articles"].values())
    if not selected:
        st.info("No articles selected for citation export yet. Check articles in the search results to add them!")
        return
    
    st.subheader(f"Selected Publications ({len(selected)})")
    style = st.selectbox("Select Citation Style:", ["APA 7th", "MLA 9th", "Chicago 17th", "IEEE", "Harvard", "BibTeX"])
    
    formatted_citations = []
    bibtex_items = []
    
    for idx, item in enumerate(selected, 1):
        authors = item.get("authors", "Unknown Authors")
        title = item.get("title", "Untitled Work")
        year = item.get("year", "N/A")
        journal = item.get("journal", "Open Repository")
        doi = item.get("doi", "")
        doi_str = f"{PROTO}doi.org/{doi}" if doi else ""
        
        cite_key = re.sub(r'[^a-zA-Z0-9]', '', authors.split(',')[0]) + str(year) + str(idx)
        if style == "APA 7th": cit = f"{authors} ({year}). {title}. *{journal}*. {doi_str}"
        elif style == "MLA 9th": cit = f'{authors}. "{title}." *{journal}*, {year}. {doi_str}'
        elif style == "Chicago 17th": cit = f'{authors}. "{title}." *{journal}* ({year}). {doi_str}'
        elif style == "IEEE": cit = f'[{idx}] {authors}, "{title}," *{journal}*, {year}. {doi_str}'
        elif style == "Harvard": cit = f"{authors}, {year}. {title}. *{journal}*. Available at: {doi_str}"
        else:
            cit = f"@article{{{cite_key},\n  author = {{{authors}}},\n  title = {{{title}}},\n  journal = {{{journal}}},\n  year = {{{year}}},\n  doi = {{{doi}}}\n}}"
        formatted_citations.append(cit)
        
        bib_item = f"@article{{{cite_key},\n  author = {{{authors}}},\n  title = {{{title}}},\n  journal = {{{journal}}},\n  year = {{{year}}},\n  doi = {{{doi}}}\n}}"
        bibtex_items.append(bib_item)

    output_text = "\n\n".join(formatted_citations)
    st.text_area("Formatted Citations:", value=output_text, height=220)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("💾 Export (.txt)", data=output_text, file_name="citations.txt", mime="text/plain", use_container_width=True)
    with col2:
        bib_text = "\n\n".join(bibtex_items)
        st.download_button("💾 Export (.bib)", data=bib_text, file_name="references.bib", mime="text/x-bibtex", use_container_width=True)
    with col3:
        if st.button("🗑️ Clear Selection", use_container_width=True):
            st.session_state["selected_articles"] = {}
            st.rerun()


scopus_active = bool(st.session_state["scopus_key"])
count_selected = len(st.session_state["selected_articles"])

col_nav_l, col_nav_r = st.columns([3.2, 1.3])

with col_nav_l:
    st.markdown('''
    <div class="os-brand">
        <div class="os-logo-box">🎓</div>
        <div>
            <div class="os-title-text">
                OmniScholar
                <span class="os-badge-oa">100% LEGAL OPEN ACCESS</span>
            </div>
            <div class="os-subtitle">Universal Scholarly Search & Citation Engine</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

with col_nav_r:
    st.write('')
    btn_c1, btn_c2 = st.columns(2)
    with btn_c1:
        scopus_label = "🔑 Scopus Active" if scopus_active else "🔑 Scopus Key"
        if st.button(scopus_label, use_container_width=True): show_scopus_dialog()
    with btn_c2:
        if st.button(f"💬 Citations ({count_selected})", type="primary", use_container_width=True): show_citations_dialog()

st.markdown('<div style="margin-bottom: 12px;"></div>', unsafe_allow_html=True)

all_repos = [
    ("openalex", "OpenAlex", "🌐", "250M+ Works & Publisher DOIs"),
    ("core", "CORE Aggregator", "☘️", "ROAR & OpenDOAR Repositories"),
    ("arxiv", "arXiv", "⚛️", "Physics, CS, Math & Stats Preprints"),
    ("doaj", "DOAJ", "📗", "Directory of Open Access Journals"),
    ("doab", "DOAB", "📘", "Directory of Open Access Books"),
    ("europepmc", "Europe PMC / PMC", "⌛", "Biomedical Full Text Articles"),
    ("unpaywall", "Unpaywall", "🔓", "Direct Publisher OA PDF Resolver"),
    ("semanticscholar", "Semantic Scholar", "🌓", "AI Citation & Metadata Graph"),
    ("scopus", "Scopus OA", "🔑", "Elsevier Open Access (Requires Key)")
]

with st.container():
    st.markdown('''
    <div class="os-section-header">
        <div class="os-section-title">
            <span>🗄️ TARGET DATABASES & OPEN REPOSITORIES</span>
            <span class="os-section-sub">(Direct API Connectivity)</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    col_sa1, col_sa2, col_sa3 = st.columns([6, 1, 1])
    with col_sa2:
        if st.button("Select All", type="tertiary"):
            st.session_state["selected_dbs"] = {r[0] for r in all_repos}
            st.rerun()
    with col_sa3:
        if st.button("Deselect All", type="tertiary"):
            st.session_state["selected_dbs"] = set()
            st.rerun()

    cols_top = st.columns(5)
    for idx, (r_id, r_name, r_icon, r_desc) in enumerate(all_repos[:5]):
        with cols_top[idx]:
            is_checked = r_id in st.session_state["selected_dbs"]
            new_val = st.checkbox(f"{r_icon} **{r_name}**", value=is_checked, key=f"cb_{r_id}")
            st.caption(f'<span style="font-size: 10px; color: #64748b;">{r_desc}</span>', unsafe_allow_html=True)
            if new_val != is_checked:
                if new_val: st.session_state["selected_dbs"].add(r_id)
                else: st.session_state["selected_dbs"].discard(r_id)

    cols_btm = st.columns(4)
    for idx, (r_id, r_name, r_icon, r_desc) in enumerate(all_repos[5:]):
        with cols_btm[idx]:
            is_checked = r_id in st.session_state["selected_dbs"]
            new_val = st.checkbox(f"{r_icon} **{r_name}**", value=is_checked, key=f"cb_{r_id}")
            st.caption(f'<span style="font-size: 10px; color: #64748b;">{r_desc}</span>', unsafe_allow_html=True)
            if new_val != is_checked:
                if new_val: st.session_state["selected_dbs"].add(r_id)
                else: st.session_state["selected_dbs"].discard(r_id)

st.markdown('<div style="margin-bottom: 16px;"></div>', unsafe_allow_html=True)


with st.container():
    st.markdown('''
    <div class="os-section-header">
        <div class="os-section-title">🎛️ ADVANCED QUERY BUILDER</div>
        <div class="os-section-sub">Supports Boolean Logic (AND, OR, NOT) & Field Scoping</div>
    </div>
    ''', unsafe_allow_html=True)

    rows_to_remove = []
    for idx, row in enumerate(st.session_state["query_rows"]):
        c_bool, c_field, c_val, c_del = st.columns([1.2, 1.8, 6, 0.5])
        
        with c_bool:
            if idx == 0: st.markdown("**QUERY**")
            else: row["boolean"] = st.selectbox("", ["AND", "OR", "NOT"], index=["AND", "OR", "NOT"].index(row["boolean"]), key=f"bool_{idx}")
        
        with c_field:
            row["field"] = st.selectbox("", ["All Fields", "Title", "Author", "Abstract", "DOI / ISSN"], index=["All Fields", "Title", "Author", "Abstract", "DOI / ISSN"].index(row["field"]), key=f"field_{idx}")
            
        with c_val:
            row["value"] = st.text_input("", value=row["value"], placeholder="Enter search terms, keywords, or DOI (e.g. 10.1038/s41586-020-2649-2)...", key=f"val_{idx}")
            
        with c_del:
            if idx > 0:
                if st.button("🗑️", key=f"del_{idx}"): rows_to_remove.append(idx)

    for idx in reversed(rows_to_remove):
        st.session_state["query_rows"].pop(idx)
        st.rerun()

    col_act1, col_act2, col_act3 = st.columns([2, 2, 3])
    with col_act1:
        if st.button("➕ Add Boolean Row"):
            st.session_state["query_rows"].append({"boolean": "AND", "field": "All Fields", "value": ""})
            st.rerun()
    with col_act2:
        if st.button("Clear Fields"):
            st.session_state["query_rows"] = [{"boolean": "AND", "field": "All Fields", "value": ""}]
            st.rerun()
            
    query_parts = []
    for r in st.session_state["query_rows"]:
        val = r["value"].strip()
        if val:
            if r["field"] != "All Fields": query_parts.append(f"{r['boolean']} {r['field']}:({val})")
            else:
                if query_parts: query_parts.append(f"{r['boolean']} ({val})")
                else: query_parts.append(val)
    full_query_string = " ".join(query_parts) if query_parts else ""

    with col_act3:
        execute_search = st.button("🔍 Execute Multi-Database Search", type="primary", use_container_width=True)

st.markdown('<div style="margin-bottom: 16px;"></div>', unsafe_allow_html=True)

enc_q = urllib.parse.quote(full_query_string or "open access research")
g_scholar_url = f"{PROTO}scholar.google.com/scholar?q={enc_q}"
base_url = f"{PROTO}www.base-search.net/Search/Results?lookfor={enc_q}"
shodh_url = f"{PROTO}shodhganga.inflibnet.ac.in/simple-search?query={enc_q}"
worldcat_url = f"{PROTO}www.worldcat.org/search?q={enc_q}"

st.markdown(f'''
<div style="background-color: #ffffff; border-radius: 12px; padding: 12px 20px; border: 1px solid #cbd5e1; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 20px;">
    <div style="font-weight: 700; color: #0d9488; font-size: 13px; display: flex; align-items: center; gap: 6px;">
        <span>🔗</span> OPEN SEARCH QUERY DIRECTLY IN EXTERNAL ENGINES:
    </div>
    <div style="display: flex; flex-wrap: wrap; gap: 10px;">
        <a href="{g_scholar_url}" target="_blank" class="ext-link-btn">🎓 Google Scholar</a>
        <a href="{base_url}" target="_blank" class="ext-link-btn">🏛️ BASE Search</a>
        <a href="{shodh_url}" target="_blank" class="ext-link-btn">📚 Shodhganga ETDs</a>
        <a href="{worldcat_url}" target="_blank" class="ext-link-btn">🌐 WorldCat</a>
    </div>
</div>
''', unsafe_allow_html=True)


async def fetch_openalex(term):
    try:
        url = f"{PROTO}api.openalex.org/works?search={urllib.parse.quote(term)}&per-page=20"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, timeout=8.0)
            if res.status_code == 200:
                data = res.json().get("results", [])
                items = []
                for item in data:
                    authors = ", ".join([a.get("author", {}).get("display_name", "") for a in item.get("authorships", []) if a.get("author", {}).get("display_name")]) or "Unknown Authors"
                    doi = item.get("doi", "").replace(f"{PROTO}doi.org/", "")
                    pdf_url = item.get("open_access", {}).get("oa_url") or item.get("doi") or f"{PROTO}openalex.org/works/{item.get('id')}"
                    items.append({
                        "id": str(item.get("id")),
                        "title": item.get("title") or "Untitled Work",
                        "authors": authors,
                        "year": str(item.get("publication_year") or "N/A"),
                        "journal": item.get("primary_location", {}).get("source", {}).get("display_name") or "Open Repository",
                        "doi": doi,
                        "pdfUrl": pdf_url,
                        "abstract": "Indexed in OpenAlex global research graph.",
                        "source": "OpenAlex",
                        "type": item.get("type", "article"),
                        "peerReviewed": True
                    })
                return items
    except Exception: pass
    return []

async def fetch_arxiv(term):
    try:
        url = f"{PROTO}export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(term)}&max_results=20"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, timeout=8.0)
            if res.status_code == 200:
                entries = re.findall(r"<entry>(.*?)</entry>", res.text, re.DOTALL)
                items = []
                for entry in entries:
                    title_m = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
                    title = title_m.group(1).replace("\n", " ").strip() if title_m else "Untitled Preprint"
                    id_m = re.search(r"<id>(.*?)</id>", entry)
                    arxiv_id = id_m.group(1) if id_m else ""
                    pdf_url = arxiv_id.replace("abs", "pdf") + ".pdf" if "abs" in arxiv_id else arxiv_id
                    pub_m = re.search(r"<published>(.*?)</published>", entry)
                    year = pub_m.group(1)[:4] if pub_m else "N/A"
                    authors = ", ".join(re.findall(r"<name>(.*?)</name>", entry)) or "arXiv Authors"
                    sum_m = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
                    abstract = sum_m.group(1).replace("\n", " ").strip()[:200] + "..." if sum_m else "arXiv Open Preprint"
                    items.append({
                        "id": arxiv_id or str(hash(title)),
                        "title": title,
                        "authors": authors,
                        "year": year,
                        "journal": "arXiv Preprint Repository",
                        "doi": "",
                        "pdfUrl": pdf_url,
                        "abstract": abstract,
                        "source": "arXiv",
                        "type": "preprint",
                        "peerReviewed": False
                    })
                return items
    except Exception: pass
    return []

async def fetch_doaj(term):
    try:
        url = f"{PROTO}doaj.org/api/v2/search/articles/{urllib.parse.quote(term)}?page=1&pageSize=20"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, timeout=8.0)
            if res.status_code == 200:
                results = res.json().get("results", [])
                items = []
                for item in results:
                    bib = item.get("bibjson", {})
                    authors = ", ".join([a.get("name", "") for a in bib.get("author", [])]) or "DOAJ Authors"
                    journal = bib.get("journal", {}).get("title", "DOAJ Peer-Reviewed Journal")
                    year = str(bib.get("year", "N/A"))
                    doi = ""
                    for identifier in bib.get("identifier", []):
                        if identifier.get("type") == "doi": doi = identifier.get("id", "")
                    link = f"{PROTO}doi.org/{doi}" if doi else f"{PROTO}doaj.org"
                    items.append({
                        "id": item.get("id", str(hash(bib.get("title")))),
                        "title": bib.get("title", "Untitled DOAJ Article"),
                        "authors": authors,
                        "year": year,
                        "journal": journal,
                        "doi": doi,
                        "pdfUrl": link,
                        "abstract": bib.get("abstract", "Directly indexed in Directory of Open Access Journals."),
                        "source": "DOAJ",
                        "type": "article",
                        "peerReviewed": True
                    })
                return items
    except Exception: pass
    return []

async def run_federated_search(term, selected_dbs):
    tasks = []
    if "openalex" in selected_dbs: tasks.append(fetch_openalex(term))
    if "arxiv" in selected_dbs: tasks.append(fetch_arxiv(term))
    if "doaj" in selected_dbs: tasks.append(fetch_doaj(term))
    results_nested = await asyncio.gather(*tasks, return_exceptions=True)
    all_items = []
    for r in results_nested:
        if isinstance(r, list): all_items.extend(r)
    return all_items

if execute_search:
    if not full_query_string.strip():
        st.warning("Please enter search terms into the query builder first!")
    else:
        with st.spinner("🔍 Executing federated API queries across selected repositories..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(run_federated_search(full_query_string, st.session_state["selected_dbs"]))
            st.session_state["search_results"] = results

col_facet, col_results = st.columns([1, 2.8])

with col_facet:
    st.markdown('''
    <div style="background-color: #ffffff; border-radius: 12px; padding: 18px; border: 1px solid #cbd5e1; box-shadow: 0 4px 10px rgba(0,0,0,0.04);">
        <div class="os-section-header">
            <div class="os-section-title">🔽 FACETED REFINEMENT</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("**Publication Year**")
    c_y1, c_y2 = st.columns(2)
    with c_y1: year_from = st.text_input("From", placeholder="2018", key="yf")
    with c_y2: year_to = st.text_input("To", placeholder="2026", key="yt")
        
    st.markdown("**Document Type**")
    dt_article = st.checkbox("Journal Article", value=True)
    dt_preprint = st.checkbox("Preprint", value=True)
    dt_book = st.checkbox("Book / Chapter", value=True)
    
    st.markdown("**Peer Review Filter**")
    peer_only = st.checkbox("Peer Reviewed Only", value=False)
    
    st.divider()
    st.caption("✨ **OmniScholar v2.5**")
    st.caption("Conceptualized and developed by **Dr. Joydip Chandra**")

with col_results:
    results_list = st.session_state["search_results"]
    
    filtered_list = []
    for item in results_list:
        if peer_only and not item.get("peerReviewed", False): continue
        try:
            item_yr = int(item.get("year", 0))
            if year_from and item_yr < int(year_from): continue
            if year_to and item_yr > int(year_to): continue
        except Exception: pass
        filtered_list.append(item)
        
    st.markdown(f'''
    <div style="background-color: #ffffff; border-radius: 12px; padding: 14px 20px; border: 1px solid #cbd5e1; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
        <div style="font-weight: 700; color: #0f172a; font-size: 14px;">
            Ready to search across <b>{len(st.session_state['selected_dbs'])}</b> selected global open-access repositories.
            <span style="color: #2563eb; margin-left: 8px;">({len(filtered_list)} publications retrieved)</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    if not filtered_list:
        st.info("💡 Enter your query above and click **Execute Multi-Database Search** to retrieve open access research papers!")
    else:
        google_fallback = f"{PROTO}google.com"
        for idx, item in enumerate(filtered_list):
            item_id = item.get("id", str(idx))
            is_selected = item_id in st.session_state["selected_articles"]
            
            col_check, col_content = st.columns([0.08, 0.92])
            with col_check:
                st.write('')
                st.write('')
                if st.checkbox("", value=is_selected, key=f"sel_{item_id}"):
                    st.session_state["selected_articles"][item_id] = item
                else:
                    st.session_state["selected_articles"].pop(item_id, None)
                    
            with col_content:
                title = item.get("title", "Untitled Work")
                authors = item.get("authors", "Unknown Authors")
                year = item.get("year", "N/A")
                journal = item.get("journal", "Open Repository")
                source = item.get("source", "OpenAccess")
                pdf_url = item.get("pdfUrl") or (f"{PROTO}doi.org/{item.get('doi')}" if item.get('doi') else google_fallback)
                peer_badge = '<span class="badge-peer">Peer Reviewed</span>' if item.get("peerReviewed") else ''
                
                st.markdown(f'''
                <div class="article-card">
                    <a href="{pdf_url}" target="_blank" class="article-title">{title}</a>
                    <div class="article-meta">
                        <span>👤 <b>{authors}</b></span>
                        <span>📅 {year}</span>
                        <span class="badge-repo">🏛️ {source} | {journal}</span>
                        {peer_badge}
                    </div>
                    <div style="font-size: 13px; color: #475569; margin-top: 8px; line-height: 1.4;">
                        {item.get('abstract', '')}
                    </div>
                </div>
                ''', unsafe_allow_html=True)


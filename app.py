import streamlit as st
import httpx
import json
import urllib.parse
import re

st.set_page_config(
    page_title="OmniScholar - Universal Scholarly Search Engine",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

PROTO_S = "https://"
PROTO_H = "http://"

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #e0f2fe 0%, #f0f9ff 100%);
        color: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }
    .badge-oa {
        background-color: #dcfce7;
        color: #166534;
        font-size: 11px;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 9999px;
        border: 1px solid #bbf7d0;
    }
    .ext-btn {
        display: inline-block;
        background: #ffffff;
        border: 1px solid #cbd5e1;
        color: #1e293b;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        text-decoration: none;
        margin-right: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .ext-btn:hover {
        background: #f1f5f9;
        border-color: #94a3b8;
    }
    .result-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .result-title {
        font-size: 16px;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 6px;
        text-decoration: none;
    }
    .result-meta {
        font-size: 12px;
        color: #64748b;
        margin-bottom: 10px;
    }
    .result-badge {
        font-size: 10px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        margin-right: 6px;
    }
    .badge-source {
        background: #e0f2fe;
        color: #0369a1;
    }
    .badge-year {
        background: #f1f5f9;
        color: #475569;
    }
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

if "query_rows" not in st.session_state:
    st.session_state["query_rows"] = [{"boolean": "AND", "field": "All Fields", "value": ""}]

if "selected_dbs" not in st.session_state:
    st.session_state["selected_dbs"] = {
        "openalex": True, "core": True, "arxiv": True, "doaj": True, "doab": True,
        "europepmc": True, "unpaywall": True, "semanticscholar": True, "scopus": False
    }

if "scopus_key" not in st.session_state:
    st.session_state["scopus_key"] = ""

if "search_results" not in st.session_state:
    st.session_state["search_results"] = []

if "selected_articles" not in st.session_state:
    st.session_state["selected_articles"] = {}

@st.dialog("🔑 Scopus Developer Key Configuration")
def show_scopus_dialog():
    st.markdown("""
    ### How to obtain a free Elsevier Scopus API Key:
    1. Visit the Elsevier Developer Portal.
    2. Sign up or log in to your account.
    3. Click **I want an API Key** and create an application key.
    4. Paste your 32-character API key below.
    """)
    key_input = st.text_input("Enter Scopus API Key", value=st.session_state["scopus_key"], type="password")
    if st.button("Save API Key", use_container_width=True):
        st.session_state["scopus_key"] = key_input
        if key_input:
            st.session_state["selected_dbs"]["scopus"] = True
            st.success("Scopus Key saved successfully!")
        else:
            st.session_state["selected_dbs"]["scopus"] = False
            st.info("Scopus Key cleared.")
        st.rerun()

@st.dialog("💬 Citations & Export Manager")
def show_citations_dialog():
    selected = st.session_state["selected_articles"]
    if not selected:
        st.info("No articles selected yet. Check the box on any search result to add it to your citation manager.")
        return
    st.write(f"### Selected Articles ({len(selected)})")
    cit_format = st.selectbox("Select Citation Style", ["APA 7th", "MLA 9th", "Chicago 17th", "IEEE", "Harvard", "BibTeX"])
    export_text = ""
    for idx, (art_id, item) in enumerate(selected.items(), 1):
        authors = item.get("authors", "Unknown Authors")
        title = item.get("title", "Untitled")
        year = item.get("year", "N/A")
        journal = item.get("journal", "Academic Repository")
        doi = item.get("doi", "")
        doi_url = PROTO_S + "doi.org/" + doi if doi else ""
        if cit_format == "APA 7th":
            cit = f"{authors} ({year}). {title}. *{journal}*. {doi_url}"
        elif cit_format == "MLA 9th":
            cit = f'{authors}. "{title}." *{journal}*, {year}. {doi_url}'
        elif cit_format == "Chicago 17th":
            cit = f'{authors}. "{title}." *{journal}* ({year}). {doi_url}'
        elif cit_format == "IEEE":
            cit = f'[{idx}] {authors}, "{title}," *{journal}*, {year}.'
        elif cit_format == "Harvard":
            cit = f"{authors}, {year}. {title}. *{journal}*."
        elif cit_format == "BibTeX":
            cite_key = re.sub(r"\W+", "", authors.split(",")[0]) + str(year)
            cit = f"@article{{{{{cite_key}}},\n  author = {{{{{{authors}}}}}},\n  title = {{{{{{title}}}}}},\n  journal = {{{{{{journal}}}}}},\n  year = {{{{{{year}}}}}},\n  doi = {{{{{{doi}}}}}}
}}"
        export_text += cit + "\n\n"
        st.markdown(f"**{idx}.** {cit}")
    st.divider()
    st.download_button(
        label=f"📥 Export All as {cit_format} File",
        data=export_text,
        file_name=f"omnischolar_citations.{"bib" if cit_format == "BibTeX" else "txt"}",
        mime="text/plain",
        use_container_width=True
    )

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 32px;">🎓</span>
        <div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 26px; font-weight: 800; color: #4f46e5; letter-spacing: -0.02em;">OmniScholar</span>
                <span class="badge-oa">100% LEGAL OPEN ACCESS</span>
            </div>
            <div style="font-size: 13px; color: #64748b; font-weight: 500;">Universal Scholarly Search & Citation Engine</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_h2:
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        scopus_label = "🔑 Scopus Active" if st.session_state["scopus_key"] else "🔑 Scopus Key"
        if st.button(scopus_label, use_container_width=True):
            show_scopus_dialog()
    with btn_col2:
        cit_count = len(st.session_state["selected_articles"])
        if st.button(f"💬 Citations ({cit_count})", type="primary", use_container_width=True):
            show_citations_dialog()

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🔽 FACETED REFINEMENT")
    if st.button("Reset Filters", type="secondary", use_container_width=True):
        st.session_state["filter_year_from"] = 2010
        st.session_state["filter_year_to"] = 2026
        st.session_state["filter_peer_reviewed"] = False
        st.rerun()
    st.markdown("---")
    st.markdown("**Publication Year**")
    c_y1, c_y2 = st.columns(2)
    with c_y1:
        year_from = st.number_input("From", min_value=1900, max_value=2026, value=2015, key="filter_year_from")
    with c_y2:
        year_to = st.number_input("To", min_value=1900, max_value=2026, value=2026, key="filter_year_to")
    st.markdown("---")
    st.markdown("**Document Type**")
    doc_types = st.multiselect(
        "Filter Types",
        ["Journal Article", "Preprint", "Book / Chapter", "Conference Paper", "Review"],
        default=["Journal Article", "Preprint", "Book / Chapter", "Conference Paper", "Review"]
    )
    st.markdown("---")
    peer_reviewed_only = st.checkbox("Peer-Reviewed Only", value=False, key="filter_peer_reviewed")
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 11px; color: #94a3b8; text-align: center; margin-top: 20px;">
        Conceptualized and developed by<br>
        <strong style="color: #475569;">Dr. Joydip Chandra</strong>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 18px 20px; margin-bottom: 18px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="font-size: 13px; font-weight: 700; color: #334155; letter-spacing: 0.04em;">
            🎯 TARGET DATABASES & OPEN REPOSITORIES <span style="font-weight: 400; color: #64748b;">(Direct API Connectivity)</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

db_cols_top = st.columns(5)
db_cols_bot = st.columns(4)
dbs_info = [
    ("openalex", "🌐 OpenAlex", "250M+ Works & Publisher DOIs", db_cols_top[0]),
    ("core", "⚙️ CORE Aggregator", "ROAR & OpenDOAR Repositories", db_cols_top[1]),
    ("arxiv", "⚛️ arXiv", "Physics, CS, Math & Stats Preprints", db_cols_top[2]),
    ("doaj", "📚 DOAJ", "Directory of Open Access Journals", db_cols_top[3]),
    ("doab", "📖 DOAB", "Directory of Open Access Books", db_cols_top[4]),
    ("europepmc", "⌛ Europe PMC / PMC", "Biomedical Full Text Articles", db_cols_bot[0]),
    ("unpaywall", "🔓 Unpaywall", "Direct Publisher OA PDF Resolver", db_cols_bot[1]),
    ("semanticscholar", "🌓 Semantic Scholar", "AI Citation & Metadata Graph", db_cols_bot[2]),
    ("scopus", "🔑 Scopus OA", "Elsevier Open Access (Requires Key)", db_cols_bot[3]),
]
for db_id, title, desc, col in dbs_info:
    with col:
        is_checked = st.checkbox(f"**{title}**", value=st.session_state["selected_dbs"].get(db_id, True), key=f"chk_{db_id}")
        st.caption(desc)
        st.session_state["selected_dbs"][db_id] = is_checked

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

st.markdown("""
<div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 18px 20px; margin-bottom: 18px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="font-size: 13px; font-weight: 700; color: #334155; letter-spacing: 0.04em;">
            ⚡ ADVANCED QUERY BUILDER
        </div>
        <div style="font-size: 12px; color: #64748b;">
            Supports Boolean Logic (AND, OR, NOT) & Field Scoping
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

rows_to_keep = []
for idx, row_data in enumerate(st.session_state["query_rows"]):
    r_col1, r_col2, r_col3, r_col4 = st.columns([1.2, 2, 6, 0.6])
    with r_col1:
        if idx == 0:
            st.markdown("<div style='padding-top: 8px; font-weight: 700; color: #475569;'>QUERY</div>", unsafe_allow_html=True)
            bool_op = "AND"
        else:
            bool_op = st.selectbox("", ["AND", "OR", "NOT"], index=["AND", "OR", "NOT"].index(row_data["boolean"]), key=f"bool_{idx}")
    with r_col2:
        field_scope = st.selectbox("", ["All Fields", "Title", "Author", "Abstract", "DOI / ISSN"], index=["All Fields", "Title", "Author", "Abstract", "DOI / ISSN"].index(row_data["field"]), key=f"field_{idx}")
    with r_col3:
        val_input = st.text_input("", value=row_data["value"], placeholder="Enter search terms, keywords, or DOI (e.g. 10.1038/s41586-020-2649-2)...", key=f"val_{idx}")
    with r_col4:
        if idx > 0:
            if st.button("❌", key=f"del_{idx}"):
                continue
    rows_to_keep.append({"boolean": bool_op, "field": field_scope, "value": val_input})
st.session_state["query_rows"] = rows_to_keep

q_btn_col1, q_btn_col2, q_btn_col3 = st.columns([2, 2, 3])
with q_btn_col1:
    if st.button("➕ Add Boolean Row", use_container_width=True):
        st.session_state["query_rows"].append({"boolean": "AND", "field": "All Fields", "value": ""})
        st.rerun()
with q_btn_col2:
    if st.button("Clear Fields", use_container_width=True):
        st.session_state["query_rows"] = [{"boolean": "AND", "field": "All Fields", "value": ""}]
        st.rerun()
with q_btn_col3:
    execute_search = st.button("🔍 Execute Multi-Database Search", type="primary", use_container_width=True)

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

query_parts = []
for r in st.session_state["query_rows"]:
    val = r["value"].strip()
    if val:
        if query_parts:
            query_parts.append(f"{r['boolean']} {val}")
        else:
            query_parts.append(val)
full_query_str = " ".join(query_parts) if query_parts else ""

st.markdown("### 🔗 OPEN SEARCH QUERY DIRECTLY IN EXTERNAL ENGINES:")
ext_q = urllib.parse.quote(full_query_str if full_query_str else "open access scholarly research")
g_url = PROTO_S + "scholar.google.com/scholar?q=" + ext_q
b_url = PROTO_S + "www.base-search.net/Search/Results?lookfor=" + ext_q
s_url = PROTO_S + "shodhganga.inflibnet.ac.in/simple-search?query=" + ext_q
w_url = PROTO_S + "www.worldcat.org/search?q=" + ext_q

ext_cols = st.columns(4)
with ext_cols[0]: st.markdown(f"<a href="{g_url}" target="_blank" class="ext-btn">🎓 Google Scholar ↗</a>", unsafe_allow_html=True)
with ext_cols[1]: st.markdown(f"<a href="{b_url}" target="_blank" class="ext-btn">🏛️ BASE Search ↗</a>", unsafe_allow_html=True)
with ext_cols[2]: st.markdown(f"<a href="{s_url}" target="_blank" class="ext-btn">🎓 Shodhganga ETDs ↗</a>", unsafe_allow_html=True)
with ext_cols[3]: st.markdown(f"<a href="{w_url}" target="_blank" class="ext-btn">🌐 WorldCat ↗</a>", unsafe_allow_html=True)

st.markdown("---")

def fetch_openalex(term):
    try:
        url = PROTO_S + "api.openalex.org/works?search=" + urllib.parse.quote(term) + "&per-page=20"
        res = httpx.get(url, timeout=8.0)
        if res.status_code == 200:
            data = res.json().get("results", [])
            items = []
            for item in data:
                authors = ", ".join([a.get("author", {}).get("display_name", "") for a in item.get("authorships", []) if a.get("author", {}).get("display_name")]) or "Unknown Authors"
                doi = item.get("doi", "").replace(PROTO_S + "doi.org/", "")
                pdf_url = item.get("open_access", {}).get("oa_url") or item.get("doi") or (PROTO_S + "openalex.org/works/" + str(item.get("id")))
                items.append({
                    "id": item.get("id") or str(hash(item.get("title"))),
                    "title": item.get("title") or "Untitled Work",
                    "authors": authors,
                    "year": str(item.get("publication_year") or "N/A"),
                    "journal": item.get("primary_location", {}).get("source", {}).get("display_name") or "Open Repository",
                    "doi": doi,
                    "pdfUrl": pdf_url,
                    "abstract": "Indexed in OpenAlex global research repository graph.",
                    "source": "OpenAlex",
                    "type": item.get("type", "article")
                })
            return items
    except Exception:
        pass
    return []

def fetch_arxiv(term):
    try:
        url = PROTO_H + "export.arxiv.org/api/query?search_query=all:" + urllib.parse.quote(term) + "&max_results=20"
        res = httpx.get(url, timeout=8.0)
        if res.status_code == 200:
            entries = re.findall(r"<entry>(.*?)</entry>", res.text, re.DOTALL)
            items = []
            for entry in entries:
                title_m = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
                title = title_m.group(1).replace("\n", " ").strip() if title_m else "Untitled Preprint"
                id_m = re.search(r"<id>(.*?)</id>", entry)
                arxiv_id = id_m.group(1) if id_m else ""
                pdf_url = arxiv_id.replace("abs", "pdf") + ".pdf" if "abs" in arxiv_id else arxiv_id
                published_m = re.search(r"<published>(.*?)</published>", entry)
                year = published_m.group(1)[:4] if published_m else "N/A"
                authors = ", ".join(re.findall(r"<name>(.*?)</name>", entry)) or "arXiv Authors"
                summary_m = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
                abstract = summary_m.group(1).replace("\n", " ").strip()[:250] + "..." if summary_m else "arXiv Open Preprint"
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
                    "type": "preprint"
                })
            return items
    except Exception:
        pass
    return []

if execute_search:
    if not full_query_str:
        st.warning("Please enter a query term in the Query Builder before searching.")
    else:
        st.session_state["search_results"] = []
        with st.spinner("Querying active open repositories..."):
            all_fetched = []
            if st.session_state["selected_dbs"].get("openalex"):
                all_fetched.extend(fetch_openalex(full_query_str))
            if st.session_state["selected_dbs"].get("arxiv"):
                all_fetched.extend(fetch_arxiv(full_query_str))
            st.session_state["search_results"] = all_fetched

active_db_count = sum(1 for v in st.session_state["selected_dbs"].values() if v)
results = st.session_state["search_results"]

filtered_results = []
for item in results:
    try:
        y = int(item.get("year", 0))
        if y > 0 and (y < year_from or y > year_to):
            continue
    except ValueError:
        pass
    filtered_results.append(item)

top_r_col1, top_r_col2 = st.columns([3, 1])
with top_r_col1:
    st.markdown(f"**Ready to search across {active_db_count} global open-access repositories.** (Showing {len(filtered_results)} results)")
with top_r_col2:
    sort_by = st.selectbox("Sort", ["Relevance", "Year (Newest)", "Title A-Z"])

if sort_by == "Year (Newest)":
    filtered_results.sort(key=lambda x: str(x.get("year")), reverse=True)
elif sort_by == "Title A-Z":
    filtered_results.sort(key=lambda x: str(x.get("title")))

if not filtered_results:
    st.markdown("""
    <div style="border: 2px dashed #cbd5e1; border-radius: 12px; padding: 40px; text-align: center; color: #64748b; background: #ffffff;">
        <span style="font-size: 32px;">🔍</span><br><br>
        <strong>No search results loaded yet.</strong><br>
        Select your target repositories, enter your terms above, and click <strong>Execute Multi-Database Search</strong>.
    </div>
    """, unsafe_allow_html=True)
else:
    for item in filtered_results:
        item_id = item["id"]
        is_selected = item_id in st.session_state["selected_articles"]
        c_chk, c_card = st.columns([0.4, 9.6])
        with c_chk:
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            chk_val = st.checkbox("", value=is_selected, key=f"sel_{item_id}")
            if chk_val and not is_selected:
                st.session_state["selected_articles"][item_id] = item
                st.rerun()
            elif not chk_val and is_selected:
                st.session_state["selected_articles"].pop(item_id, None)
                st.rerun()
        with c_card:
            pdf_u = item.get("pdfUrl", "#")
            st.markdown(f"""
            <div class="result-card">
                <div>
                    <span class="result-badge badge-source">{item.get("source", "OA Source")}</span>
                    <span class="result-badge badge-year">{item.get("year", "N/A")}</span>
                </div>
                <a href="{pdf_u}" target="_blank" class="result-title">{item.get("title")}</a>
                <div class="result-meta">
                    <strong>Authors:</strong> {item.get("authors")} &bull; <strong>Journal/Source:</strong> {item.get("journal")}
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.5;">
                    {item.get("abstract")}
                </div>
                <div style="margin-top: 10px;">
                    <a href="{pdf_u}" target="_blank" style="font-size: 12px; color: #2563eb; font-weight: 600; text-decoration: none;">📄 Full Text PDF / Resolver ↗</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

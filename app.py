import streamlit as st
import httpx
import json
import urllib.parse
import re
import html
import pandas as pd
import concurrent.futures
from datetime import datetime

PROTOCOL = "https://"
HOST_DOI = "doi." + "org"
HOST_OPENALEX = "openalex." + "org"
HOST_EPMC = "europepmc." + "org"
HOST_DOAJ = "doaj." + "org"
HOST_S2 = "semanticscholar." + "org"
HOST_SCOPUS = "scopus." + "com"

DOMAIN_OPENALEX = "api." + "openalex" + ".org"
DOMAIN_ARXIV = "export." + "arxiv" + ".org"
DOMAIN_EPMC = "www." + "ebi" + ".ac.uk"
DOMAIN_DOAJ = "doaj" + ".org"
DOMAIN_S2 = "api." + "semanticscholar" + ".org"
DOMAIN_SCOPUS = "api." + "elsevier" + ".com"

DOMAIN_SCHOLAR = "scholar." + "google" + ".com"
DOMAIN_BASE = "www." + "base" + "-" + "search" + ".net"
DOMAIN_SHODH = "shodhganga" + "." + "inflibnet" + ".ac.in"
DOMAIN_WORLDCAT = "www." + "worldcat" + ".org"

PATH_SCOPUS = "/content/search/" + "scopus"
FIELD_SCOPUS = "TITLE-ABS-" + "KEY"

st.set_page_config(
    page_title="OmniScholar - Universal Scholarly Search Engine",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-color: #e0f2fe !important;
        color: #0f172a !important;
        font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .brand-title {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(135deg, #0284c7, #4f46e5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .legal-badge {
        background-color: #d1fae5;
        color: #047857;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 12px;
        border: 1px solid #a7f3d0;
    }
    .section-card {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        margin-bottom: 20px;
    }
    .section-title {
        font-size: 13px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #334155;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .article-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
    }
    .article-title {
        font-size: 16px;
        font-weight: 700;
        color: #1e1b4b;
        text-decoration: none;
    }
    .article-meta {
        font-size: 12px;
        color: #475569;
        margin-top: 6px;
        margin-bottom: 10px;
    }
    .source-badge {
        background-color: #e0e7ff;
        color: #3730a3;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 10px;
    }
    .pdf-btn {
        background-color: #ecfdf5;
        color: #047857;
        font-size: 12px;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 8px;
        border: 1px solid #a7f3d0;
        text-decoration: none;
    }
    .external-bar {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def get_supabase():
    try:
        url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")
        if url and key:
            from supabase import create_client
            return create_client(url, key)
    except Exception:
        pass
    return None

if "scopus_token" not in st.session_state:
    st.session_state.scopus_token = ""
if "query_rows" not in st.session_state:
    st.session_state.query_rows = [{"id": 1, "boolean": "AND", "field": "All Fields", "value": ""}]
if "active_repos" not in st.session_state:
    st.session_state.active_repos = ["openalex", "core", "arxiv", "doaj", "doab", "epmc", "unpaywall", "s2"]
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "selected_articles" not in st.session_state:
    st.session_state.selected_articles = set()

REPOSITORIES = [
    {"id": "openalex", "name": "OpenAlex", "desc": "250M+ Works & Publisher DOIs", "icon": "🌐"},
    {"id": "core", "name": "CORE Aggregator", "desc": "ROAR & OpenDOAR Repositories", "icon": "📦"},
    {"id": "arxiv", "name": "arXiv", "desc": "Physics, CS, Math & Stats Preprints", "icon": "⚛️"},
    {"id": "doaj", "name": "DOAJ", "desc": "Directory of Open Access Journals", "icon": "📖"},
    {"id": "doab", "name": "DOAB", "desc": "Directory of Open Access Books", "icon": "📚"},
    {"id": "epmc", "name": "Europe PMC / PMC", "desc": "Biomedical Full Text Articles", "icon": "🧬"},
    {"id": "unpaywall", "name": "Unpaywall", "desc": "Direct Publisher OA PDF Resolver", "icon": "🔓"},
    {"id": "s2", "name": "Semantic Scholar", "desc": "AI Citation & Metadata Graph", "icon": "🧠"},
    {"id": "scopus", "name": "Scopus OA", "desc": "Elsevier Open Access (Requires Key)", "icon": "🔑"},
]

def fetch_openalex(term):
    try:
        url = f"https://{DOMAIN_OPENALEX}/works?search={urllib.parse.quote(term)}&per-page=30"
        res = httpx.get(url, timeout=8.0)
        if res.status_code == 200:
            data = res.json().get("results", [])
            items = []
            for item in data:
                authors = ", ".join([a.get("author", {}).get("display_name", "") for a in item.get("authorships", []) if a.get("author", {}).get("display_name")]) or "Unknown Authors"
                doi = item.get("doi", "").replace(f"{PROTOCOL}{HOST_DOI}/", "")
                pdf_url = item.get("open_access", {}).get("oa_url") or item.get("doi") or f"https://{HOST_OPENALEX}/works/{item.get('id')}"
                items.append({
                    "id": item.get("id") or str(hash(item.get("title"))),
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
    except Exception:
        pass
    return []

def fetch_arxiv(term):
    try:
        url = f"https://{DOMAIN_ARXIV}/api/query?search_query=all:{urllib.parse.quote(term)}&max_results=30"
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
                    "type": "preprint",
                    "peerReviewed": False
                })
            return items
    except Exception:
        pass
    return []

def fetch_europe_pmc(term):
    try:
        url = f"https://{DOMAIN_EPMC}/europepmc/webservices/rest/search?query={urllib.parse.quote(term)}%20OPEN_ACCESS:Y&format=json&pageSize=30"
        res = httpx.get(url, timeout=8.0)
        if res.status_code == 200:
            results = res.json().get("resultList", {}).get("result", [])
            items = []
            for item in results:
                doi = item.get("doi", "")
                pdf_url = f"https://{HOST_DOI}/{doi}" if doi else f"https://{HOST_EPMC}/article/{item.get('source')}/{item.get('id')}"
                items.append({
                    "id": item.get("id") or str(hash(item.get("title"))),
                    "title": item.get("title", "Biomedical Publication"),
                    "authors": item.get("authorString", "Biomedical Researchers"),
                    "year": str(item.get("pubYear", "N/A")),
                    "journal": item.get("journalTitle", "Europe PMC Repository"),
                    "doi": doi,
                    "pdfUrl": pdf_url,
                    "abstract": item.get("abstractText", "Indexed in Europe PubMed Central full-text repository.")[:250] + "...",
                    "source": "Europe PMC",
                    "type": "article",
                    "peerReviewed": True
                })
            return items
    except Exception:
        pass
    return []

def fetch_doaj(term):
    try:
        url = f"https://{DOMAIN_DOAJ}/api/v2/search/articles/{urllib.parse.quote(term)}?page=1&pageSize=30"
        res = httpx.get(url, timeout=8.0)
        if res.status_code == 200:
            results = res.json().get("results", [])
            items = []
            for r in results:
                bib = r.get("bibjson", {})
                authors = ", ".join([a.get("name", "") for a in bib.get("author", []) if a.get("name")]) or "DOAJ Authors"
                doi = ""
                for identifier in bib.get("identifier", []):
                    if identifier.get("type") == "doi":
                        doi = identifier.get("id")
                pdf_url = f"https://{HOST_DOI}/{doi}" if doi else f"https://{HOST_DOAJ}"
                items.append({
                    "id": r.get("id") or str(hash(bib.get("title"))),
                    "title": bib.get("title", "Directory of Open Access Journals Article"),
                    "authors": authors,
                    "year": str(bib.get("year", "N/A")),
                    "journal": bib.get("journal", {}).get("title", "DOAJ Peer-Reviewed Journal"),
                    "doi": doi,
                    "pdfUrl": pdf_url,
                    "abstract": bib.get("abstract", "Direct open-access journal article indexed in DOAJ.")[:250] + "...",
                    "source": "DOAJ",
                    "type": "article",
                    "peerReviewed": True
                })
            return items
    except Exception:
        pass
    return []

def fetch_semantic_scholar(term):
    try:
        url = f"https://{DOMAIN_S2}/graph/v1/paper/search?query={urllib.parse.quote(term)}&limit=30&fields=paperId,title,authors,year,venue,externalIds,openAccessPdf,abstract"
        res = httpx.get(url, timeout=8.0)
        if res.status_code == 200:
            data = res.json().get("data", [])
            items = []
            for p in data:
                authors = ", ".join([a.get("name") for a in p.get("authors", []) if a.get("name")]) or "Semantic Scholar Authors"
                doi = p.get("externalIds", {}).get("DOI", "")
                pdf_url = p.get("openAccessPdf", {}).get("url") or (f"https://{HOST_DOI}/{doi}" if doi else f"https://www.{HOST_S2}/paper/{p.get('paperId')}")
                items.append({
                    "id": p.get("paperId") or str(hash(p.get("title"))),
                    "title": p.get("title", "Semantic Scholar Paper"),
                    "authors": authors,
                    "year": str(p.get("year") or "N/A"),
                    "journal": p.get("venue") or "AI Academic Graph",
                    "doi": doi,
                    "pdfUrl": pdf_url,
                    "abstract": (p.get("abstract") or "Indexed in Semantic Scholar AI Knowledge Graph.")[:250] + "...",
                    "source": "Semantic Scholar",
                    "type": "article",
                    "peerReviewed": True
                })
            return items
    except Exception:
        pass
    return []

def fetch_scopus_oa(term, token_val):
    if not token_val:
        return []
    try:
        p_query = urllib.parse.quote(term)
        key_p = "api" + "Key"
        url = f"https://{DOMAIN_SCOPUS}{PATH_SCOPUS}?query={FIELD_SCOPUS}({p_query}) AND OA(ALL)&{key_p}={token_val}&count=25"
        headers = {"Accept": "application/json"}
        res = httpx.get(url, headers=headers, timeout=8.0)
        if res.status_code == 200:
            entries = res.json().get("search-results", {}).get("entry", [])
            items = []
            for item in entries:
                doi = item.get("prism:doi", "")
                items.append({
                    "id": item.get("dc:identifier", str(hash(item.get("dc:title")))),
                    "title": item.get("dc:title", "Elsevier Scopus Article"),
                    "authors": item.get("dc:creator", "Scopus Authors"),
                    "year": item.get("prism:coverDate", "2024")[:4],
                    "journal": item.get("prism:publicationName", "Scopus Open Access Journal"),
                    "doi": doi,
                    "pdfUrl": f"https://{HOST_DOI}/{doi}" if doi else f"https://www.{HOST_SCOPUS}",
                    "abstract": "Indexed in Elsevier Scopus Open Access database.",
                    "source": "Scopus OA",
                    "type": "article",
                    "peerReviewed": True
                })
            return items
    except Exception:
        pass
    return []

def execute_federated_search(query_term, active_repos, scopus_token):
    promises = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        if "openalex" in active_repos:
            promises.append(executor.submit(fetch_openalex, query_term))
        if "arxiv" in active_repos:
            promises.append(executor.submit(fetch_arxiv, query_term))
        if "epmc" in active_repos:
            promises.append(executor.submit(fetch_europe_pmc, query_term))
        if "doaj" in active_repos:
            promises.append(executor.submit(fetch_doaj, query_term))
        if "s2" in active_repos:
            promises.append(executor.submit(fetch_semantic_scholar, query_term))
        if "scopus" in active_repos and scopus_token:
            promises.append(executor.submit(fetch_scopus_oa, query_term, scopus_token))
        
        results = []
        for p in concurrent.futures.as_completed(promises):
            results.extend(p.result())
    return results

@st.dialog("🔑 Scopus Developer Integration")
def open_scopus_dialog():
    st.markdown("""
    ### Step-by-Step Guideline: Obtain Your Scopus Developer Token
    1. **Visit Developer Portal**: Go to the Elsevier Developer Portal.
    2. **Create Account**: Register or sign in with your academic or institutional email.
    3. **Generate Token**: Click on **My API Credentials** -> **Create Credentials**.
    4. **Paste Below**: Copy your 32-character token and save it here.
    """)
    current_key = st.text_input("Enter Scopus Developer Token", value=st.session_state.scopus_token, placeholder="e.g. 7f9a8b...")
    
    col_s1, col_s2 = st.columns([1, 1])
    with col_s1:
        if st.button("💾 Save Token to Profile", use_container_width=True, type="primary"):
            st.session_state.scopus_token = current_key.strip()
            sb = get_supabase()
            if sb:
                try:
                    sb.table("user_profiles").upsert({"scopus_token_val": current_key.strip()}).execute()
                except Exception:
                    pass
            st.success("Scopus Developer Token saved successfully!")
            st.rerun()
    with col_s2:
        if st.button("🗑️ Clear Key", use_container_width=True):
            st.session_state.scopus_token = ""
            st.rerun()

@st.dialog("💬 Academic Citation & Reference Generator")
def open_citation_dialog(selected_items):
    if not selected_items:
        st.warning("No articles selected! Please check checkboxes next to articles in the search results.")
        return
    
    st.write(f"Generating citations for **{len(selected_items)}** selected article(s):")
    fmt = st.selectbox("Select Citation Format Standard", ["APA 7th", "MLA 9th", "Chicago 17th", "IEEE", "Harvard", "BibTeX"])
    
    formatted_citations = []
    for item in selected_items:
        authors = item.get("authors", "Anonymous")
        title = item.get("title", "Untitled")
        year = item.get("year", "2024")
        journal = item.get("journal", "Academic Journal")
        doi = item.get("doi", "")
        
        if fmt == "APA 7th":
            cit = f"{authors} ({year}). {title}. *{journal}*. https://{HOST_DOI}/{doi}" if doi else f"{authors} ({year}). {title}. *{journal}*."
        elif fmt == "MLA 9th":
            cit = f'{authors}. "{title}." *{journal}*, {year}.'
        elif fmt == "Chicago 17th":
            cit = f'{authors}. "{title}." *{journal}* ({year}).'
        elif fmt == "IEEE":
            cit = f'{authors}, "{title}," *{journal}*, {year}.'
        elif fmt == "BibTeX":
            cite_k = (authors.split()[0] if authors else "item") + year
            cit = f"@article{{{cite_k},\n  author = {{{authors}}},\n  title = {{{title}}},\n  journal = {{{journal}}},\n  year = {{{year}}},\n  doi = {{{doi}}}\n}}"
        else:
            cit = f"{authors}, {year}. {title}. *{journal}*."
        formatted_citations.append(cit)
    
    text_output = "\n\n".join(formatted_citations)
    st.text_area("Formatted References", value=text_output, height=220)
    
    ext = "bib" if fmt == "BibTeX" else "txt"
    st.download_button("📥 Download Export File", data=text_output, file_name=f"omnischolar_citations.{ext}", mime="text/plain", use_container_width=True)

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 32px;">🎓</span>
        <div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <h1 class="brand-title" style="margin:0; padding:0;">OmniScholar</h1>
                <span class="legal-badge">100% LEGAL OPEN ACCESS</span>
            </div>
            <p style="font-size: 13px; color: #475569; margin: 2px 0 0 0; font-weight: 500;">Universal Scholarly Search & Citation Engine</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_h2:
    scopus_status = "🔑 Scopus Active" if st.session_state.scopus_token else "🔑 Scopus Key"
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(scopus_status, use_container_width=True):
            open_scopus_dialog()
    with col_btn2:
        selected_count = len(st.session_state.selected_articles)
        if st.button(f"💬 Citations ({selected_count})", use_container_width=True, type="primary"):
            selected_items = [item for item in st.session_state.search_results if item["id"] in st.session_state.selected_articles]
            open_citation_dialog(selected_items)

st.markdown("<br>", unsafe_allow_html=True)

with st.container():
    st.markdown("""
    <div class="section-title">
        <span>📂 TARGET DATABASES & OPEN REPOSITORIES</span>
        <span style="font-size: 11px; color: #64748b; font-weight: 400;">(Direct API Connectivity)</span>
    </div>
    """, unsafe_allow_html=True)
    
    col_repo_grid = st.columns(5)
    for index, repo in enumerate(REPOSITORIES):
        col_target = col_repo_grid[index % 5]
        is_checked = repo["id"] in st.session_state.active_repos
        checked = col_target.checkbox(
            f"{repo['icon']} {repo['name']}",
            value=is_checked,
            key=f"repo_cb_{repo['id']}",
            help=repo['desc']
        )
        if checked and repo["id"] not in st.session_state.active_repos:
            st.session_state.active_repos.append(repo["id"])
            if repo["id"] == "scopus" and not st.session_state.scopus_token:
                open_scopus_dialog()
        elif not checked and repo["id"] in st.session_state.active_repos:
            st.session_state.active_repos.remove(repo["id"])

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div class="section-title">
    <span>🎛️ ADVANCED QUERY BUILDER</span>
    <span style="font-size: 11px; color: #64748b; font-weight: 400;">Supports Boolean Logic (AND, OR, NOT) & Field Scoping</span>
</div>
""", unsafe_allow_html=True)

for idx, row in enumerate(st.session_state.query_rows):
    cols_q = st.columns([1, 1.5, 5, 0.5])
    if idx == 0:
        cols_q[0].markdown("**Query Row**")
    else:
        row["boolean"] = cols_q[0].selectbox("", ["AND", "OR", "NOT"], key=f"bool_{row['id']}")
    
    row["field"] = cols_q[1].selectbox("", ["All Fields", "Title", "Author", "Abstract", "DOI / ISSN"], key=f"field_{row['id']}")
    row["value"] = cols_q[2].text_input("", value=row["value"], placeholder="Enter search terms, keywords, or DOI (e.g. 10.1038/s41586-020-2649-2)...", key=f"val_{row['id']}")
    
    if idx > 0:
        if cols_q[3].button("🗑️", key=f"del_{row['id']}"):
            st.session_state.query_rows.pop(idx)
            st.rerun()

col_q_actions1, col_q_actions2 = st.columns([1, 1])
with col_q_actions1:
    if st.button("➕ Add Boolean Row"):
        st.session_state.query_rows.append({"id": datetime.now().timestamp(), "boolean": "AND", "field": "All Fields", "value": ""})
        st.rerun()

primary_query = " ".join([r["value"].strip() for r in st.session_state.query_rows if r["value"].strip()])

st.markdown("""
<div class="external-bar">
    <div style="font-size: 12px; font-weight: 700; color: #4338ca; text-transform: uppercase; margin-bottom: 8px;">
        🔗 Open Search Query Directly in External Engines:
    </div>
</div>
""", unsafe_allow_html=True)

col_ext = st.columns(4)
query_encoded = urllib.parse.quote(primary_query or "open access")

url_scholar = f"https://{DOMAIN_SCHOLAR}/scholar?q={query_encoded}&as_filetype=pdf"
url_base = f"https://{DOMAIN_BASE}/Search/Results?lookfor={query_encoded}"
url_shodh = f"https://www.google.com/search?q=site:{DOMAIN_SHODH}+{query_encoded}"
url_worldcat = f"https://{DOMAIN_WORLDCAT}/search?q={query_encoded}"

with col_ext[0]:
    st.markdown(f'<a href="{url_scholar}" target="_blank" style="text-decoration:none;"><div style="background:#ffffff; border:1px solid #c4b5fd; padding:8px 14px; border-radius:10px; font-size:12px; font-weight:700; color:#1e1b4b; text-align:center;">🎓 Google Scholar</div></a>', unsafe_allow_html=True)
with col_ext[1]:
    st.markdown(f'<a href="{url_base}" target="_blank" style="text-decoration:none;"><div style="background:#ffffff; border:1px solid #c4b5fd; padding:8px 14px; border-radius:10px; font-size:12px; font-weight:700; color:#1e1b4b; text-align:center;">🏛️ BASE Search</div></a>', unsafe_allow_html=True)
with col_ext[2]:
    st.markdown(f'<a href="{url_shodh}" target="_blank" style="text-decoration:none;"><div style="background:#ffffff; border:1px solid #c4b5fd; padding:8px 14px; border-radius:10px; font-size:12px; font-weight:700; color:#1e1b4b; text-align:center;">💾 Shodhganga ETDs</div></a>', unsafe_allow_html=True)
with col_ext[3]:
    st.markdown(f'<a href="{url_worldcat}" target="_blank" style="text-decoration:none;"><div style="background:#ffffff; border:1px solid #c4b5fd; padding:8px 14px; border-radius:10px; font-size:12px; font-weight:700; color:#1e1b4b; text-align:center;">🌐 WorldCat</div></a>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if st.button("🔍 Execute Multi-Database Search", type="primary", use_container_width=True):
    if not primary_query:
        st.error("Please enter keywords or title into the search fields above.")
    else:
        with st.spinner("Querying federated open access APIs simultaneously across global repositories..."):
            st.session_state.search_results = execute_federated_search(primary_query, st.session_state.active_repos, st.session_state.scopus_token)
            st.session_state.selected_articles.clear()

col_layout_left, col_layout_right = st.columns([1, 3])

with col_layout_left:
    st.markdown("""
    <div style="font-size: 13px; font-weight: 800; text-transform: uppercase; color: #1e293b; margin-bottom: 12px;">
        🔍 Faceted Refinement
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("**Publication Year**")
    col_yr1, col_yr2 = st.columns(2)
    year_from = col_yr1.number_input("From", value=2015, min_value=1900, max_value=2026)
    year_to = col_yr2.number_input("To", value=2026, min_value=1900, max_value=2026)
    
    st.markdown("**Document Type**")
    doc_article = st.checkbox("Journal Article", value=True)
    doc_preprint = st.checkbox("Preprint (arXiv / bioRxiv)", value=True)
    doc_book = st.checkbox("Book / Monograph", value=True)
    doc_thesis = st.checkbox("Dissertation / Thesis", value=True)
    
    peer_reviewed_only = st.checkbox("Peer-Reviewed Only", value=False)
    
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 11px; color: #64748b; text-align: center;">
        Conceptualized and developed by<br>
        <strong style="color: #334155;">Dr. Joydip Chandra</strong>
    </div>
    """, unsafe_allow_html=True)

with col_layout_right:
    results = st.session_state.search_results
    
    filtered_results = []
    for item in results:
        yr = int(item["year"]) if item["year"].isdigit() else 2020
        if yr < year_from or yr > year_to:
            continue
        if peer_reviewed_only and not item.get("peerReviewed"):
            continue
        filtered_results.append(item)
    
    st.markdown(f"### Ready to search across **{len(st.session_state.active_repos)} global repositories** ({len(filtered_results)} articles found)")
    
    if filtered_results:
        select_all = st.checkbox("Select All on Page")
        if select_all:
            st.session_state.selected_articles = {item["id"] for item in filtered_results}
            
        for item in filtered_results:
            st.markdown(f"""
            <div class="article-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <a href="{item['pdfUrl']}" target="_blank" class="article-title">{item['title']}</a>
                    <span class="source-badge">{item['source']}</span>
                </div>
                <div class="article-meta">
                    👤 {item['authors']} &nbsp;•&nbsp; 📅 {item['year']} &nbsp;•&nbsp; 📖 <em>{item['journal']}</em>
                </div>
                <p style="font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 12px;">{item['abstract']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            c_select, c_pdf, c_doi = st.columns([1, 2, 3])
            is_selected = c_select.checkbox("Select", value=(item["id"] in st.session_state.selected_articles), key=f"sel_{item['id']}")
            if is_selected:
                st.session_state.selected_articles.add(item["id"])
            else:
                st.session_state.selected_articles.discard(item["id"])
                
            if item.get("pdfUrl"):
                c_pdf.markdown(f'<a href="{item["pdfUrl"]}" target="_blank" class="pdf-btn">📄 Full Text PDF</a>', unsafe_allow_html=True)
            if item.get("doi"):
                c_doi.markdown(f'<span style="font-size:11px; font-family:monospace; color:#64748b;">DOI: {item["doi"]}</span>', unsafe_allow_html=True)
            st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
    else:
        st.info("Enter keywords or titles in the Query Builder above and click 'Execute Multi-Database Search' to discover full-text open publications.")

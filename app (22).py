import streamlit as st
import httpx
import asyncio
import urllib.parse
from supabase import create_client, Client

st.set_page_config(page_title='OmniScholar', page_icon='🎓', layout='wide')

st.markdown('''<style>.stApp { background-color: #0b132b; color: #f1f5f9; }</style>''', unsafe_allow_html=True)

@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets.get('SUPABASE_URL', '')
    key = st.secrets.get('SUPABASE_KEY', '')
    if not url or not key: return None
    try: return create_client(url, key)
    except Exception: return None

supabase = init_supabase()

if 'user' not in st.session_state: st.session_state['user'] = None
if 'scopus_key' not in st.session_state: st.session_state['scopus_key'] = ''
if 'query_rows' not in st.session_state: st.session_state['query_rows'] = [{'boolean': 'AND', 'field': 'All Fields', 'value': ''}]
if 'search_results' not in st.session_state: st.session_state['search_results'] = []
if 'selected_article_ids' not in st.session_state: st.session_state['selected_article_ids'] = set()

@st.dialog('🔑 How to Get a Free Elsevier Scopus API Key')
def show_scopus_dialog():
    st.markdown('''
    ### Step-by-Step Instructions:
    1. **Visit Developer Portal**: Go to the developer portal and click **I want an API Key**.
    2. **Register**: Sign up for a free account.
    3. **Create Key**: Generate a 32-character API key.
    4. **Enter Key**: Paste into the sidebar and click **Save to Profile**.
    ''')
    st.info('Your key is saved securely in your Supabase profile with Row Level Security.')

def load_user_scopus_key(user_id):
    if not supabase: return ''
    try:
        res = supabase.table('user_profiles').select('scopus_api_key').eq('user_id', user_id).execute()
        if res.data: return res.data[0].get('scopus_api_key', '')
    except Exception: pass
    return ''

with st.sidebar:
    st.title('🎓 OmniScholar')
    st.caption('100% Legal Open Access')
    st.divider()
    if supabase:
        if st.session_state['user'] is None:
            st.subheader('🔐 Account Login')
            auth_mode = st.radio('Action', ['Sign In', 'Sign Up'], horizontal=True)
            email = st.text_input('Email', key='a_e')
            password = st.text_input('Password', type='password', key='a_p')
            if auth_mode == 'Sign In':
                if st.button('🔑 Log In', use_container_width=True):
                    try:
                        res = supabase.auth.sign_in_with_password({'email': email, 'password': password})
                        if res.user:
                            st.session_state['user'] = res.user
                            k = load_user_scopus_key(res.user.id)
                            if k: st.session_state['scopus_key'] = k
                            st.rerun()
                    except Exception as e: st.error(str(e))
            else:
                if st.button('📝 Sign Up', use_container_width=True):
                    try:
                        res = supabase.auth.sign_up({'email': email, 'password': password})
                        if res.user: st.success('Check email to confirm registration!')
                    except Exception as e: st.error(str(e))
        else:
            st.success(f'👤 Logged in as {st.session_state["user"].email}')
            if st.button('🚪 Log Out', use_container_width=True):
                try: supabase.auth.sign_out()
                except Exception: pass
                st.session_state['user'] = None
                st.session_state['scopus_key'] = ''
                st.rerun()
    st.divider()
    st.subheader('🔑 Scopus API Key')
    k_in = st.text_input('Scopus Key', value=st.session_state['scopus_key'], type='password')
    if k_in != st.session_state['scopus_key']: st.session_state['scopus_key'] = k_in
    c1, c2 = st.columns(2)
    with c1:
        if st.button('📖 Key Guide'): show_scopus_dialog()
    with c2:
        if supabase and st.session_state['user']:
            if st.button('💾 Save to Profile'):
                try:
                    supabase.table('user_profiles').upsert({'user_id': st.session_state['user'].id, 'scopus_api_key': st.session_state['scopus_key']}).execute()
                    st.success('Saved!')
                except Exception as e: st.error(str(e))

st.markdown('### 🎓 OmniScholar Search')
tab1, tab2, tab3 = st.tabs([' Search', ' History', ' Bookmarks'])

with tab1:
    dbs = []
    c = st.columns(4)
    with c[0]:
        if st.checkbox('OpenAlex', value=True): dbs.append('openalex')
    with c[1]:
        if st.checkbox('arXiv', value=True): dbs.append('arxiv')
    with c[2]:
        if st.checkbox('DOAJ', value=True): dbs.append('doaj')
    with c[3]:
        sc = st.checkbox('Scopus OA', value=bool(st.session_state['scopus_key']))
        if sc:
            if not st.session_state['scopus_key']:
                st.warning('Key required')
                if st.button('🔑 Guide'): show_scopus_dialog()
            else: dbs.append('scopus')
    st.divider()
    q_input = st.text_input('Enter keywords or DOI')
    if st.button('🚀 Search', type='primary'):
        st.info('Executing federated search...')

with tab2:
    if supabase and st.session_state['user']:
        res = supabase.table('search_history').select('*').eq('user_id', st.session_state['user'].id).execute()
        st.write(res.data)

with tab3:
    if supabase and st.session_state['user']:
        res = supabase.table('bookmarks').select('*').eq('user_id', st.session_state['user'].id).execute()
        st.write(res.data)
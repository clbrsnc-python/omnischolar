# OmniScholar - Universal Scholarly Search Engine

OmniScholar is a 100% legal open-access literature search engine and citation generator built with Python, Streamlit, Supabase, and GitHub.

---

## Key Features

1. **User Authentication**:
   - Built-in Sign In / Sign Up / Sign Out powered by Supabase Auth (`supabase-py`).
2. **Scopus Key Management & Guide Popup**:
   - Logged-in users can enter their personal Elsevier Scopus API key.
   - Click **📖 Key Guide** or opt into Scopus to trigger a modal popup with step-by-step instructions.
   - Save the key directly to your private Supabase profile behind Row-Level Security (RLS).
3. **Federated Multi-Database Search**:
   - Queries OpenAlex, arXiv, DOAJ, and Scopus OA simultaneously.
4. **Advanced Query Builder**:
   - Multi-row Boolean logic (`AND`, `OR`, `NOT`) and field scoping (`All Fields`, `Title`, `Author`, `Abstract`, `DOI/ISSN`).
5. **Saved Search History & Bookmarks**:
   - Persisted in Supabase PostgreSQL tables linked to the user ID.
6. **Citation Generator**:
   - Generates and exports citations in APA 7th, MLA 9th, Chicago 17th, IEEE, Harvard, and BibTeX.

---

## Step-by-Step Implementation Guide

### Step 1: Set Up Supabase Database & Auth
1. Log in to your Supabase Dashboard and create a new project.
2. Open the **SQL Editor** in Supabase.
3. Paste and run the entire contents of `schema.sql`.
4. Copy your **Project URL** and **`anon` Public API Key** from **Project Settings -> API**.

### Step 2: Local Testing
1. Clone or download this project repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.streamlit/secrets.toml` file:
   ```toml
   SUPABASE_URL = "your-supabase-project-url"
   SUPABASE_KEY = "your-supabase-anon-key"
   ```
4. Launch the application:
   ```bash
   streamlit run app.py
   ```

### Step 3: Publish to GitHub
1. Initialize a git repository and push your project to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial OmniScholar commit"
   git branch -M main
   git remote add origin git@github.com:YOUR_USERNAME/omnischolar.git
   git push -u origin main
   ```

### Step 4: Deploy to Streamlit Community Cloud
1. Log in to Streamlit Community Cloud.
2. Click **New app**, select your GitHub repository, branch (`main`), and set Main file path to `app.py`.
3. Under **Advanced settings -> Secrets**, paste your Supabase configuration:
   ```toml
   SUPABASE_URL = "your-supabase-project-url"
   SUPABASE_KEY = "your-supabase-anon-key"
   ```
4. Click **Deploy!** Your app is now live online!

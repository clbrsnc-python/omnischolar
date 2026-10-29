-- =========================================================
-- OMNISCHOLAR SUPABASE DATABASE SCHEMA
-- Execute this script in your Supabase SQL Editor
-- =========================================================

-- 1. SEARCH HISTORY TABLE
CREATE TABLE IF NOT EXISTS public.search_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    selected_databases TEXT[] DEFAULT '{}',
    results_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE public.search_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can insert their own search history"
    ON public.search_history FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own search history"
    ON public.search_history FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own search history"
    ON public.search_history FOR DELETE USING (auth.uid() = user_id);

-- 2. BOOKMARKS / SAVED CITATIONS TABLE
CREATE TABLE IF NOT EXISTS public.bookmarks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    article_id TEXT NOT NULL,
    title TEXT NOT NULL,
    authors TEXT,
    publication_year TEXT,
    journal TEXT,
    doi TEXT,
    pdf_url TEXT,
    abstract TEXT,
    source TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, article_id)
);

ALTER TABLE public.bookmarks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can insert their own bookmarks"
    ON public.bookmarks FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own bookmarks"
    ON public.bookmarks FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own bookmarks"
    ON public.bookmarks FOR DELETE USING (auth.uid() = user_id);

-- 3. USER PROFILES TABLE (Stores user settings & Scopus API Key securely)
CREATE TABLE IF NOT EXISTS public.user_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    scopus_api_key TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile"
    ON public.user_profiles FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert/update their own profile"
    ON public.user_profiles FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own profile"
    ON public.user_profiles FOR UPDATE USING (auth.uid() = user_id);

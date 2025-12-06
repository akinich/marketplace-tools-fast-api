/**
 * ================================================================================
 * Supabase Client Configuration
 * ================================================================================
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Initializes Supabase client for frontend file uploads and storage access.
 * Used primarily for wastage tracking photo uploads.
 * ================================================================================
 */

import { createClient } from '@supabase/supabase-js';

// Get Supabase credentials from environment variables
const supabaseUrl = (import.meta as any).env.VITE_SUPABASE_URL as string;
const supabaseAnonKey = (import.meta as any).env.VITE_SUPABASE_ANON_KEY as string;

// Validate environment variables
if (!supabaseUrl || !supabaseAnonKey) {
    console.error('Missing Supabase environment variables. Please configure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env file.');
}

// Create Supabase client
export const supabase = createClient(supabaseUrl || '', supabaseAnonKey || '', {
    auth: {
        persistSession: false, // We handle auth separately via our backend
    },
});

export default supabase;

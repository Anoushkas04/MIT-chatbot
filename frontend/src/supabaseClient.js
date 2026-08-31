import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || "https://rfqpauujignqkljimovk.supabase.co";
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJmcXBhdXVqaWducWtsamltb3ZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTExNzEsImV4cCI6MjEwMzcyNzE3MX0.tA-C-senQ7yOpq_Ue3BsxI7w4vqzdG3r7D4GQgwHhXg";

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});

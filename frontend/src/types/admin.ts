export interface AdminUser {
  id: string;
  email: string;
  display_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface AIConfig {
  key: string;
  value: Record<string, unknown>;
  description: string | null;
  min_value: number | null;
  max_value: number | null;
}

export interface Analytics {
  total_users: number;
  total_migrations: number;
  total_messages: number;
  total_tokens_in: number;
  total_tokens_out: number;
  recent_activity: Array<{
    user_id: string;
    action: string;
    model_used: string;
    tokens_in: number;
    tokens_out: number;
    created_at: string;
  }>;
}

export interface Preference {
  id: string;
  category: string;
  preference_key: string;
  preference_value: string;
  source: string;
  confidence: number;
  active: boolean;
  created_at: string;
  updated_at: string;
}

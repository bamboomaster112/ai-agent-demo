export interface UserProfile {
  id: string;
  email: string;
  display_name: string | null;
  role: "user" | "admin";
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: UserProfile;
}

import { apiFetch } from "./client";
import type { AuthResponse, UserProfile } from "../types/auth";

export async function signup(
  email: string,
  password: string,
  displayName?: string
): Promise<AuthResponse> {
  return apiFetch("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password, display_name: displayName }),
  });
}

export async function login(
  email: string,
  password: string
): Promise<AuthResponse> {
  return apiFetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe(): Promise<UserProfile> {
  return apiFetch("/api/auth/me");
}

export async function refreshToken(
  refreshTokenStr: string
): Promise<{ access_token: string; refresh_token: string }> {
  return apiFetch("/api/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshTokenStr }),
  });
}

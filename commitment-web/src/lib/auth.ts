/**
 * Authentication API functions and utilities.
 */

const API_BASE = "http://127.0.0.1:8000";

// ============================================================================
// Types
// ============================================================================

export interface SignupRequest {
    email: string;
    password: string;
    role: "client" | "freelancer";
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    expires_in: number;
}

export interface UserProfile {
    public_id: string;
    email: string;
    role: string;
    is_active: boolean;
    is_verified: boolean;
    created_at: string;
}

export interface SignupResponse {
    message: string;
    public_id: string;
    email: string;
    role: string;
}

export interface AuthError {
    detail: string;
}

// ============================================================================
// Token Management (in-memory only - never localStorage)
// ============================================================================

let accessToken: string | null = null;

export function getAccessToken(): string | null {
    return accessToken;
}

export function setAccessToken(token: string | null): void {
    accessToken = token;
}

export function clearAccessToken(): void {
    accessToken = null;
}

// ============================================================================
// Auth API Functions
// ============================================================================

export async function signup(data: SignupRequest): Promise<SignupResponse> {
    const res = await fetch(`${API_BASE}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        credentials: "include", // Include cookies
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Signup failed");
    }

    return res.json();
}

export async function login(data: LoginRequest): Promise<TokenResponse> {
    const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        credentials: "include", // Include cookies for refresh token
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Login failed");
    }

    const tokenResponse = await res.json();

    // Store access token in memory
    setAccessToken(tokenResponse.access_token);

    return tokenResponse;
}

export async function logout(): Promise<void> {
    const token = getAccessToken();

    if (token) {
        try {
            await fetch(`${API_BASE}/auth/logout`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
                credentials: "include",
            });
        } catch {
            // Ignore logout errors - clear token anyway
        }
    }

    clearAccessToken();
}

export async function refreshToken(): Promise<TokenResponse | null> {
    try {
        const res = await fetch(`${API_BASE}/auth/refresh`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include", // Send refresh token cookie
        });

        if (!res.ok) {
            clearAccessToken();
            return null;
        }

        const tokenResponse = await res.json();
        setAccessToken(tokenResponse.access_token);
        return tokenResponse;
    } catch {
        clearAccessToken();
        return null;
    }
}

export async function getCurrentUser(): Promise<UserProfile | null> {
    const token = getAccessToken();

    if (!token) {
        return null;
    }

    try {
        const res = await fetch(`${API_BASE}/auth/me`, {
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json",
            },
            credentials: "include",
        });

        if (!res.ok) {
            if (res.status === 401) {
                // Token expired, try to refresh
                const refreshed = await refreshToken();
                if (refreshed) {
                    return getCurrentUser(); // Retry with new token
                }
            }
            return null;
        }

        return res.json();
    } catch {
        return null;
    }
}

// ============================================================================
// Authenticated API Helper
// ============================================================================

export async function authFetch<T>(
    path: string,
    options: RequestInit = {}
): Promise<T> {
    const token = getAccessToken();

    const res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...options.headers,
        },
        credentials: "include",
    });

    if (res.status === 401) {
        // Try to refresh token
        const refreshed = await refreshToken();
        if (refreshed) {
            // Retry the request with new token
            return authFetch<T>(path, options);
        }
        throw new Error("Session expired. Please log in again.");
    }

    if (!res.ok) {
        const text = await res.text();
        let message = "API error";
        try {
            const err = JSON.parse(text);
            message = err.detail || err.message || message;
        } catch {
            message = text || `API error (${res.status})`;
        }
        throw new Error(message);
    }

    const text = await res.text();
    return text ? JSON.parse(text) : ({} as T);
}

// ============================================================================
// Password Validation (client-side)
// ============================================================================

export interface PasswordValidation {
    isValid: boolean;
    errors: string[];
}

export function validatePassword(password: string): PasswordValidation {
    const errors: string[] = [];

    if (password.length < 8) {
        errors.push("Password must be at least 8 characters");
    }
    if (!/[A-Z]/.test(password)) {
        errors.push("Password must contain at least one uppercase letter");
    }
    if (!/[a-z]/.test(password)) {
        errors.push("Password must contain at least one lowercase letter");
    }
    if (!/\d/.test(password)) {
        errors.push("Password must contain at least one digit");
    }

    return {
        isValid: errors.length === 0,
        errors,
    };
}

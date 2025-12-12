import { API_URL } from "./utils";
import { getToken } from "./auth";

/* ============================================================
   Базовый запрос к API
============================================================ */

export async function apiRequest<T>(
  method: string,
  url: string,
  body?: any,
  customHeaders?: Record<string, string>
): Promise<T> {
  const token = getToken();

  const isForm = body instanceof URLSearchParams;

  const headers: Record<string, string> = {
    ...(isForm ? {} : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(customHeaders || {}),
  };

  const response = await fetch(API_URL + url, {
    method,
    headers,
    body: isForm ? body : body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let errorText = "Unknown error";

    try {
      const errorJson = await response.json();
      errorText = errorJson.detail || errorJson.error || JSON.stringify(errorJson);
    } catch {}

    throw new Error(`API Error ${response.status}: ${errorText}`);
  }

  if (response.status === 204) return {} as T;

  return await response.json();
}

/* ============================================================
   API Методы
============================================================ */

export const api = {
  /* ---------- AUTH ---------- */

  login: (email: string, password: string) =>
    apiRequest<{ access_token: string }>(
      "POST",
      "/auth/login",
      new URLSearchParams({
        username: email,
        password: password,
        grant_type: "",
        scope: "",
      }),
      {
        "Content-Type": "application/x-www-form-urlencoded",
      }
    ),

  me: () => apiRequest("GET", "/auth/me"),

  /* ---------- TICKETS ---------- */

  getTickets: () => apiRequest<any[]>("GET", "/tickets"),

  getTicket: (id: number) => apiRequest("GET", `/tickets/${id}`),

  sendMessage: (ticketId: number, text: string) =>
    apiRequest("POST", `/tickets/${ticketId}/messages`, {
      content: text,
    }),

  closeTicket: (ticketId: number) =>
    apiRequest("POST", `/tickets/${ticketId}/close`),
};

/* ============================================================
    Token helpers
============================================================ */

const TOKEN_KEY = "jwt_token";

// Сохранить токен
export const setToken = (token: string): void => {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
};

// Получить токен
export const getToken = (): string | null => {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
};

// Удалить токен
export const removeToken = (): void => {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
};

// Полный выход из системы
export const logout = (): void => {
  removeToken();
  // Можно добавить очистку доп. данных если появятся
  // localStorage.clear(); <-- если понадобится, скажи
  window.location.href = "/login";
};

/* ============================================================
    Auto logout helper (используем при 401)
============================================================ */

export const handleAuthError = (status: number) => {
  if (status === 401) {
    logout();
  }
};

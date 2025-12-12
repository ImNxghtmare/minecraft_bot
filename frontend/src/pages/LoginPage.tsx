import { useState } from "react";
import { api } from "@/lib/api";
import { setToken } from "@/lib/auth";
import { useNavigate } from "react-router-dom";

import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2 } from "lucide-react";
import "./login.css"; // локальные стили

export default function LoginPage() {
  const nav = useNavigate();
  const [email, setEmail] = useState("admin@minecraft.support");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await api.login(email, password);
      setToken(res.access_token);
      nav("/dashboard");
    } catch (e: any) {
      setError(e.message || "Ошибка авторизации");
    }

    setLoading(false);
  }

  return (
    <div className="login-bg min-h-screen flex items-center justify-center p-6">

      <Card className="w-full max-w-md bg-[hsl(var(--card))] border-none shadow-xl backdrop-blur-xl">
        <CardHeader className="text-center space-y-1 pb-2">
          <CardTitle className="text-3xl font-bold">CubeWorld Support</CardTitle>
          <p className="text-sm text-gray-400">Вход в панель оператора</p>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            {error && (
              <div className="text-red-400 text-sm bg-red-400/10 px-3 py-2 rounded-lg border border-red-400/30">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-medium">Email</label>
              <Input
                type="email"
                placeholder="example@mail.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Пароль</label>
              <Input
                type="password"
                placeholder="Введите пароль"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Войти"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

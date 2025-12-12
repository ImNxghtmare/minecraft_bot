import { Outlet, Link, useNavigate } from "react-router-dom";
import { logout } from "@/lib/auth";

export default function PageWrapper() {
  const navigate = useNavigate();

  function logout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-white p-4 flex flex-col">
        <h2 className="text-xl font-bold mb-6">Support Panel</h2>

        <nav className="flex flex-col gap-2">
          <Link className="hover:bg-gray-700 p-2 rounded" to="/dashboard">
            📊 Dashboard
          </Link>
          <Link className="hover:bg-gray-700 p-2 rounded" to="/tickets">
            🎫 Tickets
          </Link>
        </nav>

        <button
          onClick={logout}
          className="mt-auto bg-red-600 p-2 rounded hover:bg-red-700"
        >
          Выйти
        </button>
      </aside>

      {/* Content */}
      <main className="flex-1 bg-gray-100 p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}

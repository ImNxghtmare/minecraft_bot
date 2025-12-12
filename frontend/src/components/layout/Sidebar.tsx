import { NavLink } from "react-router-dom";
import { Home, Ticket, MessageSquare, Settings } from "lucide-react";

const links = [
  { to: "/", label: "Dashboard", icon: Home },
  { to: "/tickets", label: "Tickets", icon: Ticket },
  { to: "/messages", label: "Messages", icon: MessageSquare },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-[#1A1A1D] border-r border-[#2A2A2D] p-4 flex flex-col">
      <h1 className="text-xl font-bold mb-6">Support Panel</h1>

      <nav className="flex flex-col gap-2">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg transition ${
                isActive
                  ? "bg-[#3A3A3D] text-white"
                  : "text-gray-400 hover:bg-[#2A2A2D]"
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

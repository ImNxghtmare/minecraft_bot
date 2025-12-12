export default function Header() {
  return (
    <header className="h-14 border-b border-[#2A2A2D] flex items-center justify-between px-6">
      <h2 className="text-lg font-semibold">Operator Panel</h2>

      <div className="text-gray-400">
        Logged in as <span className="text-white font-medium">Operator</span>
      </div>
    </header>
  );
}
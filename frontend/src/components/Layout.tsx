import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-institucional-100 bg-white px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-md bg-institucional-900" aria-hidden />
          <div>
            <p className="font-display text-sm font-semibold leading-tight text-institucional-950">
              Asistente Virtual
            </p>
            <p className="text-xs leading-tight text-institucional-700">Secretaría de Educación</p>
          </div>
        </div>

        <nav className="flex items-center gap-4 text-sm">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              isActive ? "font-medium text-institucional-950" : "text-institucional-700 hover:text-institucional-950"
            }
          >
            Consultar
          </NavLink>
          {user?.role === "admin" && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                isActive ? "font-medium text-institucional-950" : "text-institucional-700 hover:text-institucional-950"
              }
            >
              Administración
            </NavLink>
          )}
          <span className="text-institucional-300">|</span>
          <span className="text-institucional-700">{user?.email}</span>
          <button onClick={handleLogout} className="text-institucional-700 underline hover:text-institucional-950">
            Salir
          </button>
        </nav>
      </header>

      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}

import { Link, Route, Routes } from "react-router-dom";
import Admin from "./pages/Admin";
import Home from "./pages/Home";

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="flex gap-6 border-b bg-white px-6 py-3 text-sm">
        <Link to="/" className="font-medium text-institutional">
          Asistente
        </Link>
        <Link to="/admin" className="text-slate-600 hover:text-institutional">
          Panel administrativo
        </Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/admin" element={<Admin />} />
      </Routes>
    </div>
  );
}

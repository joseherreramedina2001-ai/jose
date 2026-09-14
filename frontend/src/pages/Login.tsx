import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No fue posible iniciar sesión");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen grid place-items-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 h-12 w-12 rounded-md bg-institucional-900" aria-hidden />
          <h1 className="font-display text-2xl font-semibold text-institucional-950">
            Asistente Virtual
          </h1>
          <p className="mt-1 text-sm text-institucional-700">Secretaría de Educación</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-institucional-100 bg-white p-6 shadow-sm">
          <div>
            <label htmlFor="email" className="mb-1 block text-sm text-institucional-800">Correo institucional</label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-institucional-100 px-3 py-2 text-sm focus:border-institucional-700 focus:outline-none focus:ring-1 focus:ring-institucional-700"
              placeholder="nombre@secretariaeducacion.gov.co"
            />
          </div>
          <div>
            <label htmlFor="password" className="mb-1 block text-sm text-institucional-800">Contraseña</label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-institucional-100 px-3 py-2 text-sm focus:border-institucional-700 focus:outline-none focus:ring-1 focus:ring-institucional-700"
            />
          </div>

          {error && <p className="text-sm text-red-700">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-institucional-900 py-2 text-sm font-medium text-white transition hover:bg-institucional-800 disabled:opacity-60"
          >
            {loading ? "Ingresando…" : "Ingresar"}
          </button>
        </form>
      </div>
    </div>
  );
}

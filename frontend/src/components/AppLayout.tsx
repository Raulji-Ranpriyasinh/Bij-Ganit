import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { api } from "../api/client";
import { useAuthStore } from "../stores/authStore";
import { useCompanyStore, type Company } from "../stores/companyStore";

const NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/customers", label: "Customers" },
  { to: "/items", label: "Items" },
  { to: "/invoices", label: "Invoices" },
  { to: "/estimates", label: "Estimates" },
  { to: "/expenses", label: "Expenses" },
  { to: "/payments", label: "Payments" },
  { to: "/recurring-invoices", label: "Recurring Invoices" },
  { to: "/settings", label: "Settings" },
];

export function AppLayout() {
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);
  const { companies, activeCompanyId, setCompanies, setActiveCompany } = useCompanyStore();

  useEffect(() => {
    let cancelled = false;
    api
      .get<Company[]>("/v1/companies")
      .then((res) => {
        if (!cancelled) setCompanies(res.data);
      })
      .catch(() => {
        /* ignored — sidebar still renders */
      });
    return () => {
      cancelled = true;
    };
  }, [setCompanies]);

  function handleLogout() {
    api.post("/v1/auth/logout").catch(() => undefined);
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="flex h-screen bg-slate-100 text-slate-900">
      <aside className="w-60 bg-slate-900 text-slate-100 flex flex-col">
        <div className="px-5 py-4 text-lg font-semibold border-b border-slate-700">
          Bij-Ganit
        </div>
        <nav className="flex-1 overflow-y-auto py-2">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `block px-5 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-slate-800 text-white"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <label htmlFor="company-switcher" className="text-sm text-slate-500">
              Company:
            </label>
            <select
              id="company-switcher"
              className="border border-slate-300 rounded px-2 py-1 text-sm"
              value={activeCompanyId ?? ""}
              onChange={(e) => setActiveCompany(Number(e.target.value))}
            >
              {companies.length === 0 && <option value="">(no companies)</option>}
              {companies.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleLogout}
            className="text-sm text-slate-600 hover:text-slate-900"
          >
            Logout
          </button>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

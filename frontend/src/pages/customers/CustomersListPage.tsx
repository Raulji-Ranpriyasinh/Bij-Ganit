import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import type { Customer } from "../../types/masterData";

const PAGE_SIZE = 10;

export function CustomersListPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<Customer[]>("/v1/customers", {
        params: search ? { search } : undefined,
      });
      setCustomers(data);
      setPage(1);
    } catch {
      setError("Failed to load customers.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const paged = useMemo(
    () => customers.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [customers, page]
  );
  const pageCount = Math.max(1, Math.ceil(customers.length / PAGE_SIZE));

  async function handleDelete(id: number) {
    if (!confirm("Delete this customer?")) return;
    try {
      await api.post("/v1/customers/delete", { ids: [id] });
      await load();
    } catch {
      setError("Delete failed.");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Customers</h1>
        <Link
          to="/customers/new"
          className="bg-slate-900 hover:bg-slate-800 text-white text-sm font-medium rounded px-3 py-2"
        >
          + New Customer
        </Link>
      </div>
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          load();
        }}
      >
        <input
          type="search"
          placeholder="Search name, contact, company…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-slate-300 rounded px-3 py-2 text-sm flex-1 max-w-md"
        />
        <button
          type="submit"
          className="bg-slate-700 text-white text-sm rounded px-3 py-2"
        >
          Search
        </button>
      </form>

      {error && <div className="text-sm text-red-600">{error}</div>}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-slate-600 text-left">
            <tr>
              <th className="px-4 py-2 font-medium">Name</th>
              <th className="px-4 py-2 font-medium">Company</th>
              <th className="px-4 py-2 font-medium">Email</th>
              <th className="px-4 py-2 font-medium">Phone</th>
              <th className="px-4 py-2 font-medium w-32"></th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td className="px-4 py-6 text-center text-slate-500" colSpan={5}>
                  Loading…
                </td>
              </tr>
            )}
            {!loading && paged.length === 0 && (
              <tr>
                <td className="px-4 py-6 text-center text-slate-500" colSpan={5}>
                  No customers yet.
                </td>
              </tr>
            )}
            {paged.map((c) => (
              <tr key={c.id} className="border-t border-slate-100">
                <td className="px-4 py-2">
                  <Link to={`/customers/${c.id}`} className="text-slate-900 hover:underline">
                    {c.name}
                  </Link>
                </td>
                <td className="px-4 py-2 text-slate-600">{c.company_name ?? "—"}</td>
                <td className="px-4 py-2 text-slate-600">{c.email ?? "—"}</td>
                <td className="px-4 py-2 text-slate-600">{c.phone ?? "—"}</td>
                <td className="px-4 py-2 text-right">
                  <button
                    onClick={() => handleDelete(c.id)}
                    className="text-red-600 hover:underline text-xs"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-sm text-slate-600">
        <span>
          {customers.length} customer{customers.length === 1 ? "" : "s"} total
        </span>
        <div className="flex items-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="px-2 py-1 border rounded disabled:opacity-40"
          >
            Prev
          </button>
          <span>
            Page {page} of {pageCount}
          </span>
          <button
            disabled={page >= pageCount}
            onClick={() => setPage((p) => p + 1)}
            className="px-2 py-1 border rounded disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

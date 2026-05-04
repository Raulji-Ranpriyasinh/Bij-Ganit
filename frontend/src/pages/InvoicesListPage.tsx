import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from '../api/client'

interface Invoice {
  id: number;
  invoice_number: string | null;
  invoice_date: string | null;
  due_date: string | null;
  status: string;
  paid_status: string;
  total: number;
  due_amount: number;
  customer?: { name: string } | null;
}

const STATUS_COLORS: Record<string, string> = {
  DRAFT: "bg-slate-100 text-slate-700",
  SENT: "bg-blue-100 text-blue-700",
  VIEWED: "bg-purple-100 text-purple-700",
  COMPLETED: "bg-green-100 text-green-700",
};

const PAID_COLORS: Record<string, string> = {
  UNPAID: "bg-red-100 text-red-700",
  PARTIALLY_PAID: "bg-amber-100 text-amber-700",
  PAID: "bg-green-100 text-green-700",
};

const PAGE_SIZE = 10;

export default function InvoicesListPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [paidFilter, setPaidFilter] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      if (paidFilter) params.paid_status = paidFilter;
      const { data } = await api.get<{ items: Invoice[] }>("/v1/invoices", { params });
      setInvoices(data.items ?? []);
      setPage(1);
    } catch {
      setError("Failed to load invoices.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const paged = useMemo(
    () => invoices.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [invoices, page]
  );
  const pageCount = Math.max(1, Math.ceil(invoices.length / PAGE_SIZE));

  async function handleDelete(id: number) {
    if (!confirm("Delete this invoice?")) return;
    try {
      await api.post("/v1/invoices/delete", [id]);
      await load();
    } catch {
      setError("Delete failed.");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Invoices</h1>
        <Link to="/invoices/new"
          className="bg-slate-900 hover:bg-slate-800 text-white text-sm font-medium rounded px-3 py-2">
          + New Invoice
        </Link>
      </div>

      <form className="flex flex-wrap gap-2" onSubmit={(e) => { e.preventDefault(); load(); }}>
        <input type="search" placeholder="Search customer…" value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-slate-300 rounded px-3 py-2 text-sm flex-1 min-w-40 max-w-xs" />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-slate-300 rounded px-3 py-2 text-sm">
          <option value="">All statuses</option>
          {["DRAFT", "SENT", "VIEWED", "COMPLETED"].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select value={paidFilter} onChange={(e) => setPaidFilter(e.target.value)}
          className="border border-slate-300 rounded px-3 py-2 text-sm">
          <option value="">All paid statuses</option>
          {["UNPAID", "PARTIALLY_PAID", "PAID"].map((s) => (
            <option key={s} value={s}>{s.replace("_", " ")}</option>
          ))}
        </select>
        <button type="submit" className="bg-slate-700 text-white text-sm rounded px-3 py-2">
          Filter
        </button>
      </form>

      {error && <div className="text-sm text-red-600">{error}</div>}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-slate-600 text-left">
            <tr>
              <th className="px-4 py-2 font-medium">Number</th>
              <th className="px-4 py-2 font-medium">Customer</th>
              <th className="px-4 py-2 font-medium">Date</th>
              <th className="px-4 py-2 font-medium">Status</th>
              <th className="px-4 py-2 font-medium">Paid</th>
              <th className="px-4 py-2 font-medium text-right">Total</th>
              <th className="px-4 py-2 font-medium text-right">Due</th>
              <th className="px-4 py-2 font-medium w-24"></th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={8} className="px-4 py-6 text-center text-slate-500">Loading…</td></tr>
            )}
            {!loading && paged.length === 0 && (
              <tr><td colSpan={8} className="px-4 py-6 text-center text-slate-500">No invoices yet.</td></tr>
            )}
            {paged.map((inv) => (
              <tr key={inv.id} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-4 py-2">
                  <Link to={`/invoices/${inv.id}`} className="text-slate-900 hover:underline font-mono">
                    {inv.invoice_number ?? `#${inv.id}`}
                  </Link>
                </td>
                <td className="px-4 py-2 text-slate-700">{inv.customer?.name ?? "—"}</td>
                <td className="px-4 py-2 text-slate-600">{inv.invoice_date ?? "—"}</td>
                <td className="px-4 py-2">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_COLORS[inv.status] ?? "bg-slate-100 text-slate-700"}`}>
                    {inv.status}
                  </span>
                </td>
                <td className="px-4 py-2">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${PAID_COLORS[inv.paid_status] ?? "bg-slate-100 text-slate-700"}`}>
                    {inv.paid_status.replace("_", " ")}
                  </span>
                </td>
                <td className="px-4 py-2 text-right font-mono">{(inv.total / 100).toFixed(2)}</td>
                <td className="px-4 py-2 text-right font-mono">{(inv.due_amount / 100).toFixed(2)}</td>
                <td className="px-4 py-2 text-right">
                  <button onClick={() => handleDelete(inv.id)}
                    className="text-red-600 hover:underline text-xs">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-sm text-slate-600">
        <span>{invoices.length} invoice{invoices.length === 1 ? "" : "s"} total</span>
        <div className="flex items-center gap-2">
          <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}
            className="px-2 py-1 border rounded disabled:opacity-40">Prev</button>
          <span>Page {page} of {pageCount}</span>
          <button disabled={page >= pageCount} onClick={() => setPage((p) => p + 1)}
            className="px-2 py-1 border rounded disabled:opacity-40">Next</button>
        </div>
      </div>
    </div>
  );
}
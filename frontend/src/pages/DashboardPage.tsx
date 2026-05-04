import { useEffect, useState } from "react";
import { api } from "../api/client";

interface DashboardData {
  chart: {
    months: string[];
    invoice_totals: number[];
    expense_totals: number[];
    receipt_totals: number[];
    net_income: number[];
  };
  summary: {
    total_sales: number;
    total_receipts: number;
    total_expenses: number;
    total_net_income: number;
    total_customer_count: number;
    total_invoice_count: number;
    total_estimate_count: number;
    total_amount_due: number;
  };
  recent_due_invoices: Array<{
    id: number;
    invoice_number: string | null;
    due_amount: number;
    due_date: string | null;
  }>;
}

function fmt(cents: number) {
  return (cents / 100).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function SummaryCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className={`rounded-lg shadow p-5 text-white ${color}`}>
      <p className="text-sm opacity-80">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}

function SimpleBarChart({ months, datasets }: {
  months: string[];
  datasets: Array<{ label: string; values: number[]; color: string }>;
}) {
  const max = Math.max(1, ...datasets.flatMap((d) => d.values));
  return (
    <div className="space-y-2">
      <div className="flex items-end gap-1 h-40">
        {months.map((m, mi) => (
          <div key={m} className="flex-1 flex flex-col items-center gap-0.5 justify-end h-full">
            {datasets.map((d) => (
              <div key={d.label} title={`${d.label}: ${fmt(d.values[mi])}`}
                style={{ height: `${Math.max(2, (d.values[mi] / max) * 100)}%`, background: d.color }}
                className="w-full rounded-t" />
            ))}
          </div>
        ))}
      </div>
      <div className="flex gap-1 overflow-hidden">
        {months.map((m) => (
          <div key={m} className="flex-1 text-center text-xs text-slate-500 truncate">{m.slice(5)}</div>
        ))}
      </div>
      <div className="flex gap-4">
        {datasets.map((d) => (
          <div key={d.label} className="flex items-center gap-1 text-xs text-slate-600">
            <span className="w-3 h-3 rounded-sm inline-block" style={{ background: d.color }} />
            {d.label}
          </div>
        ))}
      </div>
    </div>
  );
}

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [prevYear, setPrevYear] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api.get<DashboardData>("/v1/dashboard", { params: { previous_year: prevYear } })
      .then(({ data }) => setData(data))
      .catch(() => setError("Failed to load dashboard."))
      .finally(() => setLoading(false));
  }, [prevYear]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="flex items-center gap-2 text-sm">
          <button onClick={() => setPrevYear(false)}
            className={`px-3 py-1 rounded ${!prevYear ? "bg-slate-900 text-white" : "border border-slate-300 text-slate-700"}`}>
            This year
          </button>
          <button onClick={() => setPrevYear(true)}
            className={`px-3 py-1 rounded ${prevYear ? "bg-slate-900 text-white" : "border border-slate-300 text-slate-700"}`}>
            Last year
          </button>
        </div>
      </div>

      {error && <div className="text-sm text-red-600">{error}</div>}
      {loading && <p className="text-sm text-slate-500">Loading…</p>}

      {data && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <SummaryCard label="Total Sales" value={fmt(data.summary.total_sales)} color="bg-blue-600" />
            <SummaryCard label="Total Receipts" value={fmt(data.summary.total_receipts)} color="bg-green-600" />
            <SummaryCard label="Total Expenses" value={fmt(data.summary.total_expenses)} color="bg-red-500" />
            <SummaryCard label="Net Income" value={fmt(data.summary.total_net_income)} color="bg-purple-600" />
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-center">
            {[
              { label: "Customers", val: data.summary.total_customer_count },
              { label: "Invoices", val: data.summary.total_invoice_count },
              { label: "Estimates", val: data.summary.total_estimate_count },
              { label: "Amount Due", val: `$${fmt(data.summary.total_amount_due)}` },
            ].map((s) => (
              <div key={s.label} className="bg-white rounded-lg shadow p-4">
                <p className="text-xs text-slate-500">{s.label}</p>
                <p className="text-xl font-bold text-slate-900 mt-1">{s.val}</p>
              </div>
            ))}
          </div>

          <div className="bg-white rounded-lg shadow p-5">
            <h2 className="text-sm font-semibold text-slate-700 mb-4">Monthly Overview</h2>
            <SimpleBarChart
              months={data.chart.months}
              datasets={[
                { label: "Sales", values: data.chart.invoice_totals, color: "#3b82f6" },
                { label: "Receipts", values: data.chart.receipt_totals, color: "#22c55e" },
                { label: "Expenses", values: data.chart.expense_totals, color: "#ef4444" },
              ]}
            />
          </div>

          {data.recent_due_invoices.length > 0 && (
            <div className="bg-white rounded-lg shadow p-5">
              <h2 className="text-sm font-semibold text-slate-700 mb-3">Recent Due Invoices</h2>
              <table className="w-full text-sm">
                <thead className="text-left text-slate-500 text-xs">
                  <tr>
                    <th className="pb-2 font-medium">Invoice</th>
                    <th className="pb-2 font-medium">Due Date</th>
                    <th className="pb-2 font-medium text-right">Amount Due</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_due_invoices.map((inv) => (
                    <tr key={inv.id} className="border-t border-slate-100">
                      <td className="py-2 font-mono">{inv.invoice_number ?? `#${inv.id}`}</td>
                      <td className="py-2 text-slate-600">{inv.due_date ?? "—"}</td>
                      <td className="py-2 text-right font-mono text-red-600">{fmt(inv.due_amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
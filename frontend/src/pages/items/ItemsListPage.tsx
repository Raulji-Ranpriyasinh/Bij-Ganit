import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import type { Currency, Item, Unit } from "../../types/masterData";

const PAGE_SIZE = 10;

function formatPrice(price: number, currency?: Currency) {
  if (!currency) return (price / 100).toFixed(2);
  const value = price / Math.pow(10, currency.precision);
  const parts = value.toFixed(currency.precision).split(".");
  const whole = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, currency.thousand_separator);
  const decimal = parts[1] ? currency.decimal_separator + parts[1] : "";
  const amount = whole + decimal;
  return currency.swap_currency_symbol
    ? `${amount} ${currency.symbol ?? currency.code}`
    : `${currency.symbol ?? currency.code} ${amount}`;
}

export function ItemsListPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [i, u, c] = await Promise.all([
        api.get<Item[]>("/v1/items", { params: search ? { search } : undefined }),
        api.get<Unit[]>("/v1/units"),
        api.get<Currency[]>("/v1/currencies"),
      ]);
      setItems(i.data);
      setUnits(u.data);
      setCurrencies(c.data);
      setPage(1);
    } catch {
      setError("Failed to load items.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const unitName = (id: number | null) =>
    units.find((u) => u.id === id)?.name ?? "—";
  const currency = (id: number | null) => currencies.find((c) => c.id === id);

  const paged = useMemo(
    () => items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [items, page]
  );
  const pageCount = Math.max(1, Math.ceil(items.length / PAGE_SIZE));

  async function handleDelete(id: number) {
    if (!confirm("Delete this item?")) return;
    try {
      await api.post("/v1/items/delete", { ids: [id] });
      await load();
    } catch {
      setError("Delete failed.");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Items</h1>
        <Link
          to="/items/new"
          className="bg-slate-900 hover:bg-slate-800 text-white text-sm font-medium rounded px-3 py-2"
        >
          + New Item
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
          placeholder="Search name or description…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-slate-300 rounded px-3 py-2 text-sm flex-1 max-w-md"
        />
        <button type="submit" className="bg-slate-700 text-white text-sm rounded px-3 py-2">
          Search
        </button>
      </form>

      {error && <div className="text-sm text-red-600">{error}</div>}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-slate-600 text-left">
            <tr>
              <th className="px-4 py-2 font-medium">Name</th>
              <th className="px-4 py-2 font-medium">Unit</th>
              <th className="px-4 py-2 font-medium">Price</th>
              <th className="px-4 py-2 font-medium">Taxes</th>
              <th className="px-4 py-2 font-medium w-32"></th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-500">
                  Loading…
                </td>
              </tr>
            )}
            {!loading && paged.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-500">
                  No items yet.
                </td>
              </tr>
            )}
            {paged.map((item) => (
              <tr key={item.id} className="border-t border-slate-100">
                <td className="px-4 py-2">
                  <Link to={`/items/${item.id}`} className="text-slate-900 hover:underline">
                    {item.name}
                  </Link>
                </td>
                <td className="px-4 py-2 text-slate-600">{unitName(item.unit_id)}</td>
                <td className="px-4 py-2 text-slate-600">
                  {formatPrice(item.price, currency(item.currency_id))}
                </td>
                <td className="px-4 py-2 text-slate-600">
                  {item.taxes.length
                    ? item.taxes.map((t) => `${t.name} (${t.percent}%)`).join(", ")
                    : "—"}
                </td>
                <td className="px-4 py-2 text-right">
                  <button
                    onClick={() => handleDelete(item.id)}
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
          {items.length} item{items.length === 1 ? "" : "s"} total
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

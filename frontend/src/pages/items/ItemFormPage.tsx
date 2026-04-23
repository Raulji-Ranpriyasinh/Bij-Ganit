import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../../api/client";
import type {
  Currency,
  Item,
  ItemTax,
  TaxType,
  Unit,
} from "../../types/masterData";

interface FormState {
  name: string;
  description: string;
  price: string;
  tax_per_item: boolean;
  unit_id: string;
  currency_id: string;
  tax_type_ids: number[];
}

function initial(): FormState {
  return {
    name: "",
    description: "",
    price: "",
    tax_per_item: false,
    unit_id: "",
    currency_id: "",
    tax_type_ids: [],
  };
}

export function ItemFormPage() {
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id && id !== "new");
  const navigate = useNavigate();
  const [form, setForm] = useState<FormState>(initial);
  const [units, setUnits] = useState<Unit[]>([]);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [taxTypes, setTaxTypes] = useState<TaxType[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get<Unit[]>("/v1/units"),
      api.get<Currency[]>("/v1/currencies"),
      api.get<TaxType[]>("/v1/tax-types"),
    ])
      .then(([u, c, t]) => {
        setUnits(u.data);
        setCurrencies(c.data);
        setTaxTypes(t.data);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!isEdit || !id) return;
    api
      .get<Item>(`/v1/items/${id}`)
      .then(({ data }) => {
        setForm({
          name: data.name ?? "",
          description: data.description ?? "",
          price: String(data.price ?? 0),
          tax_per_item: data.tax_per_item,
          unit_id: data.unit_id ? String(data.unit_id) : "",
          currency_id: data.currency_id ? String(data.currency_id) : "",
          tax_type_ids: data.taxes.map((t) => t.tax_type_id),
        });
      })
      .catch(() => setError("Failed to load item"));
  }, [id, isEdit]);

  function toggleTax(taxTypeId: number) {
    setForm((f) => ({
      ...f,
      tax_type_ids: f.tax_type_ids.includes(taxTypeId)
        ? f.tax_type_ids.filter((t) => t !== taxTypeId)
        : [...f.tax_type_ids, taxTypeId],
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    const taxes: Omit<ItemTax, "id" | "name">[] = form.tax_type_ids
      .map((tid) => {
        const tt = taxTypes.find((t) => t.id === tid);
        if (!tt) return null;
        return {
          tax_type_id: tid,
          amount: 0,
          percent: tt.percent,
          compound_tax: tt.compound_tax,
        };
      })
      .filter((x): x is Omit<ItemTax, "id" | "name"> => Boolean(x));

    const body = {
      name: form.name,
      description: form.description || null,
      price: Number(form.price || 0),
      tax_per_item: form.tax_per_item,
      unit_id: form.unit_id ? Number(form.unit_id) : null,
      currency_id: form.currency_id ? Number(form.currency_id) : null,
      taxes,
    };
    try {
      if (isEdit) {
        await api.put(`/v1/items/${id}`, body);
      } else {
        await api.post("/v1/items", body);
      }
      navigate("/items");
    } catch {
      setError("Save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-3xl">
      <h1 className="text-2xl font-semibold">
        {isEdit ? "Edit Item" : "New Item"}
      </h1>
      <section className="bg-white rounded-lg shadow p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1 col-span-2">
            <label className="text-sm font-medium text-slate-700">Name *</label>
            <input
              required
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
            />
          </div>
          <div className="space-y-1 col-span-2">
            <label className="text-sm font-medium text-slate-700">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              rows={3}
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-700">
              Price (smallest currency unit, e.g. cents)
            </label>
            <input
              type="number"
              min={0}
              value={form.price}
              onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))}
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-700">Unit</label>
            <select
              value={form.unit_id}
              onChange={(e) => setForm((f) => ({ ...f, unit_id: e.target.value }))}
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
            >
              <option value="">— Select —</option>
              {units.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-700">Currency</label>
            <select
              value={form.currency_id}
              onChange={(e) => setForm((f) => ({ ...f, currency_id: e.target.value }))}
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
            >
              <option value="">— Use company default —</option>
              {currencies.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.code} — {c.name}
                </option>
              ))}
            </select>
          </div>
          <label className="flex items-center gap-2 text-sm mt-6">
            <input
              type="checkbox"
              checked={form.tax_per_item}
              onChange={(e) => setForm((f) => ({ ...f, tax_per_item: e.target.checked }))}
            />
            Apply tax per item
          </label>
        </div>
      </section>

      <section className="bg-white rounded-lg shadow p-5 space-y-3">
        <h2 className="text-sm font-semibold uppercase text-slate-500">Linked taxes</h2>
        {taxTypes.length === 0 ? (
          <p className="text-sm text-slate-500">
            No tax types defined for this company yet.
          </p>
        ) : (
          <ul className="space-y-2">
            {taxTypes.map((t) => (
              <li key={t.id}>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={form.tax_type_ids.includes(t.id)}
                    onChange={() => toggleTax(t.id)}
                  />
                  <span>
                    {t.name} ({t.percent}%)
                  </span>
                </label>
              </li>
            ))}
          </ul>
        )}
      </section>

      {error && <div className="text-sm text-red-600">{error}</div>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={saving}
          className="bg-slate-900 hover:bg-slate-800 text-white text-sm font-medium rounded px-4 py-2 disabled:opacity-60"
        >
          {saving ? "Saving…" : isEdit ? "Save changes" : "Create item"}
        </button>
        <button
          type="button"
          onClick={() => navigate("/items")}
          className="text-sm text-slate-600 hover:text-slate-900"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

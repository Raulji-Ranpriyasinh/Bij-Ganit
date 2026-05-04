import { useEffect, useState, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from '../api/client'
import type { Customer, Item, TaxType } from '../types/masterData'

interface TaxLine {
  tax_type_id: number;
  name: string;
  percent: string;
  amount: number;
  compound_tax: boolean;
}

interface LineItem {
  item_id: number | null;
  name: string;
  description: string;
  price: number;
  quantity: number;
  discount: number;
  discount_val: number;
  unit_name: string;
  taxes: TaxLine[];
  _lineTotal: number;
}

function blankLine(): LineItem {
  return {
    item_id: null,
    name: "",
    description: "",
    price: 0,
    quantity: 1,
    discount: 0,
    discount_val: 0,
    unit_name: "",
    taxes: [],
    _lineTotal: 0,
  };
}

function calcLineTotal(line: LineItem): number {
  return line.price * line.quantity - line.discount_val;
}

export default function InvoiceFormPage() {
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id && id !== "new");
  const navigate = useNavigate();

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [catalog, setCatalog] = useState<Item[]>([]);
  const [taxTypes, setTaxTypes] = useState<TaxType[]>([]);

  const [customerId, setCustomerId] = useState<string>("");
  const [invoiceDate, setInvoiceDate] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [lines, setLines] = useState<LineItem[]>([blankLine()]);
  const [invoiceDiscount, setInvoiceDiscount] = useState(0);
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Totals
  const subTotal = lines.reduce((s, l) => s + calcLineTotal(l), 0);
  const lineTaxTotal = lines.reduce((s, l) => {
    return s + l.taxes.reduce((ts, t) => ts + t.amount, 0);
  }, 0);
  const total = subTotal + lineTaxTotal - invoiceDiscount;

  useEffect(() => {
    Promise.all([
      api.get<Customer[]>("/v1/customers"),
      api.get<Item[]>("/v1/items"),
      api.get<TaxType[]>("/v1/tax-types"),
    ]).then(([c, i, t]) => {
      setCustomers(c.data);
      setCatalog(i.data);
      setTaxTypes(t.data);
    }).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!isEdit || !id) return;
    api.get<{
      customer_id: number | null;
      invoice_date: string | null;
      due_date: string | null;
      notes: string | null;
      discount: number;
      items: Array<{
        item_id: number | null;
        name: string;
        description: string | null;
        price: number;
        quantity: number;
        discount: number;
        discount_val: number;
        unit_name: string | null;
      }>;
    }>(`/v1/invoices/${id}`).then(({ data }) => {
      setCustomerId(data.customer_id ? String(data.customer_id) : "");
      setInvoiceDate(data.invoice_date ?? "");
      setDueDate(data.due_date ?? "");
      setNotes(data.notes ?? "");
      setInvoiceDiscount(data.discount ?? 0);
      if (data.items?.length) {
        setLines(data.items.map((it) => ({
          item_id: it.item_id,
          name: it.name,
          description: it.description ?? "",
          price: it.price,
          quantity: it.quantity,
          discount: it.discount,
          discount_val: it.discount_val,
          unit_name: it.unit_name ?? "",
          taxes: [],
          _lineTotal: it.price * it.quantity - it.discount_val,
        })));
      }
    }).catch(() => setError("Failed to load invoice"));
  }, [id, isEdit]);

  const updateLine = useCallback((idx: number, patch: Partial<LineItem>) => {
    setLines((prev) => prev.map((l, i) => {
      if (i !== idx) return l;
      const updated = { ...l, ...patch };
      updated._lineTotal = calcLineTotal(updated);
      return updated;
    }));
  }, []);

  function pickFromCatalog(idx: number, itemId: string) {
    const item = catalog.find((c) => c.id === Number(itemId));
    if (!item) return;
    const taxes: TaxLine[] = item.taxes.map((t) => ({
      tax_type_id: t.tax_type_id,
      name: t.name ?? "",
      percent: t.percent,
      amount: Math.round((item.price * Number(t.percent)) / 100),
      compound_tax: t.compound_tax,
    }));
    updateLine(idx, {
      item_id: item.id,
      name: item.name,
      description: item.description ?? "",
      price: item.price,
      quantity: 1,
      discount: 0,
      discount_val: 0,
      taxes,
    });
  }

  function toggleLineTax(idx: number, tt: TaxType) {
    setLines((prev) => prev.map((l, i) => {
      if (i !== idx) return l;
      const exists = l.taxes.find((t) => t.tax_type_id === tt.id);
      const taxes = exists
        ? l.taxes.filter((t) => t.tax_type_id !== tt.id)
        : [...l.taxes, {
            tax_type_id: tt.id,
            name: tt.name,
            percent: tt.percent,
            amount: Math.round((l.price * l.quantity * Number(tt.percent)) / 100),
            compound_tax: tt.compound_tax,
          }];
      return { ...l, taxes };
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    const body = {
      customer_id: customerId ? Number(customerId) : null,
      invoice_date: invoiceDate || null,
      due_date: dueDate || null,
      discount: invoiceDiscount,
      notes: notes || null,
      items: lines.map((l) => ({
        item_id: l.item_id,
        name: l.name,
        description: l.description || null,
        price: l.price,
        quantity: l.quantity,
        discount: l.discount,
        discount_val: l.discount_val,
        unit_name: l.unit_name || null,
        taxes: l.taxes.map((t) => ({
          tax_type_id: t.tax_type_id,
          amount: t.amount,
          percent: t.percent,
          compound_tax: t.compound_tax,
        })),
      })),
      taxes: [],
    };
    try {
      if (isEdit) {
        await api.put(`/v1/invoices/${id}`, body);
      } else {
        await api.post("/v1/invoices", body);
      }
      navigate("/invoices");
    } catch {
      setError("Save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-5xl">
      <h1 className="text-2xl font-semibold">{isEdit ? "Edit Invoice" : "New Invoice"}</h1>

      {/* Header fields */}
      <section className="bg-white rounded-lg shadow p-5 grid grid-cols-2 gap-4">
        <div className="space-y-1 col-span-2 md:col-span-1">
          <label className="text-sm font-medium text-slate-700">Customer</label>
          <select
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
          >
            <option value="">— Select customer —</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
        <div />
        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-700">Invoice date</label>
          <input type="date" value={invoiceDate} onChange={(e) => setInvoiceDate(e.target.value)}
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm" />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-700">Due date</label>
          <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)}
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm" />
        </div>
      </section>

      {/* Line items */}
      <section className="bg-white rounded-lg shadow p-5 space-y-4">
        <h2 className="text-sm font-semibold uppercase text-slate-500">Line Items</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-600 text-left">
              <tr>
                <th className="px-2 py-2 font-medium w-40">Item</th>
                <th className="px-2 py-2 font-medium">Name</th>
                <th className="px-2 py-2 font-medium w-20">Price</th>
                <th className="px-2 py-2 font-medium w-16">Qty</th>
                <th className="px-2 py-2 font-medium w-20">Discount</th>
                <th className="px-2 py-2 font-medium w-20">Taxes</th>
                <th className="px-2 py-2 font-medium w-24 text-right">Total</th>
                <th className="px-2 py-2 w-8"></th>
              </tr>
            </thead>
            <tbody>
              {lines.map((line, idx) => (
                <tr key={idx} className="border-t border-slate-100 align-top">
                  <td className="px-2 py-2">
                    <select
                      value={line.item_id ?? ""}
                      onChange={(e) => pickFromCatalog(idx, e.target.value)}
                      className="w-full border border-slate-300 rounded px-2 py-1 text-xs"
                    >
                      <option value="">— manual —</option>
                      {catalog.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-2 py-2">
                    <input value={line.name} onChange={(e) => updateLine(idx, { name: e.target.value })}
                      placeholder="Item name" required
                      className="w-full border border-slate-300 rounded px-2 py-1 text-xs" />
                  </td>
                  <td className="px-2 py-2">
                    <input type="number" min={0} value={line.price}
                      onChange={(e) => updateLine(idx, { price: Number(e.target.value) })}
                      className="w-full border border-slate-300 rounded px-2 py-1 text-xs" />
                  </td>
                  <td className="px-2 py-2">
                    <input type="number" min={1} value={line.quantity}
                      onChange={(e) => updateLine(idx, { quantity: Number(e.target.value) })}
                      className="w-full border border-slate-300 rounded px-2 py-1 text-xs" />
                  </td>
                  <td className="px-2 py-2">
                    <input type="number" min={0} value={line.discount_val}
                      onChange={(e) => updateLine(idx, { discount_val: Number(e.target.value) })}
                      className="w-full border border-slate-300 rounded px-2 py-1 text-xs" />
                  </td>
                  <td className="px-2 py-2">
                    <div className="space-y-1">
                      {taxTypes.map((tt) => (
                        <label key={tt.id} className="flex items-center gap-1 text-xs">
                          <input type="checkbox"
                            checked={line.taxes.some((t) => t.tax_type_id === tt.id)}
                            onChange={() => toggleLineTax(idx, tt)} />
                          {tt.name} ({tt.percent}%)
                        </label>
                      ))}
                    </div>
                  </td>
                  <td className="px-2 py-2 text-right font-mono text-xs">
                    {(calcLineTotal(line) / 100).toFixed(2)}
                  </td>
                  <td className="px-2 py-2">
                    {lines.length > 1 && (
                      <button type="button" onClick={() => setLines((p) => p.filter((_, i) => i !== idx))}
                        className="text-red-500 hover:text-red-700 text-xs">✕</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <button type="button" onClick={() => setLines((p) => [...p, blankLine()])}
          className="text-sm text-slate-600 hover:text-slate-900 border border-slate-300 rounded px-3 py-1">
          + Add line
        </button>

        {/* Totals */}
        <div className="flex flex-col items-end gap-1 text-sm pt-2 border-t border-slate-100">
          <div className="flex gap-8 text-slate-600">
            <span>Subtotal</span>
            <span className="font-mono w-24 text-right">{(subTotal / 100).toFixed(2)}</span>
          </div>
          {lineTaxTotal > 0 && (
            <div className="flex gap-8 text-slate-600">
              <span>Tax</span>
              <span className="font-mono w-24 text-right">{(lineTaxTotal / 100).toFixed(2)}</span>
            </div>
          )}
          <div className="flex gap-8 text-slate-600">
            <span>Discount</span>
            <input type="number" min={0} value={invoiceDiscount}
              onChange={(e) => setInvoiceDiscount(Number(e.target.value))}
              className="border border-slate-300 rounded px-2 py-0.5 text-xs w-24 text-right font-mono" />
          </div>
          <div className="flex gap-8 font-semibold text-slate-900 text-base">
            <span>Total</span>
            <span className="font-mono w-24 text-right">{(total / 100).toFixed(2)}</span>
          </div>
        </div>
      </section>

      {/* Notes */}
      <section className="bg-white rounded-lg shadow p-5 space-y-2">
        <label className="text-sm font-medium text-slate-700">Notes</label>
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3}
          className="w-full border border-slate-300 rounded px-3 py-2 text-sm" />
      </section>

      {error && <div className="text-sm text-red-600">{error}</div>}
      <div className="flex gap-2">
        <button type="submit" disabled={saving}
          className="bg-slate-900 hover:bg-slate-800 text-white text-sm font-medium rounded px-4 py-2 disabled:opacity-60">
          {saving ? "Saving…" : isEdit ? "Save changes" : "Create invoice"}
        </button>
        <button type="button" onClick={() => navigate("/invoices")}
          className="text-sm text-slate-600 hover:text-slate-900">
          Cancel
        </button>
      </div>
    </form>
  );
}
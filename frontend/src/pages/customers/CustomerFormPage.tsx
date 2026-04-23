import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../../api/client";
import type {
  Address,
  Country,
  Currency,
  Customer,
} from "../../types/masterData";

interface FormState {
  name: string;
  email: string;
  phone: string;
  contact_name: string;
  company_name: string;
  website: string;
  currency_id: string;
  enable_portal: boolean;
  billing: Address;
  shipping: Address;
}

function blankAddress(): Address {
  return {
    name: "",
    address_street_1: "",
    address_street_2: "",
    city: "",
    state: "",
    zip: "",
    phone: "",
    country_id: null,
  };
}

function initialState(): FormState {
  return {
    name: "",
    email: "",
    phone: "",
    contact_name: "",
    company_name: "",
    website: "",
    currency_id: "",
    enable_portal: false,
    billing: blankAddress(),
    shipping: blankAddress(),
  };
}

export function CustomerFormPage() {
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id && id !== "new");
  const navigate = useNavigate();
  const [form, setForm] = useState<FormState>(initialState);
  const [countries, setCountries] = useState<Country[]>([]);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get<Country[]>("/v1/countries"),
      api.get<Currency[]>("/v1/currencies"),
    ])
      .then(([c, cur]) => {
        setCountries(c.data);
        setCurrencies(cur.data);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!isEdit || !id) return;
    api
      .get<Customer>(`/v1/customers/${id}`)
      .then(({ data }) => {
        setForm({
          name: data.name ?? "",
          email: data.email ?? "",
          phone: data.phone ?? "",
          contact_name: data.contact_name ?? "",
          company_name: data.company_name ?? "",
          website: data.website ?? "",
          currency_id: data.currency_id ? String(data.currency_id) : "",
          enable_portal: data.enable_portal,
          billing: { ...blankAddress(), ...(data.billing ?? {}) },
          shipping: { ...blankAddress(), ...(data.shipping ?? {}) },
        });
      })
      .catch(() => setError("Failed to load customer"));
  }, [id, isEdit]);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }
  function updateAddress(
    side: "billing" | "shipping",
    key: keyof Address,
    value: Address[keyof Address]
  ) {
    setForm((f) => ({ ...f, [side]: { ...f[side], [key]: value } }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    const body = {
      ...form,
      currency_id: form.currency_id ? Number(form.currency_id) : null,
      email: form.email || null,
    };
    try {
      if (isEdit) {
        await api.put(`/v1/customers/${id}`, body);
      } else {
        await api.post("/v1/customers", body);
      }
      navigate("/customers");
    } catch {
      setError("Save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-4xl">
      <h1 className="text-2xl font-semibold">
        {isEdit ? "Edit Customer" : "New Customer"}
      </h1>

      <section className="bg-white rounded-lg shadow p-5 space-y-4">
        <h2 className="text-sm font-semibold uppercase text-slate-500">
          Primary details
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Display name" required value={form.name} onChange={(v) => update("name", v)} />
          <Field label="Email" type="email" value={form.email} onChange={(v) => update("email", v)} />
          <Field label="Phone" value={form.phone} onChange={(v) => update("phone", v)} />
          <Field
            label="Contact name"
            value={form.contact_name}
            onChange={(v) => update("contact_name", v)}
          />
          <Field
            label="Company name"
            value={form.company_name}
            onChange={(v) => update("company_name", v)}
          />
          <Field label="Website" value={form.website} onChange={(v) => update("website", v)} />
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-700">Currency</label>
            <select
              value={form.currency_id}
              onChange={(e) => update("currency_id", e.target.value)}
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
          <label className="flex items-center gap-2 mt-7 text-sm">
            <input
              type="checkbox"
              checked={form.enable_portal}
              onChange={(e) => update("enable_portal", e.target.checked)}
            />
            Enable customer portal login
          </label>
        </div>
      </section>

      <AddressSection
        title="Billing address"
        side="billing"
        value={form.billing}
        countries={countries}
        onChange={updateAddress}
      />
      <AddressSection
        title="Shipping address"
        side="shipping"
        value={form.shipping}
        countries={countries}
        onChange={updateAddress}
      />

      {error && <div className="text-sm text-red-600">{error}</div>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={saving}
          className="bg-slate-900 hover:bg-slate-800 text-white text-sm font-medium rounded px-4 py-2 disabled:opacity-60"
        >
          {saving ? "Saving…" : isEdit ? "Save changes" : "Create customer"}
        </button>
        <button
          type="button"
          onClick={() => navigate("/customers")}
          className="text-sm text-slate-600 hover:text-slate-900"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  required,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  required?: boolean;
}) {
  return (
    <div className="space-y-1">
      <label className="text-sm font-medium text-slate-700">
        {label}
        {required ? " *" : ""}
      </label>
      <input
        type={type}
        required={required}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
      />
    </div>
  );
}

function AddressSection({
  title,
  side,
  value,
  countries,
  onChange,
}: {
  title: string;
  side: "billing" | "shipping";
  value: Address;
  countries: Country[];
  onChange: (
    side: "billing" | "shipping",
    key: keyof Address,
    value: Address[keyof Address]
  ) => void;
}) {
  return (
    <section className="bg-white rounded-lg shadow p-5 space-y-4">
      <h2 className="text-sm font-semibold uppercase text-slate-500">{title}</h2>
      <div className="grid grid-cols-2 gap-4">
        <Field
          label="Name"
          value={value.name ?? ""}
          onChange={(v) => onChange(side, "name", v)}
        />
        <Field
          label="Phone"
          value={value.phone ?? ""}
          onChange={(v) => onChange(side, "phone", v)}
        />
        <Field
          label="Street address"
          value={value.address_street_1 ?? ""}
          onChange={(v) => onChange(side, "address_street_1", v)}
        />
        <Field
          label="Street address (cont.)"
          value={value.address_street_2 ?? ""}
          onChange={(v) => onChange(side, "address_street_2", v)}
        />
        <Field
          label="City"
          value={value.city ?? ""}
          onChange={(v) => onChange(side, "city", v)}
        />
        <Field
          label="State"
          value={value.state ?? ""}
          onChange={(v) => onChange(side, "state", v)}
        />
        <Field
          label="Zip"
          value={value.zip ?? ""}
          onChange={(v) => onChange(side, "zip", v)}
        />
        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-700">Country</label>
          <select
            value={value.country_id ?? ""}
            onChange={(e) =>
              onChange(side, "country_id", e.target.value ? Number(e.target.value) : null)
            }
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
          >
            <option value="">— Select —</option>
            {countries.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
      </div>
    </section>
  );
}

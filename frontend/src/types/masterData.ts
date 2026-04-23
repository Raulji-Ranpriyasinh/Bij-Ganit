// Shared TypeScript types for the Sprint 2 master-data endpoints.

export interface Country {
  id: number;
  code: string;
  name: string;
  phonecode: number;
}

export interface Currency {
  id: number;
  name: string;
  code: string;
  symbol: string | null;
  precision: number;
  thousand_separator: string;
  decimal_separator: string;
  swap_currency_symbol: boolean;
}

export interface Address {
  id?: number;
  name?: string | null;
  address_street_1?: string | null;
  address_street_2?: string | null;
  city?: string | null;
  state?: string | null;
  zip?: string | null;
  phone?: string | null;
  fax?: string | null;
  country_id?: number | null;
}

export interface Customer {
  id: number;
  name: string;
  email: string | null;
  phone: string | null;
  contact_name: string | null;
  company_name: string | null;
  website: string | null;
  enable_portal: boolean;
  currency_id: number | null;
  billing: Address | null;
  shipping: Address | null;
  created_at: string;
  updated_at: string;
}

export interface Unit {
  id: number;
  name: string;
  company_id: number | null;
}

export interface TaxType {
  id: number;
  name: string;
  percent: string; // Decimal serialized as string in JSON.
  compound_tax: boolean;
  collective_tax: boolean;
  type: string | null;
  description: string | null;
  company_id: number | null;
}

export interface ItemTax {
  id?: number;
  tax_type_id: number;
  name?: string;
  amount: number;
  percent: string;
  compound_tax: boolean;
}

export interface Item {
  id: number;
  name: string;
  description: string | null;
  price: number;
  tax_per_item: boolean;
  unit_id: number | null;
  currency_id: number | null;
  taxes: ItemTax[];
}

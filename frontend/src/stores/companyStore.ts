import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface Company {
  id: number;
  name: string;
  slug: string;
}

interface CompanyState {
  companies: Company[];
  activeCompanyId: number | null;
  setCompanies: (companies: Company[]) => void;
  setActiveCompany: (id: number) => void;
  clear: () => void;
}

export const useCompanyStore = create<CompanyState>()(
  persist(
    (set) => ({
      companies: [],
      activeCompanyId: null,
      setCompanies: (companies) =>
        set((s) => ({
          companies,
          activeCompanyId:
            s.activeCompanyId && companies.some((c) => c.id === s.activeCompanyId)
              ? s.activeCompanyId
              : companies[0]?.id ?? null,
        })),
      setActiveCompany: (id) => set({ activeCompanyId: id }),
      clear: () => set({ companies: [], activeCompanyId: null }),
    }),
    { name: "bij-ganit-company" }
  )
);

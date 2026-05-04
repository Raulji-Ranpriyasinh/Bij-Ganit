import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { RequireAuth } from "./components/RequireAuth";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import InvoicesListPage from "./pages/InvoicesListPage";
import InvoiceFormPage from "./pages/InvoiceFormPage";
import { CustomerFormPage } from "./pages/customers/CustomerFormPage";
import { CustomersListPage } from "./pages/customers/CustomersListPage";
import { ItemFormPage } from "./pages/items/ItemFormPage";
import { ItemsListPage } from "./pages/items/ItemsListPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          }
        >
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/customers" element={<CustomersListPage />} />
          <Route path="/customers/new" element={<CustomerFormPage />} />
          <Route path="/customers/:id" element={<CustomerFormPage />} />
          <Route path="/items" element={<ItemsListPage />} />
          <Route path="/items/new" element={<ItemFormPage />} />
          <Route path="/items/:id" element={<ItemFormPage />} />
          <Route path="/invoices" element={<InvoicesListPage />} />
          <Route path="/invoices/new" element={<InvoiceFormPage />} />
          <Route path="/invoices/:id" element={<InvoiceFormPage />} />
          <Route path="/estimates" element={<PlaceholderPage title="Estimates" />} />
          <Route path="/expenses" element={<PlaceholderPage title="Expenses" />} />
          <Route path="/payments" element={<PlaceholderPage title="Payments" />} />
          <Route
            path="/recurring-invoices"
            element={<PlaceholderPage title="Recurring Invoices" />}
          />
          <Route path="/settings" element={<PlaceholderPage title="Settings" />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

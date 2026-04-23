import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { RequireAuth } from "./components/RequireAuth";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";

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
          <Route path="/customers" element={<PlaceholderPage title="Customers" />} />
          <Route path="/items" element={<PlaceholderPage title="Items" />} />
          <Route path="/invoices" element={<PlaceholderPage title="Invoices" />} />
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

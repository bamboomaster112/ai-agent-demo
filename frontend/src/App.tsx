import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "./auth/AuthProvider";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { LoginPage } from "./auth/LoginPage";
import { SignupPage } from "./auth/SignupPage";
import { Layout } from "./components/Layout";
import { DashboardPage } from "./pages/DashboardPage";
import { NewMigrationPage } from "./pages/NewMigrationPage";
import { MigrationDetailPage } from "./pages/MigrationDetailPage";
import { HistoryPage } from "./pages/HistoryPage";
import { PreferencesPage } from "./pages/PreferencesPage";
import { UsersPage } from "./pages/admin/UsersPage";
import { AISettingsPage } from "./pages/admin/AISettingsPage";
import { RAGDocumentsPage } from "./pages/admin/RAGDocumentsPage";
import { AnalyticsPage } from "./pages/admin/AnalyticsPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          {/* Protected routes */}
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/migrate/new" element={<NewMigrationPage />} />
            <Route path="/migrate/:id" element={<MigrationDetailPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/preferences" element={<PreferencesPage />} />

            {/* Admin routes */}
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute requireAdmin>
                  <UsersPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/settings"
              element={
                <ProtectedRoute requireAdmin>
                  <AISettingsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/rag"
              element={
                <ProtectedRoute requireAdmin>
                  <RAGDocumentsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/analytics"
              element={
                <ProtectedRoute requireAdmin>
                  <AnalyticsPage />
                </ProtectedRoute>
              }
            />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Toaster position="bottom-right" />
      </AuthProvider>
    </BrowserRouter>
  );
}

import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate
} from "react-router-dom";

import LoginPage from "./pages/LoginPage";
import Dashboard from "./pages/Dashboard";
import KnowledgeGraph from "./pages/KnowledgeGraph";
import EntityResolution from "./pages/EntityResolution";
import DataSources from "./pages/DataSources";
import AuditTrail from "./pages/AuditTrail";
import Reports from "./pages/Reports";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />

        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/graph"
          element={
            <ProtectedRoute>
              <KnowledgeGraph />
            </ProtectedRoute>
          }
        />

        <Route
          path="/entity-resolution"
          element={
            <ProtectedRoute>
              <EntityResolution />
            </ProtectedRoute>
          }
        />

        <Route
          path="/data-sources"
          element={
            <ProtectedRoute>
              <DataSources />
            </ProtectedRoute>
          }
        />

        <Route
          path="/audit-trail"
          element={
            <ProtectedRoute>
              <AuditTrail />
            </ProtectedRoute>
          }
        />

        <Route
          path="/reports"
          element={
            <ProtectedRoute>
              <Reports />
            </ProtectedRoute>
          }
        />

        <Route path="/knowledge-graph" element={<Navigate to="/graph" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
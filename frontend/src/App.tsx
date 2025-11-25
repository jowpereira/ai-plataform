import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LandingPage from "@/pages/website/LandingPage";
import LoginPage from "@/pages/auth/LoginPage";
import PlatformLayout from "@/layouts/PlatformLayout";
import DashboardPage from "@/pages/platform/dashboard/DashboardPage";
import StudioPage from "@/pages/platform/studio/StudioPage";
import AgentListPage from "@/pages/platform/agents/AgentListPage";
import WorkflowListPage from "@/pages/platform/workflow/WorkflowListPage";
import ChatPage from "@/pages/platform/chat/ChatPage";
import DebugPage from "@/pages/platform/debug/DebugPage";
import UsersPage from "@/pages/platform/admin/UsersPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />

        {/* Platform Routes (Protected) */}
        <Route path="/platform" element={<PlatformLayout />}>
          <Route index element={<Navigate to="/platform/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="agents" element={<AgentListPage />} />
          <Route path="workflows" element={<WorkflowListPage />} />
          <Route path="studio" element={<StudioPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="debug" element={<DebugPage />} />
          <Route path="users" element={<UsersPage />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

import { createBrowserRouter } from "react-router-dom";
import LoginPage from "../pages/LoginPage";
import DashboardPage from "../pages/Dashboard";
import TicketsPage from "../pages/TicketsPage";
import TicketViewPage from "../pages/TicketViewPage";
import ProtectedRoute from "./ProtectedRoute";
import PageWrapper from "../components/layout/PageWrapper";

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },

  {
    path: "/",
    element: (
      <ProtectedRoute>
        <PageWrapper />
      </ProtectedRoute>
    ),
    children: [
      { path: "dashboard", element: <DashboardPage /> },
      { path: "tickets", element: <TicketsPage /> },
      { path: "tickets/:id", element: <TicketViewPage /> },
    ],
  },
]);

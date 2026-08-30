import React from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { isLoggedIn } from "../services/api";

export default function ProtectedRoute() {
  const location = useLocation();
  return isLoggedIn() ? (
    <Outlet />
  ) : (
    <Navigate to="/login" replace state={{ from: location }} />
  );
}

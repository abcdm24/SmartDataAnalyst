import React from "react";
import { Routes, Route } from "react-router-dom";
import MasterLayout from "../components/layout/MasterLayout";
import DataAnalysisPage from "../pages/DataAnalysisPage";
import HistoryPage from "../pages/HistoryPage";

const AppRoutes: React.FC = () => (
  <Routes>
    <Route element={<MasterLayout />}>
      <Route path="/" element={<DataAnalysisPage />} />
      <Route path="/data-analysis" element={<DataAnalysisPage />} />
      <Route path="/history" element={<HistoryPage />} />
    </Route>
  </Routes>
);

export default AppRoutes;

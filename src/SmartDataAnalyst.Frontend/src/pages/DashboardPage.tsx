import { useEffect, useState } from "react";
import { getDatasetSummary } from "../api/dashboardApi";
import type { DatasetSummaryResponse } from "../api/dashboardApi";
import { EmptyDashboardState } from "../components/dashboard/emptydashboardstate";
import { DashboardLoading } from "../components/dashboard/dashboardloading";
import { DashboardError } from "../components/dashboard/dashboarderror";
import { DashboardSummary } from "../components/dashboard/dashboardsummary";

interface DashboardPageProps {
  datasetId?: string;
}

export default function DashboardPage({ datasetId }: DashboardPageProps) {
  const [summary, setSummary] = useState<DatasetSummaryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!datasetId) return;

    const loadSummary = async () => {
      try {
        setLoading(true);
        setError(null);
        //alert(`datasetId: ${datasetId}`);
        const data = await getDatasetSummary(datasetId);
        setSummary(data);
        //alert(`data: ${data}`);
      } catch (err) {
        setError("Failed to load dataset summary");
      } finally {
        setLoading(false);
      }
    };

    loadSummary();
  }, [datasetId]);

  if (!datasetId) {
    return <EmptyDashboardState />;
  }

  if (loading) {
    return <DashboardLoading />;
  }

  if (error) {
    return <DashboardError message={error} />;
  }

  return summary ? <DashboardSummary summary={summary} /> : null;
}

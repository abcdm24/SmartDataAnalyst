import apiClient from "./apiClient";

export const fetchHistory = async () => {
  const response = await apiClient.get("/history");
  return response.data ?? [];
};

export async function fetchHistoryItem(id: string) {
  const res = await apiClient.get(`history/${id}`);
  return res.data;
}

export async function deleteHistoryItem(id: string) {
  const res = await apiClient.delete(`/history/${id}`);
  return res.data;
}

export const clearHistory = async () => {
  const response = await apiClient.delete(`/history/clear`);
  return response.data;
};

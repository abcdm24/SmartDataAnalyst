import apiClient from "./apiClient";

export const fetchHistory = async () => {
  const response = await apiClient.get("/history");
  return response.data;
};

export const clearHistory = async () => {
  const response = await apiClient.delete("/history/clear");
  return response.data;
};

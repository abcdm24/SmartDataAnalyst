import apiClient from "./apiClient";

export interface ColumnInfo {
  name: string;
  type: string;
  missing: number;
}

export interface NumericSummary {
  column: string;
  min: number;
  max: number;
  mean: string; // or number if backend sends numeric
  missing: number;
}

// export interface Summary {
//   file_name: string;
//   rows: number;
//   columns: number;
//   columns_info: ColumnInfo[];
//   numeric_summary: NumericSummary[];
// }

// export interface DatasetSummary {
//   summary: Summary;
//   insights?: string[];
//   warnings?: string[];
// }

export interface DatasetSummaryDetails {
  file_name: string;
  rows: number;
  columns: number;
  columns_info: Record<string, ColumnInfo>;
  numeric_summary: Record<string, NumericSummary>;
}

export interface DatasetSummaryResponse {
  summary: DatasetSummaryDetails;
  insights?: string[];
  warnings?: string[];
}

export const getDatasetSummary = async (
  datasetId: string
): Promise<DatasetSummaryResponse> => {
  const response = await apiClient.post("/dashboard/summary", {
    file_id: datasetId,
  });
  //alert(`response: ${JSON.stringify(response.data)}`);
  console.log(`response: ${JSON.stringify(response.data)}`);
  return response.data;
};

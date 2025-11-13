import apiClient from "./apiClient";

export const uploadCsv = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
};

export const queryData = async (file: string | undefined, query: string) => {
  console.log(`query: ${query}`);
  const formData = new FormData();
  formData.append("filename", file!);
  formData.append("question", query);
  const response = await apiClient.post("/query", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  console.log(`response data: ${response.data}`);
  return response.data;
};

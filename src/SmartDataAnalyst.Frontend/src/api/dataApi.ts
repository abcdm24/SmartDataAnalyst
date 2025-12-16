import apiClient from "./apiClient";

export const uploadCsv = async (file: File) => {
  // await new Promise((resolve) => setTimeout(resolve, 3000));
  // return { preview: [] };
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post("/data/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
};

export const queryData = async (file: string | undefined, query: string) => {
  // await new Promise((resolve) => setTimeout(resolve, 3000));
  // return "Service unavailable";

  console.log(`query: ${query}`);
  const formData = new FormData();
  formData.append("filename", file!);
  formData.append("question", query);
  const response = await apiClient.post("/data/query", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  console.log(`response data: ${response.data}`);
  return response.data;
};

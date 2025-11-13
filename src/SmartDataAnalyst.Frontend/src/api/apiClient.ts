import axios from "axios";

const apiClient = axios.create({
  baseURL: "http://localhost:8000/api/data",
});

export default apiClient;

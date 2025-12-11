import React, { useState } from "react";
import {
  Container,
  Tabs,
  Tab,
  Form,
  Button,
  Table,
  //Spinner,
  Alert,
} from "react-bootstrap";
//import axios from "axios";
import FileUpload from "../components/FileUpload";
import ChatMessage from "../components/ChatMessage";
import LoadingSpinner from "../components/LoadingSpinner";
import { uploadCsv, queryData } from "../api/dataApi";
import { useAppContext } from "../context/AppContext";

interface Chat {
  sender: "user" | "ai";
  message: string;
}

const DataAnalysisPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("assistant");
  const [file, setFile] = useState<File | null>(null);
  const [dataPreview, setDataPreview] = useState<string[][]>([]);
  const [query, setQuery] = useState("");
  const [chat, setChat] = useState<Chat[]>([]);
  //const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { setCurrentFilename } = useAppContext();

  //const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

  // const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  //   if (e.target.files && e.target.files.length > 0) {
  //     setFile(e.target.files[0]);
  //     setResponse("");
  //     setError("");
  //   }
  // };

  const handleUpload = async () => {
    if (!file) {
      setError("please select a csv file before uploading.");
      return;
    }

    setLoading(true);
    setError("");
    setChat([]);
    setCurrentFilename(file.name);
    try {
      // const formData = new FormData();
      // formData.append("file", file);

      // const res = await axios.post(`${API_BASE}/upload`, formData, {
      //   headers: { "content-type": "multipart/form-data" },
      // });

      // if (res.data && res.data.preview) {
      //   setDataPreview(res.data.preview);
      // } else {
      //   setDataPreview([]);
      // }

      const result = await uploadCsv(file);
      console.log(`upload result: ${result.preview}`);
      setDataPreview(result.preview || []);
    } catch (err) {
      console.error(err);
      setError("Error uploading or parsing the file.");
    } finally {
      setLoading(false);
    }
  };

  const handleAsk = async () => {
    if (!query.trim()) {
      setError("Please enter a question for the AI assistant.");
      return;
    }

    setLoading(true);
    setError("");

    const userMsg: Chat = { sender: "user", message: query };
    setChat((prev) => [...prev, userMsg]);
    setQuery("");

    try {
      // const res = await axios.post(`${API_BASE}/query`, { query });
      // const aiReponse = res.data.answer || "No response from AI.";
      // //setResponse(res.data.answer || "No response from AI.");

      const result = await queryData(file?.name, query);
      const aiMsg: Chat = {
        sender: "ai",
        message: result.answer || "Np response from AI.",
      };
      setChat((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error(err);
      setError("Error while querying AI assistant.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container className="mt-4">
      <h2 className="mb-3">Smart Data Analysis</h2>

      <Tabs
        id="data-analysis-tabs"
        activeKey={activeTab}
        onSelect={(k) => setActiveTab(k || "assistant")}
        className="mb-3"
      >
        {/* 🧠 AI Assistant Tab */}
        <Tab eventKey="assistant" title="AI Assistant">
          <div className="p-3 border rounded bg-light">
            {/* <Form.Group controlId="formFile" className="mb-3">
              <Form.Label>Upload CSV File</Form.Label>
              <Form.Control
                type="file"
                accept=".csv"
                onChange={handleFileChange}
              />
            </Form.Group>
            <Button variant="primary" onClick={handleUpload} disabled={loading}>
              {loading ? (
                <>
                  <Spinner as="span" animation="border" size="sm" />{" "}
                  Uploading...
                </>
              ) : (
                "Upload & Preview"
              )}
            </Button> */}

            <FileUpload
              label="Upload CSV File"
              onFileSelect={(file) => setFile(file)}
              onUpload={handleUpload}
              uploading={loading}
            />

            {error && (
              <Alert variant="danger" className="mt-3">
                {error}
              </Alert>
            )}

            {/* {Array.isArray(dataPreview) && Array.isArray(dataPreview[0]) && ( */}
            {dataPreview.length > 0 && (
              <div className="mt-4">
                <h5>Data Preview</h5>
                <Table striped bordered hover size="sm">
                  <thead>
                    <tr>
                      {/* {dataPreview[0].map((header, i) => (
                        <th key={i}>{header}</th>
                      ))} */}
                      {Object.keys(dataPreview[0]).map((key) => (
                        <th key={key}>{key}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {/* {dataPreview.slice(1, 6).map((row, i) => (
                      <tr key={i}>
                        {row.map((cell, j) => (
                          <td key={j}>{cell}</td>
                        ))}
                      </tr>
                    ))} */}
                    {dataPreview.map((row, index) => (
                      <tr key={index}>
                        {Object.values(row).map((val, i) => (
                          <td key={i}>{val}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            )}
            {/* : (
              <Alert variant="info">
                No structured preview available for this file
              </Alert>
            ) */}

            {dataPreview.length > 0 && (
              <div className="mt-4">
                <Form.Group controlId="queryInput">
                  <Form.Label>Ask AI about your data</Form.Label>
                  <Form.Control
                    data-testid="query"
                    id="query"
                    type="text"
                    name="query"
                    placeholder="e.g., what is the average sales per region?"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                  />
                </Form.Group>

                <Button
                  name="AskAI"
                  variant="success"
                  className="mt-3"
                  onClick={handleAsk}
                  disabled={loading}
                >
                  {loading
                    ? // <>
                      //   <Spinner as="span" animation="border" size="sm" />
                      //   Thinking...
                      // </>
                      "Thinking..."
                    : "Ask AI"}
                </Button>
                {/* {response && (
                  <Alert variant="info" className="mt-4">
                    <strong>AI Response</strong> {response}
                  </Alert>
                )} */}
                {/* Chat Display */}
                <div className="mt-4">
                  {chat.map((msg, index) => (
                    <ChatMessage
                      key={index}
                      sender={msg.sender}
                      message={msg.message}
                    />
                  ))}

                  {loading && (
                    <LoadingSpinner text="AI is analyzing..." centered />
                  )}
                </div>
              </div>
            )}
          </div>
        </Tab>

        {/* Dashboard Tab (Placeholder) */}
        <Tab eventKey="dashboard" title="Dashboard (Coming Soon)">
          <div className="p-4 text-center text-muted">
            <p>Interactive data dashboard coming soon.</p>
          </div>
        </Tab>
      </Tabs>
    </Container>
  );
};

export default DataAnalysisPage;

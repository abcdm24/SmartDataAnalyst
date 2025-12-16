import React, { useEffect, useState } from "react";
import {
  Container,
  Table,
  Spinner,
  Alert,
  Button,
  Modal,
} from "react-bootstrap";
//import axios from "axios";
import LoadingSpinner from "../components/LoadingSpinner";
import {
  fetchHistory,
  fetchHistoryItem,
  clearHistory,
  deleteHistoryItem,
} from "../api/historyApi";

interface HistoryListItem {
  id: string;
  file_name: string;
  upload_date: string;
  query_count: number;
}

interface HistoryQuery {
  question: string;
  answer: string;
  timestamp: string;
}

interface HistorySession {
  id: string;
  file_name: string;
  upload_date: string;
  queries: HistoryQuery[];
}

const HistoryPage: React.FC = () => {
  const [history, setHistory] = useState<HistoryListItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<HistorySession | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalLoading, setModalLoading] = useState(false);
  const [error, setError] = useState("");
  const [showModal, setShowModal] = useState(false);

  //const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

  const loadHistory = async () => {
    setLoading(true);
    setError("");

    try {
      //const res = await axios.get(`${API_BASE}/history`);
      //setHistory(res.data || []);
      const result = await fetchHistory();
      setHistory(result || []);
    } catch (err) {
      console.error(err);
      setError("Failed to load history from backend.");
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (id: string) => {
    setModalLoading(true);
    setSelectedItem(null);
    setShowModal(true);

    try {
      const data = await fetchHistoryItem(id);
      setSelectedItem(data);
    } catch (err) {
      console.error(err);
      setError("Failed to load sessions details.");
    } finally {
      setModalLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this session?")) return;
    try {
      await deleteHistoryItem(id);
      setHistory(history.filter((h) => h.id !== id));
      //loadHistory();
    } catch (err) {
      console.error(err);
      setError("Failed to delete this history session.");
    }
  };

  const handleClearAll = async () => {
    if (!confirm("Clear all history records?")) return;
    try {
      await clearHistory();
      setHistory([]);
    } catch (err) {
      console.error(err);
      setError("Failed to clear history.");
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <Container className="mt-4">
      <h2 className="mb-3 d-flex justify-content-between align-items-center">
        Analysis History
        <Button variant="danger" size="sm" onClick={handleClearAll} disabled>
          Clear All
        </Button>
      </h2>

      {error && <Alert variant="danger">{error}</Alert>}
      {/* <div className="mb-3">
        <Button variant="danger" onClick={handleClear}>
          Clear All History
        </Button>
      </div> */}
      {loading ? (
        // <div className="text-center mt-5">
        //   <Spinner animation="border" />
        //   <p className="mt-2 text-muted">Loading history...</p>
        // </div>
        <LoadingSpinner text="Loading your history..." centered />
      ) : // : error ? (
      //   <Alert variant="danger">{error}</Alert>
      //)
      history.length === 0 ? (
        <Alert variant="info">No history records found.</Alert>
      ) : (
        <Table striped bordered hover responsive>
          <thead>
            <tr>
              <th>#</th>
              <th>File Name</th>
              <th>Uploaded</th>
              <th>Queries</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {history.map((item, index) => (
              <tr key={item.id}>
                <td>{index + 1}</td>
                <td>{item.file_name}</td>
                <td>{new Date(item.upload_date).toLocaleString()}</td>
                <td>{item.query_count}</td>
                {/* <td
                  style={{
                    maxWidth: 250,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {item.query}
                </td> */}
                {/* <td>{new Date(item.timestamp).toLocaleString()}</td> */}

                <td>
                  <Button
                    size="sm"
                    variant="outline-primary"
                    className="me-2"
                    onClick={() => handleViewDetails(item.id)}
                  >
                    View
                  </Button>
                  <Button
                    size="sm"
                    variant="outline-danger"
                    onClick={() => handleDelete(item.id)}
                  >
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      {/* Modal for Details */}
      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Session Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {modalLoading ? (
            <div className="text-center">
              <Spinner animation="border" />
              <p className="text-muted mt-2">Loading...</p>
            </div>
          ) : selectedItem ? (
            <>
              <h5>{selectedItem.file_name}</h5>
              <p className="text-muted">
                Uploaded on{" "}
                {new Date(selectedItem.upload_date).toLocaleString()}
              </p>

              {selectedItem.queries.length === 0 ? (
                <Alert variant="info">No queries recorded.</Alert>
              ) : (
                <Table bordered hover size="sm">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Question</th>
                      <th>Answer</th>
                      <th>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedItem.queries.map((q, i) => (
                      <tr key={i}>
                        <td>{i + 1}</td>
                        <td>{q.question}</td>
                        <td style={{ maxWidth: 350 }}>{q.answer}</td>
                        <td>{new Date(q.timestamp).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </>
          ) : (
            // <Spinner animation="border" />
            <Alert variant="warning">No session selected.</Alert>
          )}
        </Modal.Body>
      </Modal>
    </Container>
  );
};

export default HistoryPage;

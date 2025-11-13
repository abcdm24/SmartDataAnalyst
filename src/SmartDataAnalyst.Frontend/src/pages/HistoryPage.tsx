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
import { fetchHistory, clearHistory } from "../api/historyApi";

interface HistoryItem {
  id: string;
  fileName: string;
  uploadDate: string;
  queries: {
    question: string;
    answer: string;
    timestamp: string;
  }[];
}

const HistoryPage: React.FC = () => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);
  const [showModal, setShowModal] = useState(false);

  //const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

  const loadHistory = async () => {
    setLoading(true);
    setError("");

    try {
      //const res = await axios.get(`${API_BASE}/history`);
      //setHistory(res.data || []);
      const result = await fetchHistory();
      setHistory(result);
    } catch (err) {
      console.error(err);
      setError("Failed to load history from backend.");
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
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

  const handleViewDetails = (item: HistoryItem) => {
    setSelectedItem(item);
    setShowModal(true);
  };

  return (
    <Container className="mt-4">
      <h2 className="mb-3">Analysis History</h2>

      {error && <Alert variant="danger">{error}</Alert>}
      {loading ? (
        // <div className="text-center mt-5">
        //   <Spinner animation="border" />
        //   <p className="mt-2 text-muted">Loading history...</p>
        // </div>
        <LoadingSpinner text="Loading your history..." centered />
      ) : error ? (
        <Alert variant="danger">{error}</Alert>
      ) : history.length === 0 ? (
        <Alert variant="info">No history records found.</Alert>
      ) : (
        <Table striped bordered hover responsive>
          <thead>
            <tr>
              <th>#</th>
              <th>File Name</th>
              <th>Upload Date</th>
              <th>Queries</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {history.map((item, index) => (
              <tr key={item.id}>
                <td>{index + 1}</td>
                <td>{item.fileName}</td>
                <td>{new Date(item.uploadDate).toLocaleString()}</td>
                <td>{item.queries.length}</td>
                <td>
                  <Button
                    size="sm"
                    variant="outline-primary"
                    onClick={() => handleViewDetails(item)}
                  >
                    View
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
          {selectedItem ? (
            <>
              <h5>{selectedItem.fileName}</h5>
              <p className="text-muted">
                Uploaded in {new Date(selectedItem.uploadDate).toLocaleString()}
              </p>

              {selectedItem.queries.length > 0 ? (
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
                        <td>{q.answer}</td>
                        <td>{new Date(q.timestamp).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              ) : (
                <Alert variant="info">No queries recorded for this file.</Alert>
              )}
            </>
          ) : (
            <Spinner animation="border" />
          )}
        </Modal.Body>
      </Modal>
    </Container>
  );
};

export default HistoryPage;

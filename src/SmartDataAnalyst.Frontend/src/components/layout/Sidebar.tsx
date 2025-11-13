import React from "react";
import { Accordion } from "react-bootstrap";
import { Link, useLocation } from "react-router-dom";
import { FaChartLine, FaHistory } from "react-icons/fa";

const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <div className="bg-light broder-end vh-100 p-2 sidebar">
      <Accordion defaultActiveKey="0">
        <Accordion.Item eventKey="0">
          <Accordion.Header>Analysis</Accordion.Header>
          <Accordion.Body>
            <Link
              to="/data-analysis"
              className={`d-block mb-2 nav-link ${
                location.pathname === "/data-analysis"
                  ? "fw-bold text-primary"
                  : ""
              }`}
            >
              <FaChartLine className="me-2" />
              Data Analysis
            </Link>
          </Accordion.Body>
        </Accordion.Item>
        <Accordion.Item eventKey="1">
          <Accordion.Header>History</Accordion.Header>
          <Accordion.Body>
            <Link
              to="/history"
              className={`d-block mb-2 nav-link ${
                location.pathname === "/history" ? "fw-bold text-primary" : ""
              }`}
            >
              <FaHistory className="me-2" />
              History
            </Link>
          </Accordion.Body>
        </Accordion.Item>
      </Accordion>
    </div>
  );
};

export default Sidebar;

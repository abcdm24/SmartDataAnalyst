import React from "react";
import { Container, Row, Col } from "react-bootstrap";
import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";
// import StatusIndicator from "./StatusIndicator";

const MasterLayout: React.FC = () => {
  return (
    <div className="d-flex flex-column vh=-100">
      <div className="d-flex justify-content-between align-items-center bg-dark p-2">
        <Navbar />
        <div className="me-3">{/* <StatusIndicator /> */}</div>
      </div>
      <Container fluid className="flex-grow-1">
        <Row className="h-100">
          <Col xs={12} md={3} lg={2} className="p-0">
            <Sidebar />
          </Col>
          <Col xs={12} md={9} lg={10} className="p-3 overflow-auto lg-light">
            <Outlet />
          </Col>
        </Row>
      </Container>
    </div>
  );
};

export default MasterLayout;

import React, { useState } from "react";
// import { Container, Row, Col } from "react-bootstrap";
//import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";
// import StatusIndicator from "./StatusIndicator";

const MasterLayout: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <div className="d-flex vh-100 overflow-hidden">
      {isSidebarOpen && (
        <div
          className="bg-dark text-white p-0"
          style={{ width: "240px", minHeight: "100vh" }}
        >
          <Sidebar />
        </div>
      )}
      {/* Right Content Area*/}
      <div className="flex-grow-1 d-flex flex-column">
        {/* Navbar */}
        <div className="d-flex justify-content-between align-items-center bg-dark text-white p-2">
          {/* Hamburger Icon*/}
          <span
            style={{ cursor: "pointer", fontSize: "24px", marginRight: "15px" }}
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          >
            ☰
          </span>
          <Navbar />
          {/* <div className="me-3">{<StatusIndicator />}</div> */}
        </div>
        {/* Main content*/}
        <div className="overflow-auto p-3" style={{ flexGrow: 1 }}>
          {/* <Outlet /> */}
          <div className="alert alert-warning" role="alert">
            <h1 className="display-4 fw-bold text-uppercase">
              Under Maintenance
            </h1>
            <p className="lead">
              We’ll be back shortly. Thank you for your patience.
            </p>
          </div>
        </div>
      </div>
    </div>
    // <div className="d-flex flex-column vh=-100">
    //   <div className="d-flex justify-content-between align-items-center bg-dark p-2">
    //     <Navbar />
    //     <div className="me-3">{/* <StatusIndicator /> */}</div>
    //   </div>
    //   <Container fluid className="flex-grow-1">
    //     <Row className="h-100">
    //       <Col xs={12} md={3} lg={2} className="p-0">
    //         <Sidebar />
    //       </Col>
    //       <Col xs={12} md={9} lg={10} className="p-3 overflow-auto lg-light">
    //         <Outlet />
    //       </Col>
    //     </Row>
    //   </Container>
    // </div>
  );
};

export default MasterLayout;

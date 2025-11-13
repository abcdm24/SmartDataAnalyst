import React from "react";
import { Navbar as BsNavbar, Container } from "react-bootstrap";

const Navbar: React.FC = () => {
  return (
    <BsNavbar bg="dark" variant="dark" expand="lg" className="px-3">
      <Container fluid>
        <BsNavbar.Brand href="/" className="fw-hold text-light">
          🧠 Smart Data Analyst
        </BsNavbar.Brand>
      </Container>
    </BsNavbar>
  );
};

export default Navbar;

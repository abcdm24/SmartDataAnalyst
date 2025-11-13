import React from "react";
import { Spinner } from "react-bootstrap";

interface LoadingSpinnerProps {
  text?: string;
  centered: boolean;
  size?: "sm" | undefined;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  text = "Loading...",
  centered = false,
  size = "sm",
}) => {
  return (
    <div
      className={`d-flex align-items-center ${
        centered ? "justify-content-center" : ""
      }`}
      style={{ minHeight: centered ? "100px" : "auto" }}
    >
      <Spinner animation="border" size={size} className="me-2" />
      <span className="text-muted">{text}</span>
    </div>
  );
};

export default LoadingSpinner;

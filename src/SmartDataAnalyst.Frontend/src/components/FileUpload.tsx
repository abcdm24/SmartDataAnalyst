import React from "react";
import { Form, Button } from "react-bootstrap";

interface FileUploadProps {
  label?: string;
  accept?: string;
  onFileSelect: (file: File | null) => void;
  onUpload?: () => void;
  uploading?: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({
  label = "Upload File",
  accept = ".csv",
  onFileSelect,
  onUpload,
  uploading = false,
}) => {
  const handleFileChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    if (e.target.type === "file") {
      const selectedFile = (e.target as HTMLInputElement).files?.[0] || null;
      onFileSelect(selectedFile);
    }
  };
  return (
    <div className="p-3 border rounded bg-light shadow-sm">
      <Form.Group controlId="fileUploadControl" className="mb-3">
        <Form.Label className="fw-semibold">{label}</Form.Label>
        <Form.Control
          type="file"
          accept={accept}
          onChange={handleFileChange}
          disabled={uploading}
          className="mb-2"
        />
      </Form.Group>

      {onUpload && (
        <Button
          className="mt-2"
          variant="primary"
          onClick={onUpload}
          disabled={uploading}
        >
          {uploading ? "uploading..." : "Upload"}
        </Button>
      )}
    </div>
  );
};

export default FileUpload;

import React from "react";
import { Card } from "react-bootstrap";

interface ChatMessageProps {
  sender: "user" | "ai";
  message: string;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ sender, message }) => {
  const isUser = sender === "user";

  return (
    <div
      className={`d-flex mb-3 ${
        isUser ? "justify-content-end" : "justify-content-start"
      }`}
    >
      <Card
        className={`p-2 shadow-sm ${
          isUser ? "bg-primary text-white" : "bg-light text-dark"
        }`}
        style={{
          maxWidth: "75%",
          borderRadius: "15px",
          whiteSpace: "pre-wrap",
        }}
      >
        <Card.Text className="mb-0">{message}</Card.Text>
      </Card>
    </div>
  );
};

export default ChatMessage;

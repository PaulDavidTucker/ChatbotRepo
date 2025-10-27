import React, { useState, useEffect, useRef } from "react";
import { FaCommentDots, FaPaperPlane } from "react-icons/fa";

const ChatbotWidget = ({ config }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const socket = useRef(null);
  const chatBodyRef = useRef(null);

  // Apply configuration
  const widgetConfig = {
    title: "AI Assistant",
    welcomeMessage: "Hello! How can I help you?",
    position: "bottom-right",
    primaryColor: "#007bff",
    ...config,
  };

  useEffect(() => {
    // Connect to your Django service with client identification
    const wsProtocol =
      window.location.protocol === "https:" ? "wss://" : "ws://";
    const wsURL = `${wsProtocol}${widgetConfig.apiEndpoint}/ws/chat/${widgetConfig.apiKey}/?domain=${encodeURIComponent(window.location.hostname)}`;

    socket.current = new WebSocket(wsURL);

    socket.current.onopen = () => {
      console.log("Connected to chatbot service");
    };

    socket.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "start") {
        // Handle start of streaming response
      } else if (data.type === "chunk") {
        setMessages((prev) => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];

          if (lastMsg && lastMsg.sender === "bot" && lastMsg.isLoading) {
            lastMsg.text = data.content;
            lastMsg.isLoading = false;
          } else if (lastMsg && lastMsg.sender === "bot") {
            lastMsg.text += data.content;
          } else {
            updated.push({ sender: "bot", text: data.content });
          }
          return updated;
        });
      } else if (data.type === "end") {
        setIsLoading(false);
      } else if (data.type === "welcome") {
        setMessages([{ sender: "bot", text: data.message }]);
      } else {
        setMessages((prev) => [...prev, { sender: "bot", text: data.message }]);
        setIsLoading(false);
      }
    };

    socket.current.onclose = () => {
      console.error("Chat socket closed unexpectedly");
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Connection lost. Please refresh the page." },
      ]);
      setIsLoading(false);
    };

    return () => {
      if (socket.current) {
        socket.current.close();
      }
    };
  }, [widgetConfig.apiKey, widgetConfig.apiEndpoint]);

  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const toggleChatWindow = () => {
    setIsOpen((prev) => !prev);
  };

  const handleFormSubmit = (event) => {
    event.preventDefault();
    const message = inputValue.trim();
    if (
      message === "" ||
      !socket.current ||
      socket.current.readyState !== WebSocket.OPEN
    ) {
      return;
    }

    setMessages((prevMessages) => [
      ...prevMessages,
      { sender: "user", text: message },
    ]);

    setMessages((prevMessages) => [
      ...prevMessages,
      { sender: "bot", text: "", isLoading: true },
    ]);
    setIsLoading(true);

    socket.current.send(
      JSON.stringify({
        message: message,
        metadata: {
          url: window.location.href,
          timestamp: new Date().toISOString(),
        },
      }),
    );

    setInputValue("");
  };

  // Dynamic styles based on config
  const widgetStyles = {
    "--primary-color": widgetConfig.primaryColor,
    "--position-right": widgetConfig.position.includes("right")
      ? "20px"
      : "auto",
    "--position-left": widgetConfig.position.includes("left") ? "20px" : "auto",
  };

  return (
    <div className="chatbot-container" style={widgetStyles}>
      <div className="chatbot-widget" onClick={toggleChatWindow}>
        <FaCommentDots />
      </div>

      <div className={`chat-window ${isOpen ? "open" : ""}`}>
        <div className="chat-header">
          <h3>{widgetConfig.title}</h3>
          <button onClick={toggleChatWindow} className="close-chat-btn">
            &times;
          </button>
        </div>
        <div className="chat-body" ref={chatBodyRef}>
          {messages.map((msg, index) => (
            <div key={index} className={`chat-message ${msg.sender}`}>
              {msg.isLoading ? (
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              ) : (
                msg.text
              )}
            </div>
          ))}
        </div>
        <div className="chat-footer">
          <form onSubmit={handleFormSubmit}>
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask a question..."
              autoComplete="off"
            />
            <button type="submit">
              <FaPaperPlane />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatbotWidget;

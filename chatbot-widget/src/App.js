import React from "react";
import ChatbotWidget from "./ChatbotWidget";
import "./App.css";

function App() {
  // This is just for development/testing
  // The actual widget will be embedded differently
  const testConfig = {
    apiKey: "test-api-key",
    apiEndpoint: "localhost:8000",
    title: "Test Assistant",
    primaryColor: "#007bff",
  };

  return (
    <div className="App">
      <h1>Chatbot Widget Test Page</h1>
      <p>This is just for testing the widget during development.</p>
      <ChatbotWidget config={testConfig} />
    </div>
  );
}

export default App;

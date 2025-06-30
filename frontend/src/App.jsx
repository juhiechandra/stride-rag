import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import "./App.css";
import HomePage from "./pages/HomePage";
import DocumentPage from "./pages/DocumentPage";
import ChatPage from "./pages/ChatPage";
import UploadPage from "./pages/UploadPage";
import Documents from "./pages/Documents";
import NotFound from "./pages/NotFound";

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/document/*" element={<DocumentPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

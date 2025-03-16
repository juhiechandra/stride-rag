import styled from "styled-components";
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Document, Page, pdfjs } from "react-pdf";
import {
  Send,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  ArrowLeft,
  ArrowRight,
  Trash2,
  ChevronDown,
  Download,
} from "react-feather";
import { sendChatMessage, listDocuments, deleteDocument } from "../utils/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

// Ensure the correct worker is loaded
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

const Container = styled.div`
  display: flex;
  height: calc(100vh - 4rem);
  background: #1e1e1e;
  margin: -2rem;
`;

const PDFSection = styled.div`
  flex: 1;
  border-right: 1px solid #2c2c2c;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
`;

const PDFControls = styled.div`
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  background: #2c2c2c;
  border-bottom: 1px solid #374151;
  justify-content: space-between;
`;

const ControlsLeft = styled.div`
  display: flex;
  gap: 0.5rem;
`;

const ControlsRight = styled.div`
  display: flex;
  gap: 0.5rem;
`;

const DocumentSelector = styled.div`
  position: relative;
  margin-right: 1rem;
`;

const DocumentButton = styled.button`
  background: #374151;
  border: none;
  color: #e0e0e0;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
`;

const DropdownMenu = styled.div`
  position: absolute;
  top: 100%;
  left: 0;
  width: 250px;
  background: #2c2c2c;
  border: 1px solid #374151;
  border-radius: 4px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 10;
  max-height: 300px;
  overflow-y: auto;
  display: ${(props) => (props.isOpen ? "block" : "none")};
`;

const DropdownItem = styled.div`
  padding: 0.75rem 1rem;
  cursor: pointer;
  color: #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: space-between;

  &:hover {
    background: #374151;
  }
`;

const ControlButton = styled.button`
  background: transparent;
  border: none;
  color: #9ca3af;
  padding: 0.5rem;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;

  &:hover {
    background: #374151;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const PDFViewer = styled.div`
  flex: 1;
  overflow-y: auto;
  background: #1e1e1e;

  .react-pdf__Document {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2rem;
  }

  .react-pdf__Page {
    margin-bottom: 2rem;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);

    canvas {
      max-width: 100%;
      height: auto !important;
    }
  }
`;

const ChatSection = styled.div`
  width: 400px;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  position: relative;
  border-left: 1px solid #2c2c2c;
`;

const ChatHeader = styled.div`
  padding: 1rem;
  color: #e0e0e0;
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #2c2c2c;
  background: #1e1e1e;
`;

const ChatMessages = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background: #1e1e1e;
`;

const MessageWrapper = styled.div`
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
`;

const Avatar = styled.div`
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background: #6366f1;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  font-size: 0.875rem;
  flex-shrink: 0;
`;

const LoadingAvatar = styled(Avatar)`
  background: #374151;
`;

const MessageContent = styled.div`
  background: #2c2c2c;
  padding: 1rem;
  border-radius: 8px;
  flex: 1;
  color: #e0e0e0;
  font-size: 0.875rem;

  p {
    margin: 0;
    line-height: 1.5;
  }

  code {
    background: #1e1e1e;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-family: "JetBrains Mono", monospace;
    font-size: 0.9em;
  }
`;

const ChatInput = styled.div`
  padding: 1rem;
  background: #1e1e1e;
  border-top: 1px solid #2c2c2c;
`;

const InputForm = styled.form`
  display: flex;
  gap: 0.5rem;
  position: relative;
`;

const Input = styled.input`
  flex: 1;
  padding: 0.75rem 1rem;
  background: #2c2c2c;
  border: 1px solid #374151;
  border-radius: 8px;
  color: #e0e0e0;
  font-size: 0.875rem;

  &:focus {
    outline: none;
    border-color: #6366f1;
  }

  &::placeholder {
    color: #9ca3af;
  }
`;

const SendButton = styled.button`
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  color: #6366f1;
  border: none;
  width: 2rem;
  height: 2rem;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;

  &:hover {
    background: rgba(99, 102, 241, 0.1);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const DownloadButton = styled.button`
  position: absolute;
  top: 0.75rem;
  right: 1rem;
  padding: 0.5rem 1rem;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;

  &:hover {
    background: #4f46e5;
  }
`;

const ClearChatButton = styled.button`
  width: calc(100% - 2rem);
  margin: 0.5rem 1rem;
  padding: 0.5rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: background-color 0.2s;

  &:hover {
    background: #dc2626;
  }
`;

const LoadingState = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9ca3af;
`;

export default function ChatPage() {
  const { projectId } = useParams();
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [pdfFile, setPdfFile] = useState(null);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1);
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  useEffect(() => {
    // Load the PDF file for this project
    const loadProjectDocument = () => {
      try {
        const projectDocuments = JSON.parse(
          localStorage.getItem("projectDocuments") || "{}"
        );
        const documentData = projectDocuments[projectId];

        if (documentData) {
          // Convert base64 back to file
          const byteString = atob(documentData.data.split(",")[1]);
          const mimeString = documentData.data
            .split(",")[0]
            .split(":")[1]
            .split(";")[0];
          const ab = new ArrayBuffer(byteString.length);
          const ia = new Uint8Array(ab);

          for (let i = 0; i < byteString.length; i++) {
            ia[i] = byteString.charCodeAt(i);
          }

          const file = new File([ab], documentData.name, {
            type: mimeString,
            lastModified: documentData.lastModified,
          });

          setPdfFile(file);
        }
      } catch (error) {
        console.error("Error loading document:", error);
      }
    };

    loadProjectDocument();
  }, [projectId]);

  useEffect(() => {
    // Fetch documents list
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);

      // Get the project from localStorage to retrieve the fileId
      const projects = JSON.parse(localStorage.getItem("projects") || "[]");
      const currentProject = projects.find((p) => p.id === projectId);

      if (currentProject && currentProject.fileId) {
        // Find the document with the matching fileId
        const projectDoc = docs.find(
          (doc) => doc.file_id === currentProject.fileId
        );
        if (projectDoc) {
          setSelectedDocument(projectDoc);
        }
      } else if (docs.length > 0) {
        // If no fileId is found, select the first document
        setSelectedDocument(docs[0]);
      }
    } catch (error) {
      console.error("Error fetching documents:", error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    const newMessage = { role: "user", content: message };
    setMessages((prev) => [...prev, newMessage]);
    setMessage("");
    setIsLoading(true);

    try {
      // Create a session ID if it doesn't exist
      const sessionId =
        localStorage.getItem(`chat_session_${projectId}`) ||
        `session_${Date.now()}`;
      localStorage.setItem(`chat_session_${projectId}`, sessionId);

      // Use the selected model or default to gemini-2.0-flash
      const selectedModel =
        localStorage.getItem("selectedModel") || "gemini-2.0-flash";

      console.log("Sending message to API:", {
        message,
        sessionId,
        selectedModel,
      });
      const response = await sendChatMessage(message, sessionId, selectedModel);
      console.log("API response:", response);

      // The backend returns 'answer' in the response
      if (response && response.answer) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: response.answer },
        ]);
      } else {
        console.error("Unexpected response format:", response);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              "Received an unexpected response format. Please try again.",
          },
        ]);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${
            error.message || "Unknown error. Please try again."
          }`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
  };

  const changePage = (offset) => {
    setPageNumber((prevPageNumber) => prevPageNumber + offset);
  };

  const changeScale = (delta) => {
    setScale((prevScale) => Math.max(0.5, Math.min(2, prevScale + delta)));
  };

  // Function to download chat history as PDF
  const downloadChatHistoryAsPDF = async (chatHistory) => {
    const doc = new jsPDF();
    const chatContent = chatHistory
      .map((msg) => `${msg.role.toUpperCase()}: ${msg.content}\n\n`)
      .join("---\n\n");

    const canvas = await html2canvas(document.body);
    const imgData = canvas.toDataURL("image/png");

    doc.addImage(imgData, "PNG", 10, 10, 180, 160);
    doc.text(chatContent, 10, 180);
    doc.save("chat-history.pdf");
  };

  const clearChat = () => {
    setMessages([]);
  };

  const toggleDocumentDropdown = () => {
    setIsDropdownOpen((prev) => !prev);
  };

  const selectDocument = (doc) => {
    setSelectedDocument(doc);
    setIsDropdownOpen(false);
  };

  const handleDeleteDocument = async () => {
    if (!selectedDocument) return;

    try {
      await deleteDocument(selectedDocument.file_id);
      fetchDocuments();
    } catch (error) {
      console.error("Error deleting document:", error);
    }
  };

  return (
    <Container>
      <PDFSection>
        <PDFControls>
          <ControlsLeft>
            <DocumentSelector>
              <DocumentButton onClick={toggleDocumentDropdown}>
                {selectedDocument
                  ? selectedDocument.filename
                  : "Select Document"}{" "}
                <ChevronDown size={16} />
              </DocumentButton>
              <DropdownMenu isOpen={isDropdownOpen}>
                {documents.map((doc) => (
                  <DropdownItem
                    key={doc.file_id}
                    onClick={() => selectDocument(doc)}
                  >
                    {doc.filename}
                    <Trash2
                      size={16}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (window.confirm(`Delete ${doc.filename}?`)) {
                          handleDeleteDocument(doc.file_id);
                        }
                      }}
                    />
                  </DropdownItem>
                ))}
              </DropdownMenu>
            </DocumentSelector>
            <ControlButton
              onClick={() => changePage(-1)}
              disabled={pageNumber <= 1}
            >
              <ArrowLeft size={18} />
            </ControlButton>
            <ControlButton
              onClick={() => changePage(1)}
              disabled={pageNumber >= numPages}
            >
              <ArrowRight size={18} />
            </ControlButton>
          </ControlsLeft>
          <ControlsRight>
            <ControlButton onClick={() => changeScale(0.1)}>
              <ZoomIn size={18} />
            </ControlButton>
            <ControlButton onClick={() => changeScale(-0.1)}>
              <ZoomOut size={18} />
            </ControlButton>
            <ControlButton onClick={() => setScale(1)}>
              <RotateCcw size={18} />
            </ControlButton>
            <ControlButton onClick={() => downloadChatHistoryAsPDF(messages)}>
              <Download size={18} />
            </ControlButton>
          </ControlsRight>
        </PDFControls>

        <PDFViewer>
          {pdfFile ? (
            <Document
              file={pdfFile}
              onLoadSuccess={onDocumentLoadSuccess}
              loading={<LoadingState>Loading PDF...</LoadingState>}
            >
              <Page
                pageNumber={pageNumber}
                scale={scale}
                loading={<LoadingState>Loading page...</LoadingState>}
              />
            </Document>
          ) : (
            <LoadingState>No document uploaded for this project</LoadingState>
          )}
        </PDFViewer>
      </PDFSection>

      <ChatSection>
        <ChatHeader>Chat</ChatHeader>
        <DownloadButton onClick={() => downloadChatHistoryAsPDF(messages)}>
          <Download size={16} />
          Download Chat
        </DownloadButton>

        <ClearChatButton onClick={clearChat}>Clear Chat</ClearChatButton>

        <ChatMessages>
          {messages.map((msg, index) => (
            <MessageWrapper key={index}>
              <Avatar>{msg.role === "user" ? "U" : "AI"}</Avatar>
              <MessageContent>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {msg.content}
                </ReactMarkdown>
              </MessageContent>
            </MessageWrapper>
          ))}
          {isLoading && (
            <MessageWrapper>
              <LoadingAvatar>AI</LoadingAvatar>
              <MessageContent>Thinking...</MessageContent>
            </MessageWrapper>
          )}
        </ChatMessages>

        <ChatInput>
          <InputForm onSubmit={handleSendMessage}>
            <Input
              type="text"
              placeholder="Type your message..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              disabled={isLoading}
            />
            <SendButton type="submit" disabled={isLoading || !message.trim()}>
              <Send size={20} />
            </SendButton>
          </InputForm>
        </ChatInput>
      </ChatSection>
    </Container>
  );
}

import { useState, useEffect } from "react";
import styled from "styled-components";
import axios from "axios";
import { Link } from "react-router-dom";
import { FileText, Trash2, BarChart2 } from "react-feather";
import { listDocuments, deleteDocument, cleanupDocuments } from "../utils/api";

const Container = styled.div`
  padding: 2rem;
  color: #e0e0e0;
`;

const Title = styled.h1`
  font-size: 2.5rem;
  font-weight: bold;
  margin-bottom: 2rem;
  color: #e0e0e0;
`;

const DocumentsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
`;

const DocumentCard = styled.div`
  background: #2c2c2c;
  border-radius: 8px;
  padding: 1.5rem;
  color: #e0e0e0;
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }
`;

const DocumentTitle = styled.h3`
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const DocumentDate = styled.div`
  margin-top: 1rem;
  font-size: 0.875rem;
  color: #9ca3af;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-top: 1.5rem;
`;

const ActionButton = styled.button`
  background: #374151;
  color: #e0e0e0;
  border: none;
  padding: 0.5rem;
  border-radius: 0.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;

  &:hover {
    background: #4b5563;
  }
`;

const BreakdownButton = styled(Link)`
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  font-size: 0.875rem;
  transition: background-color 0.2s;

  &:hover {
    background: #2563eb;
  }
`;

const UploadContainer = styled.div`
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #2c2c2c;
  border-radius: 0.5rem;
`;

const UploadForm = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const ButtonsContainer = styled.div`
  display: flex;
  gap: 1rem;
  align-items: center;
`;

const CleanupButton = styled.button`
  background: #ef4444;
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 0.25rem;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;

  &:hover {
    background: #dc2626;
  }

  &:disabled {
    background: #6b7280;
    cursor: not-allowed;
  }
`;

const UploadInput = styled.input`
  background: #1e1e1e;
  border: 1px solid #4b5563;
  padding: 0.75rem;
  border-radius: 0.25rem;
  color: #e0e0e0;
  width: 100%;
`;

const UploadButton = styled.button`
  background: #10b981;
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 0.25rem;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
  align-self: flex-start;

  &:hover {
    background: #059669;
  }

  &:disabled {
    background: #6b7280;
    cursor: not-allowed;
  }
`;

const LoadingSpinner = styled.div`
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top: 3px solid #10b981;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
  margin: 0 auto;

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
`;

const ErrorMessage = styled.div`
  background-color: rgba(220, 38, 38, 0.1);
  color: #ef4444;
  padding: 0.75rem;
  border-radius: 0.25rem;
  margin-top: 1rem;
`;

const Documents = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [cleanupLoading, setCleanupLoading] = useState(false);
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const docs = await listDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error("Error fetching documents:", err);
      setError("Failed to load documents. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file to upload");
      return;
    }

    try {
      setUploadLoading(true);
      setError(null);

      const formData = new FormData();
      formData.append("file", file);

      await axios.post("http://localhost:8000/upload-doc", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setFile(null);
      fetchDocuments();
    } catch (err) {
      console.error("Error uploading document:", err);
      setError(
        err.response?.data?.message ||
          "Failed to upload document. Please try again."
      );
    } finally {
      setUploadLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this document?")) {
      return;
    }

    try {
      await deleteDocument(id);
      fetchDocuments();
    } catch (err) {
      console.error("Error deleting document:", err);
      setError("Failed to delete document. Please try again.");
    }
  };

  const handleCleanup = async () => {
    if (
      !window.confirm(
        "This will delete all documents except the most recent one. Are you sure?"
      )
    ) {
      return;
    }

    try {
      setCleanupLoading(true);
      setError(null);

      const response = await cleanupDocuments();

      console.log("Cleanup response:", response);

      // Show success message
      alert(
        `Cleanup successful! Kept document: ${response.kept_document}. Deleted ${response.deleted_count} documents.`
      );

      // Refresh the documents list
      fetchDocuments();
    } catch (err) {
      console.error("Error cleaning up documents:", err);
      setError(
        err.response?.data?.message ||
          "Failed to clean up documents. Please try again."
      );
    } finally {
      setCleanupLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <Container>
      <Title>Documents</Title>

      <UploadContainer>
        <h2>Upload New Document</h2>
        <UploadForm onSubmit={handleUpload}>
          <UploadInput
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            onChange={handleFileChange}
          />
          {error && <ErrorMessage>{error}</ErrorMessage>}
          <ButtonsContainer>
            <UploadButton type="submit" disabled={uploadLoading || !file}>
              {uploadLoading ? <LoadingSpinner /> : "Upload Document"}
            </UploadButton>
            <CleanupButton
              type="button"
              onClick={handleCleanup}
              disabled={cleanupLoading || documents.length <= 1}
            >
              {cleanupLoading ? <LoadingSpinner /> : "Clean Up Documents"}
            </CleanupButton>
          </ButtonsContainer>
        </UploadForm>
      </UploadContainer>

      {loading ? (
        <LoadingSpinner />
      ) : (
        <DocumentsGrid>
          {documents.map((doc) => (
            <DocumentCard key={doc.id}>
              <DocumentTitle>
                <FileText size={20} />
                {doc.filename}
              </DocumentTitle>
              <DocumentDate>
                Uploaded: {formatDate(doc.upload_timestamp)}
              </DocumentDate>
              <ActionButtons>
                <ActionButton onClick={() => handleDelete(doc.id)}>
                  <Trash2 size={18} />
                </ActionButton>
                <BreakdownButton to={`/document/breakdown/${doc.id}`}>
                  <BarChart2 size={18} />
                  Generate Breakdown
                </BreakdownButton>
              </ActionButtons>
            </DocumentCard>
          ))}
        </DocumentsGrid>
      )}
    </Container>
  );
};

export default Documents;

import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import styled from "styled-components";

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  background: white;
  min-height: 100vh;
`;

const Title = styled.h1`
  color: #2c3e50;
  margin-bottom: 2rem;
  text-align: center;
  font-weight: 600;
`;

const DocumentGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
`;

const DocumentCard = styled.div`
  background: #f8f9fa;
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 123, 255, 0.1);
    border-color: #007bff;
  }
`;

const DocumentName = styled.h3`
  color: #2c3e50;
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  word-break: break-word;
  font-weight: 600;
`;

const DocumentMeta = styled.div`
  color: #6c757d;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
`;

const Button = styled.button`
  background: ${props => props.danger ? '#dc3545' : '#007bff'};
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;

  &:hover {
    background: ${props => props.danger ? '#c82333' : '#0056b3'};
    transform: translateY(-1px);
  }

  &:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }
`;

const LoadingSpinner = styled.div`
  text-align: center;
  padding: 2rem;
  color: #6c757d;
`;

const ErrorMessage = styled.div`
  background: #f8d7da;
  color: #721c24;
  padding: 1rem;
  border-radius: 6px;
  margin: 1rem 0;
  border: 1px solid #f5c6cb;
`;

const SuccessMessage = styled.div`
  background: #d4edda;
  color: #155724;
  padding: 1rem;
  border-radius: 6px;
  margin: 1rem 0;
  border: 1px solid #c3e6cb;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem;
  color: #6c757d;

  h3 {
    color: #2c3e50;
    margin-bottom: 1rem;
  }
`;

const BackButton = styled(Link)`
  display: inline-block;
  background: #6c757d;
  color: white;
  text-decoration: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  margin-bottom: 2rem;
  transition: all 0.3s ease;

  &:hover {
    background: #545b62;
    transform: translateY(-1px);
  }
`;

const CleanupButton = styled.button`
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 2rem;
  margin-left: 1rem;
  transition: all 0.3s ease;

  &:hover {
    background: #c82333;
    transform: translateY(-1px);
  }

  &:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }
`;

const API_BASE_URL = "http://localhost:8000";

const Documents = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState("");
  const [deleting, setDeleting] = useState(null);
  const [cleaningUp, setCleaningUp] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/documents`);
      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.status}`);
      }
      const data = await response.json();
      setDocuments(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error("Error fetching documents:", err);
    } finally {
      setLoading(false);
    }
  };

  const deleteDocument = async (fileId, filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) {
      return;
    }

    try {
      setDeleting(fileId);
      const response = await fetch(`${API_BASE_URL}/delete-doc`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ file_id: fileId }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Failed to delete document");
      }

      setSuccess(`Document "${filename}" deleted successfully`);
      fetchDocuments();
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.message);
      console.error("Error deleting document:", err);
    } finally {
      setDeleting(null);
    }
  };

  const cleanupAllDocuments = async () => {
    if (!window.confirm("Are you sure you want to delete ALL documents? This cannot be undone.")) {
      return;
    }

    try {
      setCleaningUp(true);
      const response = await fetch(`${API_BASE_URL}/cleanup-documents`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Failed to cleanup documents");
      }

      setSuccess("All documents have been deleted successfully");
      fetchDocuments();
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.message);
      console.error("Error cleaning up documents:", err);
    } finally {
      setCleaningUp(false);
    }
  };

  if (loading) {
    return (
      <Container>
        <LoadingSpinner>Loading documents...</LoadingSpinner>
      </Container>
    );
  }

  return (
    <Container>
      <div>
        <BackButton to="/">← Back to Home</BackButton>
        <CleanupButton
          onClick={cleanupAllDocuments}
          disabled={cleaningUp || documents.length === 0}
        >
          {cleaningUp ? "Cleaning up..." : "Delete All Documents"}
        </CleanupButton>
      </div>

      <Title>Document Library</Title>

      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}

      {documents.length === 0 ? (
        <EmptyState>
          <h3>No documents found</h3>
          <p>Upload a document to get started.</p>
        </EmptyState>
      ) : (
        <DocumentGrid>
          {documents.map((doc) => (
            <DocumentCard key={doc.id}>
              <DocumentName>{doc.filename}</DocumentName>
              <DocumentMeta>
                Uploaded: {new Date(doc.upload_date).toLocaleDateString()}
                <br />
                ID: {doc.id}
              </DocumentMeta>
              <ButtonGroup>
                <Button
                  danger
                  onClick={() => deleteDocument(doc.id, doc.filename)}
                  disabled={deleting === doc.id}
                >
                  {deleting === doc.id ? "Deleting..." : "Delete"}
                </Button>
              </ButtonGroup>
            </DocumentCard>
          ))}
        </DocumentGrid>
      )}
    </Container>
  );
};

export default Documents;

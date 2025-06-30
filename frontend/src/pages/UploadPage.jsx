import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import styled from "styled-components";
import { uploadDocument } from "../utils/api";

const Container = styled.div`
  max-width: 600px;
  margin: 0 auto;
  padding: 2rem;
`;

const Title = styled.h1`
  color: #333;
  margin-bottom: 2rem;
  text-align: center;
`;

const UploadArea = styled.div`
  border: 2px dashed #ccc;
  border-radius: 12px;
  padding: 3rem 2rem;
  text-align: center;
  background: ${props => props.isDragOver ? '#f8f9fa' : 'white'};
  border-color: ${props => props.isDragOver ? '#007bff' : '#ccc'};
  transition: all 0.3s ease;
  cursor: pointer;

  &:hover {
    border-color: #007bff;
    background: #f8f9fa;
  }
`;

const UploadIcon = styled.div`
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #666;
`;

const UploadText = styled.p`
  color: #666;
  margin-bottom: 1rem;
  font-size: 1.1rem;
`;

const UploadSubtext = styled.p`
  color: #999;
  font-size: 0.9rem;
`;

const FileInput = styled.input`
  display: none;
`;

const SelectedFile = styled.div`
  background: #f8f9fa;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  padding: 1rem;
  margin: 1rem 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const FileName = styled.span`
  color: #333;
  font-weight: 500;
`;

const FileSize = styled.span`
  color: #666;
  font-size: 0.9rem;
`;

const RemoveButton = styled.button`
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  font-size: 0.8rem;

  &:hover {
    background: #c82333;
  }
`;

const UploadButton = styled.button`
  background: #007bff;
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  width: 100%;
  margin-top: 1rem;
  transition: background 0.3s ease;

  &:hover:not(:disabled) {
    background: #0056b3;
  }

  &:disabled {
    background: #ccc;
    cursor: not-allowed;
  }
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

const UploadPage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const navigate = useNavigate();

  const handleFileSelect = (file) => {
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError(null);
    } else {
      setError('Please select a PDF file.');
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    handleFileSelect(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploading(true);
      setError(null);
      setSuccess(null);

      const result = await uploadDocument(selectedFile);
      
      setSuccess(`Document "${selectedFile.name}" uploaded successfully!`);
      setSelectedFile(null);
      
      // Navigate to chat after successful upload
      setTimeout(() => {
        navigate('/chat');
      }, 1500);
      
    } catch (err) {
      setError(err.message || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setError(null);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Container>
      <Title>Upload Document</Title>
      
      <UploadArea
        isDragOver={isDragOver}
        onClick={() => document.getElementById('fileInput').click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <UploadIcon>📄</UploadIcon>
        <UploadText>
          Drag and drop a PDF file here, or click to select
        </UploadText>
        <UploadSubtext>
          Only PDF files are supported (max 50MB)
        </UploadSubtext>
      </UploadArea>

      <FileInput
        id="fileInput"
        type="file"
        accept=".pdf"
        onChange={handleFileChange}
      />

      {selectedFile && (
        <SelectedFile>
          <div>
            <FileName>{selectedFile.name}</FileName>
            <br />
            <FileSize>{formatFileSize(selectedFile.size)}</FileSize>
          </div>
          <RemoveButton onClick={removeFile}>Remove</RemoveButton>
        </SelectedFile>
      )}

      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}

      <UploadButton
        onClick={handleUpload}
        disabled={!selectedFile || uploading}
      >
        {uploading ? 'Uploading...' : 'Upload Document'}
      </UploadButton>
    </Container>
  );
};

export default UploadPage; 
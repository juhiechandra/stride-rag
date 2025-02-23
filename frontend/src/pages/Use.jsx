import styled from "styled-components";
import { useNavigate, useParams } from "react-router-dom";
import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { uploadDocument } from "../utils/api"; // Import upload function
import { CheckCircle } from "react-feather"; // Import success icon

const Container = styled.div`
  padding: 2rem;
  color: #e0e0e0;
  max-width: 800px;
  margin: 0 auto;
`;

const Section = styled.div`
  margin-bottom: 2rem;
`;

const UploadContainer = styled.div`
  margin-bottom: 2rem;
`;

const DropZone = styled.div`
  border: 2px dashed #a855f7;
  border-radius: 16px;
  padding: 3rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #2c2c2c;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
`;

const UploadButton = styled.button`
  background: #1e3a8a;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease;

  &:hover {
    background: #1e40af;
  }
`;

const Card = styled.div`
  background: #2c2c2c;
  padding: 1.5rem;
  border-radius: 0.5rem;
  margin-bottom: 2rem;
  color: #e0e0e0;
`;

const StartButton = styled.button`
  padding: 0.75rem 2rem;
  background: #7c3aed;
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 2rem 0;

  &:hover {
    background: #6d28d9;
  }
`;

const SuccessMessage = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #10b981; // Success green color
  margin-top: 1rem;
  padding: 0.75rem;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 0.5rem;

  svg {
    flex-shrink: 0;
  }
`;

const ViewButton = styled.button`
  background: #6366f1;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  margin-top: 1rem;
  transition: background-color 0.2s;

  &:hover {
    background: #4f46e5;
  }
`;

const Use = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [uploadError, setUploadError] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [pdfFile, setPdfFile] = useState(null);

  const onDrop = async (acceptedFiles) => {
    try {
      const file = acceptedFiles[0];
      setPdfFile(file);
      setIsUploading(true);
      setUploadError(null);
      setUploadSuccess(false);

      // Convert file to base64 for storage
      const reader = new FileReader();
      reader.onload = async () => {
        const base64Data = reader.result;

        const formData = new FormData();
        formData.append("file", file);

        const response = await uploadDocument(formData);

        if (response && response.file_id) {
          // Store the document with project ID
          const projectDocuments = JSON.parse(
            localStorage.getItem("projectDocuments") || "{}"
          );

          // Store both the file data and metadata
          projectDocuments[projectId] = {
            data: base64Data,
            name: file.name,
            type: file.type,
            lastModified: file.lastModified,
          };

          localStorage.setItem(
            "projectDocuments",
            JSON.stringify(projectDocuments)
          );
          localStorage.setItem("currentFileId", response.file_id);

          setUploadSuccess(true);
          setUploadError(null);
        } else {
          setUploadError("Failed to upload document. Please try again.");
          setUploadSuccess(false);
        }
      };

      reader.readAsDataURL(file);
    } catch (err) {
      console.error("Upload error:", err);
      setUploadError("Failed to upload document. Please try again.");
      setUploadSuccess(false);
    } finally {
      setIsUploading(false);
    }
  };

  const { getRootProps, getInputProps } = useDropzone({
    accept: { "application/pdf": [".pdf"] },
    onDrop: (files) => onDrop(files),
  });

  const handleViewChat = () => {
    navigate(`/project/${projectId}/chat`);
  };

  return (
    <Container>
      <Section>
        <h2>Welcome to the Document Analysis Tool</h2>
        <p>
          This tool helps you analyze documents for security vulnerabilities and
          risks.
        </p>
        {/* Add your how-to-use content here */}
        <br></br>
        <UploadContainer>
          <DropZone {...getRootProps()}>
            <input {...getInputProps()} />
            <UploadButton disabled={isUploading}>
              {isUploading ? "Uploading..." : "Upload PDF"}
            </UploadButton>
          </DropZone>
          {uploadError && <div style={{ color: "#ef4444" }}>{uploadError}</div>}
          {uploadSuccess && (
            <>
              <SuccessMessage>
                <CheckCircle size={20} />
                Document uploaded successfully!
              </SuccessMessage>
              <ViewButton onClick={handleViewChat}>View in Chat</ViewButton>
            </>
          )}
        </UploadContainer>
      </Section>

      <Card>
        <h3>Document Summary</h3>
        <p>
          {pdfFile
            ? "Here is a summary of your document: [Dummy Summary]"
            : "Please upload a document to see the summary."}
        </p>
      </Card>
    </Container>
  );
};

export default Use;

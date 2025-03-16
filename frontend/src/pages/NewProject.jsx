import styled from "styled-components";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadDocument } from "../utils/api";

const Container = styled.div`
  padding: 2rem;
  max-width: 800px;
  margin: 0 auto;
  color: #e0e0e0;
`;

const Title = styled.h1`
  font-size: 2rem;
  margin-bottom: 2rem;
`;

const Form = styled.form`
  background: #2c2c2c;
  padding: 2rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const Label = styled.label`
  font-size: 0.875rem;
  color: #9ca3af;
`;

const Input = styled.input`
  padding: 0.75rem;
  background: #1e1e1e;
  border: 1px solid #374151;
  border-radius: 6px;
  color: #e0e0e0;
  font-size: 1rem;

  &:focus {
    outline: none;
    border-color: #a855f7;
  }
`;

const TextArea = styled.textarea`
  padding: 0.75rem;
  background: #1e1e1e;
  border: 1px solid #374151;
  border-radius: 6px;
  color: #e0e0e0;
  font-size: 1rem;
  min-height: 100px;
  resize: vertical;

  &:focus {
    outline: none;
    border-color: #a855f7;
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
`;

const Button = styled.button`
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;

  ${(props) =>
    props.primary
      ? `
    background: #a855f7;
    color: white;
    border: none;

    &:hover {
      background: #9333ea;
    }
  `
      : `
    background: transparent;
    color: #e0e0e0;
    border: 1px solid #374151;

    &:hover {
      background: #374151;
    }
  `}
`;

const ErrorMessage = styled.div`
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 0.5rem;
`;

export default function NewProject() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    code: "",
    owner: "",
    summary: "",
  });
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Validate form
    if (
      !formData.name.trim() ||
      !formData.code.trim() ||
      !formData.owner.trim()
    ) {
      setError("Please fill in all required fields");
      return;
    }

    if (!file) {
      setError("Please select a document to upload");
      return;
    }

    try {
      setUploading(true);

      // Upload document to backend
      const formDataObj = new FormData();
      formDataObj.append("file", file);

      const uploadResponse = await uploadDocument(formDataObj);

      // Here you would typically make an API call to create the project
      // For now, we'll simulate it with localStorage
      const projects = JSON.parse(localStorage.getItem("projects") || "[]");
      const newProject = {
        id: Date.now().toString(),
        ...formData,
        fileId: uploadResponse.file_id, // Store the file ID from the backend
        created_at: new Date().toISOString(),
      };

      projects.push(newProject);
      localStorage.setItem("projects", JSON.stringify(projects));

      // Navigate to the new project
      navigate(`/project/${newProject.id}/how-to-use`);
    } catch (err) {
      setError("Failed to create project. Please try again.");
      console.error("Error creating project:", err);
    } finally {
      setUploading(false);
    }
  };

  const handleCancel = () => {
    navigate("/projects");
  };

  return (
    <Container>
      <Title>Create New Project</Title>
      <Form onSubmit={handleSubmit}>
        <FormGroup>
          <Label htmlFor="name">Project Name *</Label>
          <Input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Enter project name"
            required
          />
        </FormGroup>

        <FormGroup>
          <Label htmlFor="code">Project Code *</Label>
          <Input
            type="text"
            id="code"
            name="code"
            value={formData.code}
            onChange={handleChange}
            placeholder="e.g., PROJ-1"
            required
          />
        </FormGroup>

        <FormGroup>
          <Label htmlFor="owner">Project Owner *</Label>
          <Input
            type="text"
            id="owner"
            name="owner"
            value={formData.owner}
            onChange={handleChange}
            placeholder="Enter owner name"
            required
          />
        </FormGroup>

        <FormGroup>
          <Label htmlFor="summary">Project Summary</Label>
          <TextArea
            id="summary"
            name="summary"
            value={formData.summary}
            onChange={handleChange}
            placeholder="Enter project description or summary"
          />
        </FormGroup>

        <FormGroup>
          <Label htmlFor="document">Upload Document *</Label>
          <Input
            type="file"
            id="document"
            name="document"
            onChange={handleFileChange}
            accept=".pdf"
            required
          />
          <small style={{ color: "#9ca3af", marginTop: "0.25rem" }}>
            Only PDF files are supported
          </small>
        </FormGroup>

        {error && <ErrorMessage>{error}</ErrorMessage>}

        <ButtonGroup>
          <Button type="submit" primary disabled={uploading}>
            {uploading ? "Creating..." : "Create Project"}
          </Button>
          <Button type="button" onClick={handleCancel} disabled={uploading}>
            Cancel
          </Button>
        </ButtonGroup>
      </Form>
    </Container>
  );
}

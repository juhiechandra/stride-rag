import { useState, useEffect } from "react";
import styled from "styled-components";
import axios from "axios";
import { useParams, useNavigate } from "react-router-dom";

const Container = styled.div`
  padding: 2rem;
  color: #e0e0e0;
`;

const Title = styled.h1`
  font-size: 2.5rem;
  font-weight: bold;
  margin-bottom: 3rem;
  color: #e0e0e0;
`;

const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
`;

const LoadingDot = styled.div`
  width: 0.75rem;
  height: 0.75rem;
  background-color: #3b82f6;
  border-radius: 50%;
  margin: 0 0.5rem;
  animation: bounce 0.5s ease-in-out infinite;
  animation-delay: ${(props) => props.delay}s;

  @keyframes bounce {
    0%,
    100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(-10px);
    }
  }
`;

const Section = styled.div`
  margin-bottom: 3rem;
`;

const SectionTitle = styled.h2`
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: #3b82f6; // bright blue for section titles
`;

const ItemList = styled.ul`
  list-style-type: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
`;

const Item = styled.li`
  padding: 1rem 1.5rem;
  border-radius: 0.5rem;
  background-color: #2c2c2c;
  border: 1px solid #404040;
  transition: all 0.2s ease-in-out;

  &:hover {
    background-color: #363636;
    border-color: #4b4b4b;
    transform: translateX(4px);
  }
`;

const ErrorContainer = styled.div`
  padding: 2rem;
  background-color: rgba(220, 38, 38, 0.1);
  border: 1px solid rgba(220, 38, 38, 0.3);
  border-radius: 0.5rem;
  color: #ef4444;
  margin-bottom: 2rem;
`;

const ComponentItem = styled(Item)`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const ComponentName = styled.h3`
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0;
  color: #60a5fa;
`;

const ComponentDescription = styled.p`
  margin: 0.5rem 0;
  color: #d1d5db;
  line-height: 1.5;
`;

const FunctionsList = styled.ul`
  list-style-type: disc;
  padding-left: 1.5rem;
  margin: 0.5rem 0;
`;

const FunctionItem = styled.li`
  color: #9ca3af;
  margin-bottom: 0.25rem;
`;

const ApiItem = styled(Item)`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const ApiEndpoint = styled.div`
  font-family: monospace;
  font-size: 1.1rem;
  color: #10b981;
  background-color: rgba(16, 185, 129, 0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  display: inline-block;
`;

const ApiMethod = styled.span`
  font-weight: bold;
  color: #f59e0b;
  margin-left: 0.5rem;
`;

const ParameterTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin: 0.5rem 0;
  font-size: 0.9rem;
`;

const TableHead = styled.thead`
  background-color: #374151;
`;

const TableRow = styled.tr`
  &:nth-child(even) {
    background-color: #1f2937;
  }
`;

const TableHeader = styled.th`
  text-align: left;
  padding: 0.5rem;
  color: #d1d5db;
`;

const TableCell = styled.td`
  padding: 0.5rem;
  color: #9ca3af;
  border-top: 1px solid #4b5563;
`;

const ResponseSection = styled.div`
  margin-top: 0.5rem;
`;

const ResponseTitle = styled.h4`
  font-size: 1rem;
  font-weight: 600;
  margin: 0.5rem 0;
  color: #d1d5db;
`;

const ResponseCode = styled.pre`
  background-color: #1f2937;
  padding: 0.5rem;
  border-radius: 0.25rem;
  font-family: monospace;
  font-size: 0.9rem;
  color: #d1d5db;
  overflow-x: auto;
`;

const ErrorCodesList = styled.ul`
  list-style-type: none;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.5rem 0;
`;

const ErrorCode = styled.li`
  background-color: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-family: monospace;
  font-size: 0.9rem;
`;

const PiiItem = styled.li`
  background-color: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-family: monospace;
  font-size: 0.9rem;
  display: inline-block;
  margin-right: 0.5rem;
  margin-bottom: 0.5rem;
`;

const PiiList = styled.ul`
  list-style-type: none;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  margin: 0.5rem 0;
`;

const ComplianceList = styled.ul`
  list-style-type: none;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.5rem 0;
`;

const ComplianceItem = styled.li`
  background-color: rgba(16, 185, 129, 0.1);
  color: #10b981;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-family: monospace;
  font-size: 0.9rem;
`;

const BackButton = styled.button`
  background-color: #3b82f6;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  font-size: 1rem;
  cursor: pointer;
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background-color 0.2s;

  &:hover {
    background-color: #2563eb;
  }
`;

const Breakdown = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const { fileId: urlFileId } = useParams();
  const { projectId } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchBreakdown = async () => {
      try {
        setLoading(true);
        setError(null);

        // Get file ID from URL or localStorage based on context
        let id;

        if (urlFileId) {
          // If we have a fileId in the URL (direct breakdown page)
          id = parseInt(urlFileId);
        } else {
          // If we're in a project context, get the file ID from localStorage
          id = parseInt(localStorage.getItem("currentFileId"));
        }

        if (isNaN(id) || !id) {
          throw new Error("Invalid file ID");
        }

        console.log("Using file ID for breakdown:", id);

        // Call the API
        const response = await axios.post(
          "http://localhost:8000/document/analyze",
          {
            file_id: id,
            model: "gemini-2.0-flash", // Use the more capable model for better results
          }
        );

        setData(response.data);
      } catch (err) {
        console.error("Error fetching document breakdown:", err);
        setError(
          err.response?.data?.message ||
            err.message ||
            "An error occurred while analyzing the document"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchBreakdown();
  }, [urlFileId, projectId]);

  const handleBack = () => {
    // If we're in a project context, go back to the project page
    if (projectId) {
      navigate(`/project/${projectId}/how-to-use`);
    } else {
      // Otherwise, go back to the documents page
      navigate("/documents");
    }
  };

  if (loading) {
    return (
      <Container>
        <Title>Generating Breakdown</Title>
        <LoadingContainer>
          <LoadingDot delay={0} />
          <LoadingDot delay={0.2} />
          <LoadingDot delay={0.4} />
        </LoadingContainer>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <BackButton onClick={handleBack}>← Back to Documents</BackButton>
        <Title>Document Breakdown</Title>
        <ErrorContainer>
          <h3>Error</h3>
          <p>{error}</p>
        </ErrorContainer>
      </Container>
    );
  }

  return (
    <Container>
      <BackButton onClick={handleBack}>← Back to Documents</BackButton>
      <Title>Document Breakdown</Title>

      <Section>
        <SectionTitle>Major Components</SectionTitle>
        <ItemList>
          {data.major_components.map((component, index) => (
            <ComponentItem key={index}>
              <ComponentName>{component.name}</ComponentName>
              <ComponentDescription>
                {component.description}
              </ComponentDescription>
              <FunctionsList>
                {component.key_functions.map((func, idx) => (
                  <FunctionItem key={idx}>{func}</FunctionItem>
                ))}
              </FunctionsList>
            </ComponentItem>
          ))}
        </ItemList>
      </Section>

      <Section>
        <SectionTitle>Diagrams</SectionTitle>
        <ItemList>
          {data.diagrams.map((diagram, index) => (
            <ComponentItem key={index}>
              <ComponentName>{diagram.type}</ComponentName>
              <ComponentDescription>
                <strong>Purpose:</strong> {diagram.purpose}
              </ComponentDescription>
              <ComponentDescription>
                <strong>Relation to System:</strong>{" "}
                {diagram.relation_to_system}
              </ComponentDescription>
              <div>
                <strong>Key Elements:</strong>
                <FunctionsList>
                  {diagram.key_elements.map((element, idx) => (
                    <FunctionItem key={idx}>{element}</FunctionItem>
                  ))}
                </FunctionsList>
              </div>
            </ComponentItem>
          ))}
        </ItemList>
      </Section>

      <Section>
        <SectionTitle>API Contracts</SectionTitle>
        <ItemList>
          {data.api_contracts.map((contract, index) => (
            <ApiItem key={index}>
              <div>
                <ApiEndpoint>{contract.endpoint}</ApiEndpoint>
                <ApiMethod>{contract.method}</ApiMethod>
              </div>

              {contract.parameters.length > 0 && (
                <div>
                  <ResponseTitle>Parameters</ResponseTitle>
                  <ParameterTable>
                    <TableHead>
                      <TableRow>
                        <TableHeader>Name</TableHeader>
                        <TableHeader>Type</TableHeader>
                        <TableHeader>Description</TableHeader>
                      </TableRow>
                    </TableHead>
                    <tbody>
                      {contract.parameters.map((param, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{param.name}</TableCell>
                          <TableCell>{param.type}</TableCell>
                          <TableCell>{param.description}</TableCell>
                        </TableRow>
                      ))}
                    </tbody>
                  </ParameterTable>
                </div>
              )}

              <ResponseSection>
                <ResponseTitle>Success Response</ResponseTitle>
                <ResponseCode>{contract.success_response}</ResponseCode>
              </ResponseSection>

              {contract.error_codes.length > 0 && (
                <ResponseSection>
                  <ResponseTitle>Error Codes</ResponseTitle>
                  <ErrorCodesList>
                    {contract.error_codes.map((code, idx) => (
                      <ErrorCode key={idx}>{code}</ErrorCode>
                    ))}
                  </ErrorCodesList>
                </ResponseSection>
              )}
            </ApiItem>
          ))}
        </ItemList>
      </Section>

      <Section>
        <SectionTitle>PII Data / Sensitive Information</SectionTitle>
        <ComponentItem>
          <ResponseTitle>Identified Fields</ResponseTitle>
          <PiiList>
            {data.pii_data.identified_fields.map((field, idx) => (
              <PiiItem key={idx}>{field}</PiiItem>
            ))}
          </PiiList>

          <ResponseTitle>Handling Procedures</ResponseTitle>
          <ComponentDescription>
            {data.pii_data.handling_procedures}
          </ComponentDescription>

          <ResponseTitle>Compliance Standards</ResponseTitle>
          <ComplianceList>
            {data.pii_data.compliance_standards.map((standard, idx) => (
              <ComplianceItem key={idx}>{standard}</ComplianceItem>
            ))}
          </ComplianceList>
        </ComponentItem>
      </Section>
    </Container>
  );
};

export default Breakdown;

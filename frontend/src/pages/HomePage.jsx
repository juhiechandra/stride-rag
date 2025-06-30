import React from "react";
import { Link } from "react-router-dom";
import styled from "styled-components";

const Container = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
`;

const Title = styled.h1`
  color: #333;
  font-size: 3rem;
  margin-bottom: 1rem;
`;

const Subtitle = styled.p`
  color: #666;
  font-size: 1.2rem;
  margin-bottom: 3rem;
  line-height: 1.6;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
`;

const ActionButton = styled(Link)`
  display: inline-block;
  padding: 1rem 2rem;
  background: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 500;
  transition: background 0.3s ease;

  &:hover {
    background: #0056b3;
  }
`;

const SecondaryButton = styled(Link)`
  display: inline-block;
  padding: 1rem 2rem;
  background: #6c757d;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 500;
  transition: background 0.3s ease;

  &:hover {
    background: #545b62;
  }
`;

const FeatureSection = styled.div`
  margin-top: 4rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
`;

const FeatureCard = styled.div`
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: 1px solid #e1e5e9;
`;

const FeatureTitle = styled.h3`
  color: #333;
  margin-bottom: 1rem;
`;

const FeatureDescription = styled.p`
  color: #666;
  line-height: 1.5;
`;

const HomePage = () => {
  return (
    <Container>
      <Title>Simple RAG Chatbot</Title>
      <Subtitle>
        Upload PDF documents and ask questions about their content using advanced AI.
        Powered by Gemini 2.5 Flash with text and image capabilities.
      </Subtitle>
      
      <ButtonGroup>
        <ActionButton to="/upload">Upload Document</ActionButton>
        <SecondaryButton to="/chat">Start Chat</SecondaryButton>
        <SecondaryButton to="/documents">View Documents</SecondaryButton>
      </ButtonGroup>

      <FeatureSection>
        <FeatureCard>
          <FeatureTitle>📄 Document Upload</FeatureTitle>
          <FeatureDescription>
            Upload PDF documents and automatically extract text and images for analysis.
          </FeatureDescription>
        </FeatureCard>
        
        <FeatureCard>
          <FeatureTitle>💬 Smart Chat</FeatureTitle>
          <FeatureDescription>
            Ask questions about your documents and get intelligent answers with source citations.
          </FeatureDescription>
        </FeatureCard>
        
        <FeatureCard>
          <FeatureTitle>🔍 Vector Search</FeatureTitle>
          <FeatureDescription>
            Advanced semantic search finds relevant content even when exact keywords don't match.
          </FeatureDescription>
        </FeatureCard>
        
        <FeatureCard>
          <FeatureTitle>🖼️ Image Analysis</FeatureTitle>
          <FeatureDescription>
            Gemini 2.5 Flash analyzes images from PDFs including charts, diagrams, and text.
          </FeatureDescription>
        </FeatureCard>
      </FeatureSection>
    </Container>
  );
};

export default HomePage; 
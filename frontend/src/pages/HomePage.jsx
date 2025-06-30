import React from "react";
import { Link } from "react-router-dom";
import styled from "styled-components";

const Container = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
  background: white;
  min-height: 100vh;
`;

const Title = styled.h1`
  color: #2c3e50;
  font-size: 2.5rem;
  margin-bottom: 1rem;
  font-weight: 600;
`;

const Subtitle = styled.p`
  color: #6c757d;
  font-size: 1.1rem;
  margin-bottom: 3rem;
  line-height: 1.6;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 4rem;
`;

const ActionButton = styled(Link)`
  display: inline-block;
  padding: 1rem 2rem;
  background: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  border: 2px solid #007bff;

  &:hover {
    background: #0056b3;
    border-color: #0056b3;
    transform: translateY(-2px);
  }
`;

const SecondaryButton = styled(Link)`
  display: inline-block;
  padding: 1rem 2rem;
  background: transparent;
  color: #007bff;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 500;
  border: 2px solid #007bff;
  transition: all 0.3s ease;

  &:hover {
    background: #007bff;
    color: white;
    transform: translateY(-2px);
  }
`;

const FeatureSection = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
`;

const FeatureCard = styled.div`
  background: #f8f9fa;
  padding: 2rem;
  border-radius: 12px;
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 123, 255, 0.1);
    border-color: #007bff;
  }
`;

const FeatureTitle = styled.h3`
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1.2rem;
  font-weight: 600;
`;

const FeatureDescription = styled.p`
  color: #6c757d;
  line-height: 1.5;
  margin: 0;
`;

const HomePage = () => {
  return (
    <Container>
      <Title>RAG Document Assistant</Title>
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
          <FeatureTitle>Document Upload</FeatureTitle>
          <FeatureDescription>
            Upload PDF documents and automatically extract text and images for analysis.
          </FeatureDescription>
        </FeatureCard>
        
        <FeatureCard>
          <FeatureTitle>Smart Chat</FeatureTitle>
          <FeatureDescription>
            Ask questions about your documents and get intelligent answers with source citations.
          </FeatureDescription>
        </FeatureCard>
        
        <FeatureCard>
          <FeatureTitle>Vector Search</FeatureTitle>
          <FeatureDescription>
            Advanced semantic search finds relevant content even when exact keywords don't match.
          </FeatureDescription>
        </FeatureCard>
        
        <FeatureCard>
          <FeatureTitle>Image Analysis</FeatureTitle>
          <FeatureDescription>
            Gemini 2.5 Flash analyzes images from PDFs including charts, diagrams, and text.
          </FeatureDescription>
        </FeatureCard>
      </FeatureSection>
    </Container>
  );
};

export default HomePage; 
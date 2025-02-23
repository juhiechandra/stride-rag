import React, { useState, useEffect } from "react";
import styled from "styled-components";

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

const Breakdown = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setData({
        majorComponents: [
          "Authentication Service",
          "Document Processing Engine",
          "Security Analysis Module",
          "Report Generation System",
        ],
        diagrams: [
          "System Architecture Diagram",
          "Data Flow Diagram",
          "Component Interaction Diagram",
        ],
        apiContracts: [
          "/api/v1/document/upload - POST",
          "/api/v1/analysis/security - GET",
          "/api/v1/report/generate - POST",
          "/api/v1/report/{id} - GET",
        ],
      });
      setLoading(false);
    }, 2000); // 2 seconds delay to simulate loading
  }, []);

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

  return (
    <Container>
      <Title>Document Breakdown</Title>

      <Section>
        <SectionTitle>Major Components</SectionTitle>
        <ItemList>
          {data.majorComponents.map((component, index) => (
            <Item key={index}>{component}</Item>
          ))}
        </ItemList>
      </Section>

      <Section>
        <SectionTitle>Diagrams</SectionTitle>
        <ItemList>
          {data.diagrams.map((diagram, index) => (
            <Item key={index}>{diagram}</Item>
          ))}
        </ItemList>
      </Section>

      <Section>
        <SectionTitle>API Contracts</SectionTitle>
        <ItemList>
          {data.apiContracts.map((contract, index) => (
            <Item key={index}>{contract}</Item>
          ))}
        </ItemList>
      </Section>
    </Container>
  );
};

export default Breakdown;

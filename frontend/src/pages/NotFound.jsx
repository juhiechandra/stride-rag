import React from "react";
import { Link } from "react-router-dom";
import styled from "styled-components";

const Container = styled.div`
  max-width: 600px;
  margin: 0 auto;
  padding: 4rem 2rem;
  text-align: center;
`;

const ErrorCode = styled.h1`
  font-size: 6rem;
  color: #dc3545;
  margin: 0;
  font-weight: bold;
`;

const Title = styled.h2`
  color: #333;
  margin: 1rem 0;
  font-size: 2rem;
`;

const Description = styled.p`
  color: #666;
  font-size: 1.1rem;
  margin-bottom: 2rem;
  line-height: 1.6;
`;

const HomeButton = styled(Link)`
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

const NotFound = () => {
  return (
    <Container>
      <ErrorCode>404</ErrorCode>
      <Title>Page Not Found</Title>
      <Description>
        Oops! The page you're looking for doesn't exist. 
        It might have been moved, deleted, or you entered the wrong URL.
      </Description>
      <HomeButton to="/">Go Back Home</HomeButton>
    </Container>
  );
};

export default NotFound; 
import styled from "styled-components";

const Container = styled.div`
  padding: 2rem;
  color: #e0e0e0;
`;

const Title = styled.h1`
  font-size: 2rem;
  margin-bottom: 2rem;
`;

export default function AttackTree() {
  return (
    <Container>
      <Title>Attack Tree Analysis</Title>
      {/* Add attack tree content here */}
    </Container>
  );
}

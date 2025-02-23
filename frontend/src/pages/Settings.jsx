import styled from "styled-components";

const SettingsContainer = styled.div`
  padding: 2rem;
  color: #e0e0e0;
`;

const Title = styled.h1`
  font-size: 2rem;
  margin-bottom: 2rem;
`;

export default function Settings() {
  return (
    <SettingsContainer>
      <Title>Settings</Title>
      {/* Add settings content here */}
    </SettingsContainer>
  );
}

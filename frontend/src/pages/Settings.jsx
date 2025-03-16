import styled from "styled-components";
import { useState, useEffect } from "react";

const SettingsContainer = styled.div`
  padding: 2rem;
  color: #e0e0e0;
`;

const Title = styled.h1`
  font-size: 2rem;
  margin-bottom: 2rem;
`;

const Section = styled.div`
  margin-bottom: 2rem;
`;

const SectionTitle = styled.h2`
  font-size: 1.5rem;
  margin-bottom: 1rem;
`;

const ModelSelector = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const RadioGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const RadioOption = styled.label`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
`;

const SaveButton = styled.button`
  background-color: #4f46e5;
  color: white;
  border: none;
  border-radius: 0.25rem;
  padding: 0.5rem 1rem;
  font-size: 1rem;
  cursor: pointer;
  margin-top: 1rem;

  &:hover {
    background-color: #4338ca;
  }

  &:disabled {
    background-color: #6b7280;
    cursor: not-allowed;
  }
`;

const StatusMessage = styled.div`
  margin-top: 1rem;
  color: ${(props) => (props.isError ? "#ef4444" : "#10b981")};
`;

export default function Settings() {
  const [selectedModel, setSelectedModel] = useState("");
  const [status, setStatus] = useState({ message: "", isError: false });

  useEffect(() => {
    // Load the currently selected model from localStorage
    const savedModel =
      localStorage.getItem("selectedModel") || "gemini-2.0-flash";
    setSelectedModel(savedModel);
  }, []);

  const handleModelChange = (e) => {
    setSelectedModel(e.target.value);
  };

  const saveSettings = () => {
    try {
      localStorage.setItem("selectedModel", selectedModel);
      setStatus({
        message: "Settings saved successfully!",
        isError: false,
      });

      // Clear status message after 3 seconds
      setTimeout(() => {
        setStatus({ message: "", isError: false });
      }, 3000);
    } catch (error) {
      setStatus({
        message: `Error saving settings: ${error.message}`,
        isError: true,
      });
    }
  };

  return (
    <SettingsContainer>
      <Title>Settings</Title>

      <Section>
        <SectionTitle>Model Selection</SectionTitle>
        <ModelSelector>
          <p>Select the AI model to use for chat interactions:</p>

          <RadioGroup>
            <RadioOption>
              <input
                type="radio"
                id="gemini-2.0-flash"
                name="model"
                value="gemini-2.0-flash"
                checked={selectedModel === "gemini-2.0-flash"}
                onChange={handleModelChange}
              />
              <span>Gemini 2.0 Flash (Recommended)</span>
            </RadioOption>

            <RadioOption>
              <input
                type="radio"
                id="gemini-2.0-flash"
                name="model"
                value="gemini-2.0-flash"
                checked={selectedModel === "gemini-2.0-flash"}
                onChange={handleModelChange}
              />
              <span>Gemini 2.0 Pro</span>
            </RadioOption>
          </RadioGroup>

          <SaveButton onClick={saveSettings}>Save Settings</SaveButton>

          {status.message && (
            <StatusMessage isError={status.isError}>
              {status.message}
            </StatusMessage>
          )}
        </ModelSelector>
      </Section>
    </SettingsContainer>
  );
}

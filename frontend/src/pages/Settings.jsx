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

const SettingSection = styled.div`
  margin-bottom: 2rem;
`;

const SectionTitle = styled.h2`
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: #a855f7;
`;

const SelectWrapper = styled.div`
  margin-bottom: 1rem;
`;

const Label = styled.label`
  display: block;
  margin-bottom: 0.5rem;
`;

const Select = styled.select`
  background: #2c2c2c;
  color: #e0e0e0;
  padding: 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid #374151;
  width: 300px;
  font-size: 1rem;
`;

const SaveButton = styled.button`
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

const SuccessMessage = styled.div`
  color: #10b981;
  margin-top: 1rem;
  padding: 0.5rem;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 0.5rem;
  display: ${(props) => (props.visible ? "block" : "none")};
`;

export default function Settings() {
  const [selectedModel, setSelectedModel] = useState("gemini-2.0-flash");
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    // Load saved model preference
    const savedModel = localStorage.getItem("selectedModel");
    if (savedModel) {
      setSelectedModel(savedModel);
    }
  }, []);

  const handleModelChange = (e) => {
    setSelectedModel(e.target.value);
  };

  const saveSettings = () => {
    localStorage.setItem("selectedModel", selectedModel);
    setSaveSuccess(true);

    // Hide success message after 3 seconds
    setTimeout(() => {
      setSaveSuccess(false);
    }, 3000);
  };

  return (
    <SettingsContainer>
      <Title>Settings</Title>

      <SettingSection>
        <SectionTitle>AI Model Settings</SectionTitle>
        <SelectWrapper>
          <Label htmlFor="model-select">Default AI Model:</Label>
          <Select
            id="model-select"
            value={selectedModel}
            onChange={handleModelChange}
          >
            <option value="gemini-2.0-flash">Gemini 2.0 Flash (Faster)</option>
            <option value="gemini-2.0-pro">
              Gemini 2.0 Pro (More powerful)
            </option>
          </Select>
        </SelectWrapper>

        <SaveButton onClick={saveSettings}>Save Settings</SaveButton>
        <SuccessMessage visible={saveSuccess}>
          Settings saved successfully!
        </SuccessMessage>
      </SettingSection>
    </SettingsContainer>
  );
}

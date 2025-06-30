import React from "react";
import styled from "styled-components";
import { useState } from "react";
import {
  Link,
  Routes,
  Route,
  useNavigate,
  Navigate,
} from "react-router-dom";
import { ArrowLeft } from "react-feather";
import ChatPage from "./ChatPage";
import UploadPage from "./UploadPage";

const PageContainer = styled.div`
  display: flex;
  min-height: 100vh;
  background: #f5f5f5;
`;

const Sidebar = styled.div`
  width: 280px;
  background: white;
  border-right: 1px solid #e1e5e9;
  padding: 1rem;
  box-shadow: 2px 0 4px rgba(0, 0, 0, 0.1);
`;

const MainContent = styled.div`
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
`;

const MenuList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0;
`;

const MenuItem = styled.li`
  margin-bottom: 0.5rem;
`;

const MenuLink = styled(Link)`
  display: block;
  padding: 0.75rem 1rem;
  color: #333;
  text-decoration: none;
  border-radius: 0.5rem;
  transition: background-color 0.2s;

  &:hover {
    background: #f0f0f0;
  }

  &.active {
    background: #007bff;
    color: white;
  }
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 2rem;
  padding: 0 1rem;
`;

const BackButton = styled.button`
  background: none;
  border: none;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 0.5rem;
  margin-right: 1rem;

  &:hover {
    background: #f0f0f0;
  }
`;

const Title = styled.h2`
  color: #333;
  margin: 0;
`;

export default function DocumentPage() {
  const [activeItem, setActiveItem] = useState("upload");
  const navigate = useNavigate();

  const handleBack = () => {
    navigate("/");
  };

  return (
    <PageContainer>
      <Sidebar>
        <Header>
          <BackButton onClick={handleBack}>
            <ArrowLeft size={20} />
            Back to Home
          </BackButton>
        </Header>
        <Title>RAG System</Title>
        <MenuList>
          <MenuItem>
            <MenuLink
              to="/document/upload"
              className={activeItem === "upload" ? "active" : ""}
              onClick={() => setActiveItem("upload")}
            >
              Upload Document
            </MenuLink>
          </MenuItem>
          <MenuItem>
            <MenuLink
              to="/document/chat"
              className={activeItem === "chat" ? "active" : ""}
              onClick={() => setActiveItem("chat")}
            >
              Chat with Documents
            </MenuLink>
          </MenuItem>
        </MenuList>
      </Sidebar>
      <MainContent>
        <Routes>
          <Route path="upload" element={<UploadPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="*" element={<Navigate to="upload" replace />} />
        </Routes>
      </MainContent>
    </PageContainer>
  );
}

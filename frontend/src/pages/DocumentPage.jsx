import styled from "styled-components";
import { useState } from "react";
import {
  Link,
  Routes,
  Route,
  useNavigate,
  useParams,
  Navigate,
} from "react-router-dom";
import { ArrowLeft } from "react-feather";
import ChatPage from "./ChatPage";
import Use from "./Use";
import Breakdown from "./Breakdown";
import Stride from "./Stride";
import AttackTree from "./AttackTree";
import TrustBoundaries from "./TrustBoundaries";
import DataFlowDiagrams from "./DataFlowDiagrams";

const PageContainer = styled.div`
  display: flex;
  min-height: 100vh;
  background: #1e1e1e;
`;

const ProjectSidebar = styled.div`
  width: 280px;
  background: #2c2c2c;
  border-right: 1px solid #374151;
  padding: 1rem;
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
  color: #e0e0e0;
  text-decoration: none;
  border-radius: 0.5rem;
  transition: background-color 0.2s;

  &:hover {
    background: #3b3b3b;
  }

  &.active {
    background: #4b4b4b;
    color: #a855f7;
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
  color: #e0e0e0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 0.5rem;
  margin-right: 1rem;

  &:hover {
    background: #3b3b3b;
  }
`;

export default function DocumentPage() {
  const [activeItem, setActiveItem] = useState("how-to-use");
  const navigate = useNavigate();
  const { projectId } = useParams();

  const handleBack = () => {
    navigate("/projects");
  };

  return (
    <PageContainer>
      <ProjectSidebar>
        <Header>
          <BackButton onClick={handleBack}>
            <ArrowLeft size={20} />
            Back to Projects
          </BackButton>
        </Header>
        <MenuList>
          <MenuItem>
            <MenuLink
              to={`/project/${projectId}/how-to-use`}
              className={activeItem === "how-to-use" ? "active" : ""}
              onClick={() => setActiveItem("how-to-use")}
            >
              Upload Document
            </MenuLink>
          </MenuItem>
          <MenuItem>
            <MenuLink
              to={`/project/${projectId}/chat`}
              className={activeItem === "chat" ? "active" : ""}
              onClick={() => setActiveItem("chat")}
            >
              Chat Section
            </MenuLink>
          </MenuItem>
          <MenuItem>
            <MenuLink
              to={`/project/${projectId}/components`}
              className={activeItem === "components" ? "active" : ""}
              onClick={() => setActiveItem("components")}
            >
              List of Components
            </MenuLink>
          </MenuItem>
          <MenuItem>
            <MenuLink
              to={`/project/${projectId}/stride`}
              className={activeItem === "stride" ? "active" : ""}
              onClick={() => setActiveItem("stride")}
            >
              Generate - STRIDE
            </MenuLink>
          </MenuItem>
          <MenuItem>
            <MenuLink
              to={`/project/${projectId}/attack-tree`}
              className={activeItem === "attack-tree" ? "active" : ""}
              onClick={() => setActiveItem("attack-tree")}
            >
              Attack Tree
            </MenuLink>
          </MenuItem>
          <MenuItem>
            <MenuLink
              to={`/project/${projectId}/trust-boundaries`}
              className={activeItem === "trust-boundaries" ? "active" : ""}
              onClick={() => setActiveItem("trust-boundaries")}
            >
              Trust Boundaries
            </MenuLink>
          </MenuItem>
          <MenuItem>
            <MenuLink
              to={`/project/${projectId}/data-flow-diagrams`}
              className={activeItem === "data-flow-diagrams" ? "active" : ""}
              onClick={() => setActiveItem("data-flow-diagrams")}
            >
              Data Flow Diagrams
            </MenuLink>
          </MenuItem>
        </MenuList>
      </ProjectSidebar>
      <MainContent>
        <Routes>
          <Route path="how-to-use" element={<Use />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="components" element={<Breakdown />} />
          <Route path="stride" element={<Stride />} />
          <Route path="attack-tree" element={<AttackTree />} />
          <Route path="trust-boundaries" element={<TrustBoundaries />} />
          <Route path="data-flow-diagrams" element={<DataFlowDiagrams />} />
          <Route path="*" element={<Navigate to="how-to-use" replace />} />
        </Routes>
      </MainContent>
    </PageContainer>
  );
}

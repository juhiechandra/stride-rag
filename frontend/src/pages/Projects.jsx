import styled from "styled-components";
import { Link } from "react-router-dom";
import { useState, useEffect } from "react";

const ProjectsContainer = styled.div`
  padding: 2rem;
`;

const ProjectsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
`;

const ProjectCard = styled(Link)`
  background: #2c2c2c;
  border-radius: 8px;
  padding: 1.5rem;
  text-decoration: none;
  color: #e0e0e0;
  transition: transform 0.2s, box-shadow 0.2s;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }
`;

const ProjectTitle = styled.h3`
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
`;

const ProjectCode = styled.span`
  color: #a855f7;
  font-size: 0.875rem;
`;

const ProjectOwner = styled.div`
  margin-top: 1rem;
  font-size: 0.875rem;
  color: #9ca3af;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
`;

const NewProjectButton = styled(Link)`
  background: #a855f7;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 500;
  transition: background-color 0.2s;

  &:hover {
    background: #9333ea;
  }
`;

export default function Projects() {
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    // Load projects from localStorage
    const savedProjects = JSON.parse(localStorage.getItem("projects") || "[]");
    setProjects([
      {
        id: "default",
        title: "Default Project",
        code: "DPROJ",
        owner: "Juhie Chandra",
      },
      ...savedProjects,
    ]);
  }, []);

  return (
    <ProjectsContainer>
      <Header>
        <h1>Projects</h1>
        <NewProjectButton to="/new-project">New Project +</NewProjectButton>
      </Header>

      <ProjectsGrid>
        {projects.map((project) => (
          <ProjectCard key={project.id} to={`/project/${project.id}`}>
            <ProjectTitle>{project.title || project.name}</ProjectTitle>
            <ProjectCode>({project.code})</ProjectCode>
            <ProjectOwner>
              <span>{project.owner}</span>
            </ProjectOwner>
          </ProjectCard>
        ))}
      </ProjectsGrid>
    </ProjectsContainer>
  );
}

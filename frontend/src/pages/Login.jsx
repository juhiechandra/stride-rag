import styled from "styled-components";
import { Container, Card, Button, Input } from "../components/styled/common";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

const LoginContainer = styled(Container)`
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #1e1e1e;
`;

const LoginCard = styled(Card)`
  width: 100%;
  max-width: 400px;
  background: #2c2c2c;
  padding: 2rem;
  border-radius: 8px;
`;

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 2rem;
  text-align: center;
  color: #e0e0e0;
`;

const Label = styled.label`
  display: block;
  margin-bottom: 0.5rem;
  color: #9ca3af;
`;

const FormGroup = styled.div`
  margin-bottom: 1.5rem;
`;

export default function Login() {
  const navigate = useNavigate();
  const [credentials, setCredentials] = useState({
    username: "",
    password: "",
  });

  const handleLogin = (e) => {
    e.preventDefault();
    // Add your authentication logic here
    localStorage.setItem("isAuthenticated", "true");
    navigate("/projects");
  };

  return (
    <LoginContainer>
      <LoginCard>
        <Title>Welcome back</Title>
        <form onSubmit={handleLogin}>
          <FormGroup>
            <Label>Username</Label>
            <Input
              type="text"
              value={credentials.username}
              onChange={(e) =>
                setCredentials({ ...credentials, username: e.target.value })
              }
              required
            />
          </FormGroup>
          <FormGroup>
            <Label>Password</Label>
            <Input
              type="password"
              value={credentials.password}
              onChange={(e) =>
                setCredentials({ ...credentials, password: e.target.value })
              }
              required
            />
          </FormGroup>
          <Button type="submit" fullWidth>
            Sign in
          </Button>
        </form>
      </LoginCard>
    </LoginContainer>
  );
}

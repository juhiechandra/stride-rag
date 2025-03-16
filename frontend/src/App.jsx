import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "styled-components";
import { MantineProvider } from "@mantine/core";
import { theme } from "./styles/theme";
import AppLayout from "./components/Layout/AppLayout";
import Projects from "./pages/Projects";
import DocumentPage from "./pages/DocumentPage";
import Settings from "./pages/Settings.jsx";
import Login from "./pages/Login";
import NewProject from "./pages/NewProject";
import Breakdown from "./pages/Breakdown";
import Documents from "./pages/Documents";
import ProtectedRoute from "./components/ProtectedRoute.jsx";

function App() {
  return (
    <ThemeProvider theme={theme}>
      <MantineProvider withGlobalStyles withNormalizeCSS>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<Login />} />

            {/* Protected Routes */}
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/projects" element={<Projects />} />
                <Route path="/new-project" element={<NewProject />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/documents" element={<Documents />} />
                <Route
                  path="/document/breakdown/:fileId"
                  element={<Breakdown />}
                />
                <Route
                  path="/project/:projectId/*"
                  element={<DocumentPage />}
                />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </MantineProvider>
    </ThemeProvider>
  );
}

export default App;

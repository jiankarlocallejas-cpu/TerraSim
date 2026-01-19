import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';
import { useAuth } from './contexts/AuthContext';
import Layout from './components/Layout/Layout';
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import Dashboard from './pages/Dashboard/Dashboard';
import Projects from './pages/Projects/Projects';
import ProjectDetail from './pages/Projects/ProjectDetail';
import DataUpload from './pages/Data/DataUpload';
import DataManagement from './pages/Data/DataManagement';
import Analysis from './pages/Analysis/Analysis';
import AnalysisDetail from './pages/Analysis/AnalysisDetail';
import Models from './pages/Models/Models';
import ModelDetail from './pages/Models/ModelDetail';
import Jobs from './pages/Jobs/Jobs';
import JobDetail from './pages/Jobs/JobDetail';
import Settings from './pages/Settings/Settings';
import NotFound from './pages/NotFound/NotFound';

function App() {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading screen while checking authentication
  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="100vh"
      >
        <div className="loading-spinner">
          <div style={{ width: 40, height: 40, border: '4px solid #f3f3f3', borderTop: '4px solid #1976d2', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
        </div>
      </Box>
    );
  }

  // Public routes (accessible without authentication)
  const publicRoutes = (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );

  // Protected routes (require authentication)
  const protectedRoutes = (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/projects/:id" element={<ProjectDetail />} />
        <Route path="/data/upload" element={<DataUpload />} />
        <Route path="/data/management" element={<DataManagement />} />
        <Route path="/analysis" element={<Analysis />} />
        <Route path="/analysis/:id" element={<AnalysisDetail />} />
        <Route path="/models" element={<Models />} />
        <Route path="/models/:id" element={<ModelDetail />} />
        <Route path="/jobs" element={<Jobs />} />
        <Route path="/jobs/:id" element={<JobDetail />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/404" element={<NotFound />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Routes>
    </Layout>
  );

  return (
    <Box height="100vh" display="flex" flexDirection="column">
      {isAuthenticated ? protectedRoutes : publicRoutes}
    </Box>
  );
}

export default App;

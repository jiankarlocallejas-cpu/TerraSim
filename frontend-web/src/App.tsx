import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { MainLayout } from './components/Layout/MainLayout'
import { Dashboard } from './pages/Dashboard'
import { AnalysisEditor } from './pages/AnalysisEditor'
import { ResultsPage } from './pages/ResultsPage'
import { ProjectManager } from './pages/ProjectManager'
import { Settings } from './pages/Settings'

export function App() {
  return (
    <Router>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analysis" element={<AnalysisEditor />} />
          <Route path="/results/:id" element={<ResultsPage />} />
          <Route path="/projects" element={<ProjectManager />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  )
}

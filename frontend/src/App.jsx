import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import LoadingSpinner from './components/LoadingSpinner'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import JobList from './pages/JobList'
import JobCreate from './pages/JobCreate'
import JobDetail from './pages/JobDetail'
import CandidateList from './pages/CandidateList'
import CandidateCreate from './pages/CandidateCreate'
import CandidateDetail from './pages/CandidateDetail'
import MatchResults from './pages/MatchResults'
import CandidateCompare from './pages/CandidateCompare'
import ExplanationDetail from './pages/ExplanationDetail'
import FairnessDashboard from './pages/FairnessDashboard'
import TaskList from './pages/TaskList'
import TaskCreate from './pages/TaskCreate'
import TaskDetail from './pages/TaskDetail'
import CreateUser from './pages/CreateUser'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <LoadingSpinner size="lg" className="min-h-screen" />
  if (!user) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

function AppRoutes() {
  const { user, loading } = useAuth()
  if (loading) return <LoadingSpinner size="lg" className="min-h-screen" />

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login"    element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to="/" replace /> : <Register />} />

      {/* Core app */}
      <Route path="/"          element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/jobs"      element={<ProtectedRoute><JobList /></ProtectedRoute>} />
      <Route path="/jobs/new"  element={<ProtectedRoute><JobCreate /></ProtectedRoute>} />
      <Route path="/jobs/:id"  element={<ProtectedRoute><JobDetail /></ProtectedRoute>} />
      <Route path="/candidates"      element={<ProtectedRoute><CandidateList /></ProtectedRoute>} />
      <Route path="/candidates/new"  element={<ProtectedRoute><CandidateCreate /></ProtectedRoute>} />
      <Route path="/candidates/:id"  element={<ProtectedRoute><CandidateDetail /></ProtectedRoute>} />
      <Route path="/matching/:jobId" element={<ProtectedRoute><MatchResults /></ProtectedRoute>} />
      <Route path="/matching/:jobId/compare/:matchIdA/:matchIdB" element={<ProtectedRoute><CandidateCompare /></ProtectedRoute>} />
      <Route path="/matching/:jobId/explain/:matchId" element={<ProtectedRoute><ExplanationDetail /></ProtectedRoute>} />
      <Route path="/fairness" element={<ProtectedRoute><FairnessDashboard /></ProtectedRoute>} />

      {/* Tasks (session-10 feature) */}
      <Route path="/tasks"     element={<ProtectedRoute><TaskList /></ProtectedRoute>} />
      <Route path="/tasks/new" element={<ProtectedRoute><TaskCreate /></ProtectedRoute>} />
      <Route path="/tasks/:id" element={<ProtectedRoute><TaskDetail /></ProtectedRoute>} />

      {/* User management — admin & manager only */}
      <Route path="/users/create" element={<ProtectedRoute><CreateUser /></ProtectedRoute>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}

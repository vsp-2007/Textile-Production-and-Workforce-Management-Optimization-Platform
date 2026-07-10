import React, { useState, useEffect, useContext, createContext } from 'react'
import { Routes, Route, Navigate, Outlet, useNavigate, useLocation } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import api from './services/api'

// Pages
import Login from './pages/Login'
import AdminDashboard from './pages/AdminDashboard'
import SupervisorDashboard from './pages/SupervisorDashboard'
import OperatorTerminal from './pages/OperatorTerminal'
import FloorMap from './pages/FloorMap'

// Layouts
import MainLayout from './layouts/MainLayout'
import AuthLayout from './layouts/AuthLayout'

// Auth Context
const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const location = useLocation()

  const login = async (employeeId, password) => {
    try {
      const response = await api.post('/auth/login', { employee_id: employeeId, password })
      const { user: userData, access_token } = response.data
      
      // Store token
      localStorage.setItem('access_token', access_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      setUser(userData)
      toast.success(`Welcome back, ${userData.name}!`)
      
      // Redirect based on role
      const redirectPath = getRedirectPath(userData.role)
      navigate(redirectPath, { replace: true })
      
      return userData
    } catch (error) {
      const message = error.response?.data?.error || 'Login failed'
      toast.error(message)
      throw error
    }
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      localStorage.removeItem('access_token')
      delete api.defaults.headers.common['Authorization']
      setUser(null)
      navigate('/login', { replace: true })
    }
  }

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setLoading(false)
      return
    }

    try {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      const response = await api.get('/auth/me')
      setUser(response.data.user)
    } catch (error) {
      localStorage.removeItem('access_token')
      delete api.defaults.headers.common['Authorization']
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    checkAuth()
  }, [])

  const getRedirectPath = (role) => {
    switch (role) {
      case 'admin': return '/admin'
      case 'supervisor': return '/supervisor'
      case 'operator': return '/operator'
      default: return '/'
    }
  }

  const hasRole = (...roles) => {
    return user && roles.includes(user.role)
  }

  const value = {
    user,
    loading,
    login,
    logout,
    hasRole,
    isAuthenticated: !!user
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, loading, isAuthenticated } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="d-flex align-items-center justify-content-center" style={{ minHeight: '100vh' }}>
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-2 text-muted">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={getRedirectPath(user.role)} replace />
  }

  return children
}

const getRedirectPath = (role) => {
  switch (role) {
    case 'admin': return '/admin'
    case 'supervisor': return '/supervisor'
    case 'operator': return '/operator'
    default: return '/'
  }
}

// Public Route (redirects authenticated users)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading, user } = useAuth()

  if (loading) {
    return (
      <div className="d-flex align-items-center justify-content-center" style={{ minHeight: '100vh' }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to={getRedirectPath(user.role)} replace />
  }

  return children
}

const App = () => {
  return (
    <AuthProvider>
      <Routes>
        {/* Public Routes */}
        <Route element={<PublicRoute><AuthLayout /></PublicRoute>}>
          <Route path="/login" element={<Login />} />
        </Route>

        {/* Protected Routes */}
        <Route element={<ProtectedRoute allowedRoles={['admin']}><MainLayout /></ProtectedRoute>}>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/*" element={<AdminDashboard />} />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={['supervisor', 'admin']}><MainLayout /></ProtectedRoute>}>
          <Route path="/supervisor" element={<SupervisorDashboard />} />
          <Route path="/supervisor/*" element={<SupervisorDashboard />} />
          <Route path="/floor-map" element={<FloorMap />} />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={['operator']}><MainLayout /></ProtectedRoute>}>
          <Route path="/operator" element={<OperatorTerminal />} />
          <Route path="/operator/*" element={<OperatorTerminal />} />
        </Route>

        {/* Redirect root */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </AuthProvider>
  )
}

export default App
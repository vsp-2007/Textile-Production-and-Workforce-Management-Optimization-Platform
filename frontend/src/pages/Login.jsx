import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../App'
import { authService } from '../services/api'
import toast from 'react-hot-toast'
import './Login.css'

function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    employee_id: '',
    password: ''
  })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [demoUsers, setDemoUsers] = useState([])

  useEffect(() => {
    // Demo users for quick login
    setDemoUsers([
      { id: 'ADMIN001', name: 'Admin User', role: 'admin', password: 'Admin@123' },
      { id: 'SUPV001', name: 'Shift Supervisor', role: 'supervisor', password: 'Supervisor@123' },
      { id: 'OPR001', name: 'John Doe', role: 'operator', password: 'Operator@123' },
      { id: 'OPR002', name: 'Jane Smith', role: 'operator', password: 'Operator@123' },
      { id: 'OPR003', name: 'Mike Johnson', role: 'operator', password: 'Operator@123' }
    ])
  }, [])

  const validateForm = () => {
    const newErrors = {}
    if (!form.employee_id.trim()) {
      newErrors.employee_id = 'Employee ID is required'
    }
    if (!form.password) {
      newErrors.password = 'Password is required'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validateForm()) return

    setLoading(true)
    try {
      const userData = await login(form.employee_id, form.password)
      toast.success(`Welcome back, ${userData.name}!`)
      
      // Redirect based on role
      if (userData.role === 'admin') {
        navigate('/dashboard')
      } else if (userData.role === 'supervisor') {
        navigate('/dashboard')
      } else {
        navigate('/dashboard')
      }
    } catch (error) {
      const message = error.response?.data?.error || 'Invalid credentials. Please try again.'
      toast.error(message)
      setErrors({ form: message })
    } finally {
      setLoading(false)
    }
  }

  const handleDemoLogin = async (user) => {
    setLoading(true)
    setForm({ employee_id: user.id, password: user.password })
    try {
      const userData = await login(user.id, user.password)
      toast.success(`Logged in as ${userData.name} (${userData.role})`)
      navigate('/dashboard')
    } catch (error) {
      toast.error('Demo login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
    if (errors.form) {
      setErrors(prev => ({ ...prev, form: '' }))
    }
  }

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card">
          {/* Left Panel - Branding */}
          <div className="login-brand">
            <div className="login-logo">
              <i className="bi bi-thread"></i>
            </div>
            <h1 className="login-title">TexWorkforce Optimizer</h1>
            <p className="login-subtitle">
              Manufacturing Execution System & Workforce Management Platform
              for Textile Industry
            </p>
            
            <div className="features-list">
              <div className="feature-item">
                <i className="bi bi-check-circle-fill"></i>
                <span>Real-time Machine Monitoring</span>
              </div>
              <div className="feature-item">
                <i className="bi bi-check-circle-fill"></i>
                <span>Skill-based Workforce Scheduling</span>
              </div>
              <div className="feature-item">
                <i className="bi bi-check-circle-fill"></i>
                <span>Automated Reallocation Engine</span>
              </div>
              <div className="feature-item">
                <i className="bi bi-check-circle-fill"></i>
                <span>Production Analytics & Reports</span>
              </div>
            </div>

            <div className="version-info">
              <span>Version 1.0.0</span>
              <span>U23IT481 - Software Engineering Lab</span>
            </div>
          </div>

          {/* Right Panel - Login Form */}
          <div className="login-form-panel">
            <div className="form-header">
              <h2>Sign In</h2>
              <p>Enter your credentials to access the dashboard</p>
            </div>

            {errors.form && (
              <div className="alert alert-danger">
                <i className="bi bi-exclamation-triangle"></i>
                {errors.form}
              </div>
            )}

            <form onSubmit={handleSubmit} noValidate>
              <div className="form-group">
                <label htmlFor="employee_id">Employee ID</label>
                <div className="input-wrapper">
                  <i className="bi bi-person-badge input-icon"></i>
                  <input
                    type="text"
                    id="employee_id"
                    name="employee_id"
                    value={form.employee_id}
                    onChange={handleInputChange}
                    placeholder="e.g., ADMIN001, SUPV001, OPR001"
                    autoComplete="username"
                    disabled={loading}
                    className={errors.employee_id ? 'error' : ''}
                  />
                </div>
                {errors.employee_id && <span className="error-message">{errors.employee_id}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="password">Password</label>
                <div className="input-wrapper">
                  <i className="bi bi-lock input-icon"></i>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="password"
                    name="password"
                    value={form.password}
                    onChange={handleInputChange}
                    placeholder="Enter your password"
                    autoComplete="current-password"
                    disabled={loading}
                    className={errors.password ? 'error' : ''}
                  />
                  <button
                    type="button"
                    className="toggle-password"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    <i className={showPassword ? 'bi bi-eye-slash' : 'bi bi-eye'}></i>
                  </button>
                </div>
                {errors.password && <span className="error-message">{errors.password}</span>}
              </div>

              <div className="form-options">
                <label className="checkbox-wrapper">
                  <input type="checkbox" />
                  <span>Remember me</span>
                </label>
                <a href="#" className="forgot-password">Forgot Password?</a>
              </div>

              <button 
                type="submit" 
                className="btn btn-primary btn-lg btn-block login-btn"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="loading-spinner-sm"></span>
                    Signing in...
                  </>
                ) : (
                  'Sign In'
                )}
              </button>
            </form>

            <div className="demo-section">
              <p className="demo-title">Quick Demo Access</p>
              <div className="demo-users">
                {demoUsers.map(user => (
                  <button
                    key={user.id}
                    type="button"
                    className="demo-user-btn"
                    onClick={() => handleDemoLogin(user)}
                    disabled={loading}
                  >
                    <div className="demo-user-info">
                      <span className="demo-user-id">{user.id}</span>
                      <span className="demo-user-name">{user.name}</span>
                    </div>
                    <span className={`demo-role-badge ${user.role}`}>{user.role}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="login-footer">
              <p>
                <strong>TexWorkforce Optimizer</strong> - Textile Production & 
                Workforce Management Optimization Platform
              </p>
              <p className="text-muted">
                Sri Eshwar College of Engineering • U23IT481
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
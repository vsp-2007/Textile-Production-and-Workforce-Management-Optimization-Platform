import React, { useState, useEffect } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { useAuth } from '../App'
import { operatorService, machineService, shiftService, reportService, alertService } from '../services/api'
import toast from 'react-hot-toast'
import './OperatorTerminal.css'

function OperatorTerminal() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [operator, setOperator] = useState(null)
  const [schedule, setSchedule] = useState([])
  const [currentShift, setCurrentShift] = useState(null)
  const [activeTab, setActiveTab] = useState('schedule')
  const [notifications, setNotifications] = useState([])
  const [showNotification, setShowNotification] = useState(false)

  useEffect(() => {
    fetchOperatorData()
    fetchNotifications()
    
    // Set up real-time updates
    const interval = setInterval(fetchNotifications, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchOperatorData = async () => {
    try {
      setLoading(true)
      const [operatorRes, scheduleRes] = await Promise.all([
        operatorService.get(user.id),
        operatorService.getSchedule(user.id)
      ])
      
      setOperator(operatorRes.data.operator)
      setSchedule(scheduleRes.data.schedule || [])
      
      // Find current shift
      const now = new Date()
      const current = scheduleRes.data.schedule?.find(s => {
        const start = new Date(s.shift.start_time)
        const end = new Date(s.shift.end_time)
        return now >= start && now <= end && s.status === 'started'
      })
      setCurrentShift(current || null)
    } catch (error) {
      toast.error('Failed to load operator data')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const fetchNotifications = async () => {
    try {
      const res = await alertService.list({ operator_id: user.id, is_read: false, days: 7 })
      setNotifications(res.data.alerts || [])
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
    }
  }

  const handleClockIn = async (assignmentId) => {
    try {
      await shiftService.updateAssignment(assignmentId, { status: 'started' })
      toast.success('Clocked in successfully')
      fetchOperatorData()
    } catch (error) {
      toast.error('Failed to clock in')
    }
  }

  const handleClockOut = async (assignmentId) => {
    try {
      await shiftService.updateAssignment(assignmentId, { status: 'completed' })
      toast.success('Clocked out successfully')
      fetchOperatorData()
    } catch (error) {
      toast.error('Failed to clock out')
    }
  }

  const handleReportDelay = async (assignmentId, reason) => {
    try {
      await shiftService.updateAssignment(assignmentId, { 
        status: 'reassigned',
        notes: `Delay reported: ${reason}`
      })
      toast.success('Delay reported')
      fetchOperatorData()
    } catch (error) {
      toast.error('Failed to report delay')
    }
  }

  const handleRequestMaintenance = async (machineId) => {
    try {
      await machineService.updateStatus(machineId, { 
        status: 'maintenance',
        reason: 'Maintenance requested by operator'
      })
      toast.success('Maintenance requested')
      fetchOperatorData()
    } catch (error) {
      toast.error('Failed to request maintenance')
    }
  }

  const getShiftStatus = (shift) => {
    const now = new Date()
    const start = new Date(shift.shift.start_time)
    const end = new Date(shift.shift.end_time)
    
    if (now < start) return 'upcoming'
    if (now > end) return 'past'
    return 'active'
  }

  if (loading) {
    return (
      <div className="terminal-loading">
        <div className="loading-spinner"></div>
        <p>Loading your terminal...</p>
      </div>
    )
  }

  return (
    <div className="operator-terminal">
      {/* Header */}
      <header className="terminal-header">
        <div className="header-left">
          <div className="operator-badge">
            <span className="badge-label">OPERATOR</span>
            <span className="badge-id">{operator?.employee_id}</span>
          </div>
          <div className="operator-info">
            <h1>{operator?.name}</h1>
            <div className="operator-meta">
              <span><i className="bi bi-building"></i> {operator?.department?.name || 'N/A'}</span>
              <span><i className="bi bi-clock"></i> {operator?.shift_pattern || 'N/A'} Shift</span>
            </div>
          </div>
        </div>
        
        <div className="header-right">
          <div className="current-time" id="currentTime"></div>
          <div className="header-actions">
            <button 
              className={`notification-btn ${notifications.length > 0 ? 'has-alerts' : ''}`}
              onClick={() => setShowNotification(!showNotification)}
              aria-label="Notifications"
            >
              <i className="bi bi-bell"></i>
              {notifications.length > 0 && (
                <span className="notification-count">{notifications.length}</span>
              )}
            </button>
            <div className="theme-toggle" onClick={() => {
              const newTheme = document.documentElement.classList.contains('high-contrast') ? 'light' : 'high-contrast'
              document.documentElement.classList.toggle('high-contrast')
              localStorage.setItem('theme', newTheme)
            }}>
              <i className={`bi ${document.documentElement.classList.contains('high-contrast') ? 'bi-sun' : 'bi-moon'}`}></i>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={logout}>
              <i className="bi bi-box-arrow-right"></i> Logout
            </button>
          </div>
        </div>
      </header>

      {/* Notification Panel */}
      {showNotification && (
        <div className="notification-panel" onClick={(e) => e.stopPropagation()}>
          <div className="panel-header">
            <h3>Notifications</h3>
            <button className="btn btn-ghost btn-sm" onClick={() => setShowNotification(false)}>
              <i className="bi bi-x"></i>
            </button>
          </div>
          <div className="panel-body">
            {notifications.length === 0 ? (
              <p className="no-notifications">No new notifications</p>
            ) : (
              notifications.map(alert => (
                <div key={alert.id} className={`alert-item alert-${alert.severity}`}>
                  <div className="alert-icon">
                    <i className={`bi ${alert.alert_type === 'machine_fault' ? 'bi-exclamation-triangle' : 'bi-info-circle'}`}></i>
                  </div>
                  <div className="alert-content">
                    <p className="alert-message">{alert.message}</p>
                    <span className="alert-time">
                      {new Date(alert.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <button 
                    className="btn btn-ghost btn-sm"
                    onClick={() => alertService.acknowledge(alert.id)}
                  >
                    <i className="bi bi-check"></i>
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <nav className="terminal-tabs" role="tablist">
        <button 
          role="tab"
          className={`tab-btn ${activeTab === 'schedule' ? 'active' : ''}`}
          onClick={() => setActiveTab('schedule')}
          aria-selected={activeTab === 'schedule'}
        >
          <i className="bi bi-calendar-check"></i>
          <span>My Schedule</span>
        </button>
        <button 
          role="tab"
          className={`tab-btn ${activeTab === 'machines' ? 'active' : ''}`}
          onClick={() => setActiveTab('machines')}
          aria-selected={activeTab === 'machines'}
        >
          <i className="bi bi-cpu"></i>
          <span>My Machines</span>
        </button>
        <button 
          role="tab"
          className={`tab-btn ${activeTab === 'production' ? 'active' : ''}`}
          onClick={() => setActiveTab('production')}
          aria-selected={activeTab === 'production'}
        >
          <i className="bi bi-graph-up"></i>
          <span>Production</span>
        </button>
        <button 
          role="tab"
          className={`tab-btn ${activeTab === 'certifications' ? 'active' : ''}`}
          onClick={() => setActiveTab('certifications')}
          aria-selected={activeTab === 'certifications'}
        >
          <i className="bi bi-award"></i>
          <span>Certifications</span>
        </button>
      </nav>

      {/* Tab Content */}
      <main className="terminal-content">
        {activeTab === 'schedule' && (
          <div className="tab-panel" role="tabpanel">
            <div className="panel-header">
              <h2>Today's Schedule</h2>
              {currentShift && (
                <div className="current-shift-badge">
                  <span className="pulse"></span>
                  Currently on: {currentShift.shift.name}
                </div>
              )}
            </div>

            {schedule.length === 0 ? (
              <div className="empty-state">
                <i className="bi bi-calendar-x"></i>
                <h3>No Shifts Scheduled</h3>
                <p>You don't have any shifts assigned for today.</p>
              </div>
            ) : (
              <div className="schedule-list">
                {schedule.map(assignment => (
                  <div key={assignment.id} className={`schedule-card ${getShiftStatus(assignment)}`}>
                    <div className="schedule-card-header">
                      <div className="shift-info">
                        <span className="shift-name">{assignment.shift.name}</span>
                        <span className="shift-time">
                          {formatTime(assignment.shift.start_time)} - {formatTime(assignment.shift.end_time)}
                        </span>
                      </div>
                      <span className={`shift-status status-${getShiftStatus(assignment)}`}>
                        {getShiftStatus(assignment).charAt(0).toUpperCase() + getShiftStatus(assignment).slice(1)}
                      </span>
                    </div>
                    
                    <div className="schedule-card-body">
                      <div className="machine-info">
                        <div className="machine-code">{assignment.machine?.machine_code}</div>
                        <div className="machine-name">{assignment.machine?.name}</div>
                        <div className="machine-location">
                          <i className="bi bi-geo"></i> {assignment.machine?.floor_zone || 'Zone A'}
                        </div>
                      </div>
                      
                      <div className="assignment-actions">
                        {assignment.status === 'assigned' && getShiftStatus(assignment) === 'active' && (
                          <button 
                            className="btn btn-success btn-sm"
                            onClick={() => handleClockIn(assignment.id)}
                          >
                            <i className="bi bi-play-circle"></i> Start Shift
                          </button>
                        )}
                        {assignment.status === 'started' && (
                          <>
                            <button 
                              className="btn btn-primary btn-sm"
                              onClick={() => handleClockOut(assignment.id)}
                            >
                              <i className="bi bi-stop-circle"></i> End Shift
                            </button>
                            <button 
                              className="btn btn-warning btn-sm"
                              onClick={() => {
                                const reason = prompt('Reason for delay:')
                                if (reason) handleReportDelay(assignment.id, reason)
                              }}
                            >
                              <i className="bi bi-exclamation-triangle"></i> Report Delay
                            </button>
                            <button 
                              className="btn btn-secondary btn-sm"
                              onClick={() => handleRequestMaintenance(assignment.machine_id)}
                            >
                              <i className="bi bi-tools"></i> Request Maintenance
                            </button>
                          </>
                        )}
                        {assignment.status === 'completed' && (
                          <span className="completed-badge">
                            <i className="bi bi-check-circle"></i> Completed
                          </span>
                        )}
                        {assignment.status === 'cancelled' && (
                          <span className="cancelled-badge">
                            <i className="bi bi-x-circle"></i> Cancelled
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'machines' && (
          <div className="tab-panel" role="tabpanel">
            <div className="panel-header">
              <h2>Assigned Machines</h2>
            </div>
            
            <div className="machines-grid">
              {schedule.map(assignment => (
                <div key={assignment.id} className="machine-card-terminal">
                  <div className="machine-card-header">
                    <div>
                      <div className="machine-code">{assignment.machine?.machine_code}</div>
                      <div className="machine-name">{assignment.machine?.name}</div>
                    </div>
                    <span className={`machine-status status-${assignment.machine?.status?.toLowerCase() || 'idle'}`}>
                      {assignment.machine?.status || 'Unknown'}
                    </span>
                  </div>
                  
                  <div className="machine-card-body">
                    <div className="machine-details">
                      <span><i className="bi bi-tag"></i> {assignment.machine?.machine_type?.name}</span>
                      <span><i className="bi bi-geo"></i> {assignment.machine?.floor_zone}</span>
                    </div>
                    
                    <div className="machine-telemetry">
                      <div className="telemetry-item">
                        <span className="telemetry-label">Output</span>
                        <span className="telemetry-value">
                          {assignment.machine?.latest_telemetry?.output_count || 0} yds
                        </span>
                      </div>
                      <div className="telemetry-item">
                        <span className="telemetry-label">RPM</span>
                        <span className="telemetry-value">
                          {assignment.machine?.latest_telemetry?.rpm || 0}
                        </span>
                      </div>
                      <div className="telemetry-item">
                        <span className="telemetry-label">Temp</span>
                        <span className="telemetry-value">
                          {assignment.machine?.latest_telemetry?.temperature || 0}°C
                        </span>
                      </div>
                      <div className="telemetry-item">
                        <span className="telemetry-label">Status</span>
                        <span className="telemetry-value">
                          {assignment.machine?.latest_telemetry?.status || 'N/A'}
                        </span>
                      </div>
                    </div>
                    
                    <div className="machine-actions">
                      {assignment.status === 'started' && (
                        <button 
                          className="btn btn-danger btn-sm"
                          onClick={() => handleRequestMaintenance(assignment.machine_id)}
                        >
                          <i className="bi bi-tools"></i> Request Maintenance
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              {schedule.length === 0 && (
                <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
                  <i className="bi bi-cpu"></i>
                  <h3>No Machines Assigned</h3>
                  <p>You don't have any machines assigned for current shifts.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'production' && (
          <div className="tab-panel" role="tabpanel">
            <div className="panel-header">
              <h2>Production Log</h2>
            </div>
            
            <div className="production-summary">
              <div className="summary-card">
                <div className="summary-value">{calculateTotalYards()} yds</div>
                <div className="summary-label">Total Produced Today</div>
              </div>
              <div className="summary-card">
                <div className="summary-value">{calculateEfficiency()}%</div>
                <div className="summary-label">Efficiency</div>
              </div>
              <div className="summary-card">
                <div className="summary-value">{calculateWaste()}%</div>
                <div className="summary-label">Waste Rate</div>
              </div>
              <div className="summary-card">
                <div className="summary-value">{schedule.filter(s => s.status === 'completed').length}</div>
                <div className="summary-label">Completed Shifts</div>
              </div>
            </div>

            <div className="production-table-container">
              <table className="production-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Shift</th>
                    <th>Machine</th>
                    <th>Target (yds)</th>
                    <th>Actual (yds)</th>
                    <th>Waste (yds)</th>
                    <th>Efficiency</th>
                    <th>Quality</th>
                  </tr>
                </thead>
                <tbody>
                  {schedule.flatMap(s => s.production_logs || []).map(log => (
                    <tr key={log.id}>
                      <td>{formatDate(log.start_time)}</td>
                      <td>{log.assignment?.shift?.name}</td>
                      <td>{log.machine?.machine_code}</td>
                      <td>{log.target_yards}</td>
                      <td>{log.actual_yards}</td>
                      <td className="waste-cell">{log.waste_yards}</td>
                      <td>
                        <div className="efficiency-bar">
                          <div 
                            className="efficiency-fill" 
                            style={{ width: `${log.efficiency || 0}%` }}
                          ></div>
                        </div>
                        <span>{log.efficiency?.toFixed(1) || 0}%</span>
                      </td>
                      <td>
                        <span className={`quality-badge quality-${log.quality_grade?.toLowerCase()}`}>
                          {log.quality_grade || 'N/A'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {schedule.flatMap(s => s.production_logs || []).length === 0 && (
                <div className="empty-state">
                  <i className="bi bi-graph-up"></i>
                  <h3>No Production Data</h3>
                  <p>Production logs will appear here after completing shifts.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'certifications' && (
          <div className="tab-panel" role="tabpanel">
            <div className="panel-header">
              <h2>My Certifications</h2>
            </div>
            
            <div className="certifications-grid">
              {operator?.certifications?.map(cert => (
                <div key={cert.id} className={`cert-card ${cert.is_valid ? '' : 'expired'}`}>
                  <div className="cert-header">
                    <div className="cert-icon">
                      <i className="bi bi-award"></i>
                    </div>
                    <div className="cert-status">
                      {cert.is_valid ? (
                        <span className="badge bg-success">Valid</span>
                      ) : (
                        <span className="badge bg-danger">Expired</span>
                      )}
                    </div>
                  </div>
                  <div className="cert-body">
                    <h4>{cert.certification?.name}</h4>
                    <p className="cert-code">{cert.certification?.code} - Level {cert.certification?.level}</p>
                    <div className="cert-dates">
                      <span><i className="bi bi-calendar-check"></i> Obtained: {formatDate(cert.obtained_date)}</span>
                      {cert.expiry_date && (
                        <span><i className="bi bi-calendar-x"></i> Expires: {formatDate(cert.expiry_date)}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              {(!operator?.certifications || operator.certifications.length === 0) && (
                <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
                  <i className="bi bi-award"></i>
                  <h3>No Certifications</h3>
                  <p>You don't have any certifications assigned yet.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  const [hours, minutes] = timeStr.split(':')
  const hour = parseInt(hours)
  const ampm = hour >= 12 ? 'PM' : 'AM'
  const displayHour = hour % 12 || 12
  return `${displayHour}:${minutes} ${ampm}`
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric' 
  })
}

function calculateTotalYards() {
  // This would come from production logs
  return 0
}

function calculateEfficiency() {
  return 0
}

function calculateWaste() {
  return 0
}

function getShiftStatus(shift) {
  const now = new Date()
  const start = new Date(shift.shift?.start_time)
  const end = new Date(shift.shift?.end_time)
  
  if (now < start) return 'upcoming'
  if (now > end) return 'past'
  return 'active'
}

// Update clock every second
useEffect(() => {
  const updateClock = () => {
    const now = new Date()
    const timeString = now.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: true 
    })
    const dateString = now.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    })
    const element = document.getElementById('currentTime')
    if (element) {
      element.innerHTML = `${dateString} • ${timeString}`
    }
  }
  
  updateClock()
  const interval = setInterval(updateClock, 1000)
  return () => clearInterval(interval)
}, [])

export default OperatorTerminal
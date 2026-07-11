import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth, useSocket } from '../../App'
import { machineService, shiftService, alertService } from '../../services/api'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell 
} from 'recharts'
import './SupervisorDashboard.css'

function SupervisorDashboard() {
  const { user, isSupervisor } = useAuth()
  const { socket, on, off } = useSocket()
  const navigate = useNavigate()
  
  const [stats, setStats] = useState({
    totalMachines: 0,
    activeMachines: 0,
    idleMachines: 0,
    faultMachines: 0,
    totalOperators: 0,
    presentOperators: 0,
    todayYards: 0,
    todayWaste: 0,
    avgOEE: 0
  })
  
  const [machines, setMachines] = useState([])
  const [alerts, setAlerts] = useState([])
  const [shiftData, setShiftData] = useState([])
  const [productionData, setProductionData] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedShift, setSelectedShift] = useState(null)
  const [shifts, setShifts] = useState([])

  // Colors for charts
  const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#8b5cf6']
  
  // Machine status colors
  const STATUS_COLORS = {
    active: '#10b981',
    idle: '#f59e0b',
    maintenance: '#06b6d4',
    fault: '#ef4444',
    offline: '#64748b',
    disconnected: '#9ca3af'
  }

  useEffect(() => {
    if (!isSupervisor) {
      navigate('/dashboard')
      return
    }
    fetchDashboardData()
    setupSocketListeners()
    
    return () => {
      cleanupSocketListeners()
    }
  }, [isSupervisor])

  const setupSocketListeners = () => {
    if (!socket) return
    
    socket.on('machine_status_update', handleMachineUpdate)
    socket.on('machine_telemetry', handleTelemetryUpdate)
    socket.on('assignment_created', handleAssignmentChange)
    socket.on('assignment_updated', handleAssignmentChange)
    socket.on('assignment_deleted', handleAssignmentChange)
    socket.on('shift_started', () => fetchDashboardData())
    socket.on('shift_ended', () => fetchDashboardData())
    socket.on('new_alert', handleNewAlert)
    socket.on('alert_acknowledged', handleAlertAcknowledged)
  }

  const cleanupSocketListeners = () => {
    if (!socket) return
    socket.off('machine_status_update', handleMachineUpdate)
    socket.off('machine_telemetry', handleTelemetryUpdate)
    socket.off('assignment_created', handleAssignmentChange)
    socket.off('assignment_updated', handleAssignmentChange)
    socket.off('assignment_deleted', handleAssignmentChange)
    socket.off('shift_started', fetchDashboardData)
    socket.off('shift_ended', fetchDashboardData)
    socket.off('new_alert', handleNewAlert)
    socket.off('alert_acknowledged', handleAlertAcknowledged)
  }

  const handleMachineUpdate = (data) => {
    setMachines(prev => {
      const index = prev.findIndex(m => m.id === data.machine_id)
      if (index >= 0) {
        const updated = [...prev]
        updated[index] = { ...updated[index], status: data.status, latest_telemetry: data.telemetry }
        return updated
      }
      return prev
    })
    // Refresh stats
    fetchMachineStats()
  }

  const handleTelemetryUpdate = (data) => {
    // Update real-time telemetry
    setMachines(prev => {
      const index = prev.findIndex(m => m.id === data.machine_id)
      if (index >= 0) {
        const updated = [...prev]
        updated[index] = { ...updated[index], latest_telemetry: data.telemetry }
        return updated
      }
      return prev
    })
  }

  const handleAssignmentChange = () => {
    fetchShiftData()
  }

  const handleNewAlert = (alert) => {
    setAlerts(prev => [alert, ...prev].slice(0, 50))
    // Show toast notification
    import('react-hot-toast').then(({ toast }) => {
      toast.error(alert.message, { duration: 5000 })
    })
  }

  const handleAlertAcknowledged = (data) => {
    setAlerts(prev => prev.map(a => 
      a.id === data.alert_id ? { ...a, is_read: true, acknowledged_at: data.acknowledged_at } : a
    ))
  }

  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      const [statsRes, machinesRes, alertsRes, shiftsRes, shiftDataRes] = await Promise.all([
        machineService.getStats(),
        machineService.list({ per_page: 50 }),
        alertService.list({ per_page: 20, is_read: false }),
        shiftService.list(),
        shiftService.getToday()
      ])
      
      setStats(statsRes.data)
      setMachines(machinesRes.data.machines)
      setAlerts(alertsRes.data.alerts)
      setShifts(shiftsRes.data.shifts)
      setShiftData(shiftDataRes.data.shifts)
      
      // Calculate production data for charts
      calculateProductionCharts(shiftDataRes.data.shifts)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      import('react-hot-toast').then(({ toast }) => {
        toast.error('Failed to load dashboard data')
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchMachineStats = async () => {
    try {
      const res = await machineService.getStats()
      setStats(prev => ({ ...prev, ...res.data }))
    } catch (error) {
      console.error('Failed to fetch machine stats:', error)
    }
  }

  const fetchShiftData = async () => {
    try {
      const res = await shiftService.getToday()
      setShiftData(res.data.shifts)
      calculateProductionCharts(res.data.shifts)
    } catch (error) {
      console.error('Failed to fetch shift data:', error)
    }
  }

  const calculateProductionCharts = (shifts) => {
    // Hourly production for today
    const hourlyData = {}
    const hourlyTarget = {}
    
    shifts.forEach(shift => {
      shift.assignments?.forEach(assignment => {
        assignment.production_logs?.forEach(log => {
          if (log.start_time) {
            const hour = new Date(log.start_time).getHours()
            const key = `${hour}:00`
            hourlyData[key] = (hourlyData[key] || 0) + (log.actual_yards || 0)
            hourlyTarget[key] = (hourlyTarget[key] || 0) + (log.target_yards || 0)
          }
        })
      })
    })
    
    const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`)
    const productionChartData = hours.map(hour => ({
      hour,
      actual: hourlyData[hour] || 0,
      target: hourlyTarget[hour] || 0
    }))
    
    setProductionData(productionChartData)
  }

  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await alertService.acknowledge(alertId)
      setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, is_read: true } : a))
    } catch (error) {
      console.error('Failed to acknowledge alert:', error)
    }
  }

  const getStatusBadge = (status) => (
    <span className={`status-badge status-${status}`}>
      <span className="status-dot"></span>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )

  const renderOverviewTab = () => (
    <div className="dashboard-tab">
      {/* Stats Grid */}
      <div className="stats-grid">
        <StatCard
          title="Total Machines"
          value={stats.totalMachines}
          icon="bi-cpu"
          color="primary"
          trend={{ value: stats.activeMachines, label: "Active" }}
        />
        <StatCard
          title="Active Machines"
          value={stats.activeMachines}
          icon="bi-play-circle-fill"
          color="success"
        />
        <StatCard
          title="Idle Machines"
          value={stats.idleMachines}
          icon="bi-pause-circle-fill"
          color="warning"
        />
        <StatCard
          title="Faults"
          value={stats.faultMachines}
          icon="bi-exclamation-triangle-fill"
          color="danger"
        />
        <StatCard
          title="Operators Present"
          value={`${stats.presentOperators}/${stats.totalOperators}`}
          icon="bi-people-fill"
          color="info"
        />
        <StatCard
          title="Today's Production"
          value={`${(stats.todayYards / 1000).toFixed(1)}K yds`}
          icon="bi-graph-up"
          color="primary"
          trend={{ value: `${stats.todayWaste} yds waste`, label: "Waste" }}
        />
      </div>

      {/* Charts Row */}
      <div className="charts-row">
        <div className="chart-card">
          <div className="chart-header">
            <h3>Hourly Production (Today)</h3>
            <div className="chart-legend">
              <span className="legend-item"><span className="legend-color" style={{background: '#2563eb'}}></span>Actual</span>
              <span className="legend-item"><span className="legend-color" style={{background: '#94a3b8'}}></span>Target</span>
            </div>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={productionData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" tickFormatter={v => `${v/1000}K`} stroke="#64748b" fontSize={11} />
                <YAxis dataKey="hour" type="category" width={50} stroke="#64748b" fontSize={11} />
                <Tooltip 
                  formatter={(value, name) => [name === 'actual' ? `${value} yds` : `${value} yds`, name === 'actual' ? 'Actual' : 'Target']}
                  labelFormatter={hour => hour}
                />
                <Legend />
                <Bar dataKey="actual" fill="#2563eb" radius={[0, 4, 4, 0]} />
                <Bar dataKey="target" fill="#94a3b8" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card">
          <div className="chart-header">
            <h3>Machine Status Distribution</h3>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Active', value: stats.activeMachines, color: STATUS_COLORS.active },
                    { name: 'Idle', value: stats.idleMachines, color: STATUS_COLORS.idle },
                    { name: 'Maintenance', value: 0, color: STATUS_COLORS.maintenance },
                    { name: 'Fault', value: stats.faultMachines, color: STATUS_COLORS.fault },
                    { name: 'Offline', value: stats.offlineMachines || 0, color: STATUS_COLORS.offline },
                  ].filter(d => d.value > 0)}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {[
                    { name: 'Active', value: stats.activeMachines, color: STATUS_COLORS.active },
                    { name: 'Idle', value: stats.idleMachines, color: STATUS_COLORS.idle },
                    { name: 'Fault', value: stats.faultMachines, color: STATUS_COLORS.fault },
                  ].filter(d => d.value > 0).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={v => `${v} machines`} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Machines Table */}
      <div className="chart-card">
        <div className="chart-header">
          <h3>Machine Status Overview</h3>
          <Link to="/machines" className="btn btn-ghost btn-sm">View All</Link>
        </div>
        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                <th>Machine</th>
                <th>Type</th>
                <th>Zone</th>
                <th>Status</th>
                <th>Operator</th>
                <th>Output (yds)</th>
                <th>Last Update</th>
              </tr>
            </thead>
            <tbody>
              {machines.slice(0, 10).map(machine => (
                <tr key={machine.id}>
                  <td>
                    <strong>{machine.machine_code}</strong>
                    <br><small className="text-muted">{machine.name}</small>
                  </td>
                  <td>{machine.machine_type?.name || 'N/A'}</td>
                  <td>{machine.floor_zone || '-'}</td>
                  <td>{getStatusBadge(machine.status)}</td>
                  <td>
                    {machine.current_operator ? (
                      <span>{machine.current_operator.name}</span>
                    ) : (
                      <span className="text-muted">Unassigned</span>
                    )}
                  </td>
                  <td>{machine.latest_telemetry?.output_count || 0}</td>
                  <td>
                    {machine.last_telemetry_at ? (
                      <span className="text-muted">
                        {new Date(machine.last_telemetry_at).toLocaleTimeString()}
                      </span>
                    ) : (
                      <span className="text-muted">Never</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Alerts Panel */}
      {alerts.length > 0 && (
        <div className="chart-card">
          <div className="chart-header">
            <h3>Active Alerts</h3>
          </div>
          <div className="alerts-list">
            {alerts.slice(0, 5).map(alert => (
              <div key={alert.id} className={`alert-item alert-${alert.severity}`}>
                <div className="alert-icon">
                  <i className={getAlertIcon(alert.alert_type)}></i>
                </div>
                <div className="alert-content">
                  <div className="alert-message">{alert.message}</div>
                  <div className="alert-meta">
                    <span className="alert-time">{new Date(alert.created_at).toLocaleTimeString()}</span>
                    {alert.machine_code && <span className="alert-machine">{alert.machine_code}</span>}
                  </div>
                </div>
                {!alert.is_read && (
                  <button 
                    className="btn btn-ghost btn-sm"
                    onClick={() => handleAcknowledgeAlert(alert.id)}
                  >
                    Acknowledge
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  const renderMachinesTab = () => (
    <div className="dashboard-tab">
      <div className="tab-header">
        <h2>Machine Monitoring</h2>
        <div className="tab-filters">
          <select className="form-select form-select-sm" style={{width: 'auto'}}>
            <option>All Status</option>
            <option>Active</option>
            <option>Idle</option>
            <option>Fault</option>
            <option>Maintenance</option>
          </select>
        </div>
      </div>
      <div className="machines-grid">
        {machines.map(machine => (
          <MachineCard 
            key={machine.id} 
            machine={machine} 
            onClick={() => navigate(`/machines/${machine.id}`)}
          />
        ))}
      </div>
    </div>
  )

  const renderSchedulerTab = () => (
    <div className="dashboard-tab">
      <div className="tab-header">
        <h2>Shift Scheduler</h2>
        <Link to="/scheduler" className="btn btn-primary">
          <i className="bi bi-plus"></i> Open Full Scheduler
        </Link>
      </div>
      <div className="shifts-overview">
        {shiftData.map(shift => (
          <ShiftCard key={shift.shift?.id} shift={shift} />
        ))}
      </div>
    </div>
  )

  const renderReportsTab = () => (
    <div className="dashboard-tab">
      <div className="tab-header">
        <h2>Production Reports</h2>
        <Link to="/reports" className="btn btn-primary">
          <i className="bi bi-file-earmark-arrow-down"></i> View All Reports
        </Link>
      </div>
      <div className="reports-summary">
        <ReportSummaryCard 
          title="Today's Efficiency" 
          value={`${((stats.todayYards / (stats.todayYards + stats.todayWaste || 1)) * 100).toFixed(1)}%`}
          subtitle={`${stats.todayYards} yds produced • ${stats.todayWaste} yds waste`}
        />
        <ReportSummaryCard 
          title="Average OEE" 
          value={`${stats.avgOEE?.toFixed(1) || '0'}%`}
          subtitle="Overall Equipment Effectiveness"
        />
        <ReportSummaryCard 
          title="Shift Utilization" 
          value={`${((stats.activeMachines / (stats.totalMachines || 1)) * 100).toFixed(1)}%`}
          subtitle={`${stats.activeMachines} of ${stats.totalMachines} machines active`}
        />
      </div>
    </div>
  )

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    )
  }

  return (
    <div className="supervisor-dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Supervisor Dashboard</h1>
          <p className="text-muted">Good {getTimeOfDay()}, {user?.name?.split(' ')[0]} • {new Date().toLocaleDateString()}</p>
        </div>
        <div className="dashboard-actions">
          <button className="btn btn-outline-primary" onClick={fetchDashboardData}>
            <i className="bi bi-arrow-clockwise"></i> Refresh
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/scheduler')}>
            <i className="bi bi-calendar-plus"></i> Create Shift
          </button>
        </div>
      </div>

      <div className="dashboard-tabs">
        <nav className="tabs-nav">
          <button 
            className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <i className="bi bi-house"></i> Overview
          </button>
          <button 
            className={`tab-btn ${activeTab === 'machines' ? 'active' : ''}`}
            onClick={() => setActiveTab('machines')}
          >
            <i className="bi bi-cpu"></i> Machines
          </button>
          <button 
            className={`tab-btn ${activeTab === 'scheduler' ? 'active' : ''}`}
            onClick={() => setActiveTab('scheduler')}
          >
            <i className="bi bi-calendar3"></i> Scheduler
          </button>
          <button 
            className={`tab-btn ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => setActiveTab('reports')}
          >
            <i className="bi bi-file-bar-graph"></i> Reports
          </button>
        </nav>

        <div className="tab-content">
          {activeTab === 'overview' && renderOverviewTab()}
          {activeTab === 'machines' && renderMachinesTab()}
          {activeTab === 'scheduler' && renderSchedulerTab()}
          {activeTab === 'reports' && renderReportsTab()}
        </div>
      </div>
    </div>
  )
}

function getTimeOfDay() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Morning'
  if (hour < 17) return 'Afternoon'
  return 'Evening'
}

function getAlertIcon(type) {
  const icons = {
    machine_fault: 'bi-exclamation-triangle',
    machine_idle: 'bi-pause-circle',
    maintenance_due: 'bi-tools',
    operator_absent: 'bi-person-x',
    certification_expiring: 'bi-award',
    shift_violation: 'bi-clock-history',
    reallocation_needed: 'bi-arrow-repeat',
    connection_lost: 'bi-wifi-off'
  }
  return icons[type] || 'bi-bell'
}

// Stat Card Component
function StatCard({ title, value, icon, color, trend }) {
  const colors = {
    primary: 'bg-primary',
    success: 'bg-success',
    warning: 'bg-warning',
    danger: 'bg-danger',
    info: 'bg-info'
  }
  
  return (
    <div className="stat-card">
      <div className="stat-icon">
        <i className={`bi ${icon} ${colors[color]}`}></i>
      </div>
      <div className="stat-content">
        <div className="stat-value">{value}</div>
        <div className="stat-label">{title}</div>
        {trend && (
          <div className="stat-trend">
            <span>{trend.value}</span>
            <span className="text-muted">{trend.label}</span>
          </div>
        )}
      </div>
    </div>
  )
}

// Machine Card Component
function MachineCard({ machine, onClick }) {
  const statusColors = {
    active: 'status-active',
    idle: 'status-idle',
    maintenance: 'status-maintenance',
    fault: 'status-fault',
    offline: 'status-offline',
    disconnected: 'status-disconnected'
  }

  return (
    <div className="machine-card" onClick={onClick}>
      <div className="machine-card-header">
        <div>
          <div className="machine-code">{machine.machine_code}</div>
          <div className="machine-name">{machine.name}</div>
        </div>
        <span className={`machine-status ${statusColors[machine.status] || ''}`}>
          {machine.status.charAt(0).toUpperCase() + machine.status.slice(1)}
        </span>
      </div>
      <div className="machine-card-body">
        <div className="machine-info">
          <span><i className="bi bi-tag"></i> {machine.machine_type?.name || 'N/A'}</span>
          <span><i className="bi bi-geo"></i> {machine.floor_zone || 'N/A'}</span>
        </div>
        {machine.current_operator && (
          <div className="machine-operator">
            <i className="bi bi-person"></i> {machine.current_operator.name}
          </div>
        )}
        <div className="machine-metrics">
          <div className="metric">
            <span className="metric-value">{machine.latest_telemetry?.output_count || 0}</span>
            <span className="metric-label">Output (yds)</span>
          </div>
          <div className="metric">
            <span className="metric-value">{machine.latest_telemetry?.rpm || 0}</span>
            <span className="metric-label">RPM</span>
          </div>
          <div className="metric">
            <span className="metric-value">{machine.latest_telemetry?.temperature || 0}°C</span>
            <span className="metric-label">Temp</span>
          </div>
        </div>
      </div>
    </div>
  )
}

// Shift Card Component
function ShiftCard({ shift }) {
  const assignments = shift.assignments || []
  const activeCount = assignments.filter(a => a.status === 'started').length
  const totalCount = assignments.length
  
  return (
    <div className="shift-card">
      <div className="shift-card-header">
        <div>
          <h4>{shift.shift?.name || 'Unknown Shift'}</h4>
          <small className="text-muted">
            {shift.shift?.start_time} - {shift.shift?.end_time}
          </small>
        </div>
        <div className="shift-status">
          <span className="badge bg-primary">{activeCount}/{totalCount} Active</span>
        </div>
      </div>
      <div className="shift-assignments">
        {assignments.map(assignment => (
          <div key={assignment.id} className="assignment-row">
            <span className="machine-code">{assignment.machine?.machine_code}</span>
            <span className="operator-name">{assignment.operator?.name}</span>
            <span className={`assignment-status status-${assignment.status}`}>
              {assignment.status}
            </span>
          </div>
        ))}
        {assignments.length === 0 && (
          <p className="text-muted text-center py-3">No assignments for this shift</p>
        )}
      </div>
    </div>
  )
}

// Report Summary Card
function ReportSummaryCard({ title, value, subtitle }) {
  return (
    <div className="report-summary-card">
      <div className="report-value">{value}</div>
      <div className="report-title">{title}</div>
      <div className="report-subtitle">{subtitle}</div>
    </div>
  )
}

export default SupervisorDashboard
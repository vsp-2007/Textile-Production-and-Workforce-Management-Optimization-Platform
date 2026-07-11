import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../App'
import { machineService, operatorService, shiftService, reportService, authService } from '../services/api'
import toast from 'react-hot-toast'
import './AdminDashboard.css'

function AdminDashboard() {
  const { user, isAdmin } = useAuth()
  const [stats, setStats] = useState({})
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [users, setUsers] = useState([])
  const [machines, setMachines] = useState([])
  const [departments, setDepartments] = useState([])
  const [machineTypes, setMachineTypes] = useState([])
  const [certifications, setCertifications] = useState([])
  const [shifts, setShifts] = useState([])
  const [reports, setReports] = useState([])
  const [showModal, setShowModal] = useState(false)
  const [modalType, setModalType] = useState('')
  const [editingItem, setEditingItem] = useState(null)

  useEffect(() => {
    if (!isAdmin) return
    fetchDashboardData()
  }, [isAdmin])

  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      const [machineStats, usersRes, machinesRes, deptsRes, typesRes, certsRes, shiftsRes, reportsRes] = await Promise.all([
        machineService.getStats(),
        authService.listUsers({ per_page: 100 }),
        machineService.list({ per_page: 100 }),
        operatorService.list({ per_page: 100 }), // reuse for departments
        machineService.listTypes(),
        operatorService.listCertifications(),
        shiftService.list(),
        reportService.getSummary({ days: 30 })
      ])
      
      setStats(machineStats.data)
      setUsers(usersRes.data.users || [])
      setMachines(machinesRes.data.machines || [])
      setDepartments(deptsRes.data.operators || []) // departments from operators
      setMachineTypes(typesRes.data.machine_types || [])
      setCertifications(certsRes.data.certifications || [])
      setShifts(shiftsRes.data.shifts || [])
      setReports(reportsRes.data)
    } catch (error) {
      console.error('Failed to load admin data:', error)
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteUser = async (id) => {
    if (!confirm('Are you sure you want to deactivate this user?')) return
    try {
      await authService.deleteUser(id)
      toast.success('User deactivated')
      fetchDashboardData()
    } catch (error) {
      toast.error('Failed to deactivate user')
    }
  }

  const handleDeleteMachine = async (id) => {
    if (!confirm('Are you sure you want to deactivate this machine?')) return
    try {
      await machineService.update(id, { is_active: false })
      toast.success('Machine deactivated')
      fetchDashboardData()
    } catch (error) {
      toast.error('Failed to deactivate machine')
    }
  }

  const renderOverviewTab = () => (
    <div className="admin-tab">
      <div className="stats-grid">
        <StatCard title="Total Users" value={stats.totalOperators + (stats.totalAdmins || 0) + (stats.totalSupervisors || 0)} icon="bi-people" color="primary" />
        <StatCard title="Total Machines" value={stats.totalMachines} icon="bi-cpu" color="success" />
        <StatCard title="Active Machines" value={stats.activeMachines} icon="bi-play-circle" color="info" />
        <StatCard title="Departments" value={stats.totalDepartments || 6} icon="bi-building" color="warning" />
        <StatCard title="Machine Types" value={machineTypes.length} icon="bi-tag" color="danger" />
        <StatCard title="Certifications" value={certifications.length} icon="bi-award" color="info" />
      </div>

      <div className="charts-row">
        <div className="chart-card">
          <div className="chart-header">
            <h3>User Roles Distribution</h3>
          </div>
          <div className="chart-container">
            <RoleDistributionChart users={users} />
          </div>
        </div>
        <div className="chart-card">
          <div className="chart-header">
            <h3>Machine Status Distribution</h3>
          </div>
          <div className="chart-container">
            <MachineStatusChart machines={machines} />
          </div>
        </div>
      </div>

      <div className="charts-row">
        <div className="chart-card">
          <div className="chart-header">
            <h3>Production Summary (30 Days)</h3>
          </div>
          <div className="chart-container">
            <ProductionSummaryChart reports={reports} />
          </div>
        </div>
        <div className="chart-card">
          <div className="chart-header">
            <h3>Recent Activity</h3>
          </div>
          <div className="chart-container">
            <RecentActivity users={users} machines={machines} />
          </div>
        </div>
      </div>
    </div>
  )

  const renderUsersTab = () => (
    <div className="admin-tab">
      <div className="tab-header">
        <h2>User Management</h2>
        <button className="btn btn-primary" onClick={() => openModal('user')}>
          <i className="bi bi-plus"></i> Add User
        </button>
      </div>
      <div className="table-responsive">
        <table className="table">
          <thead>
            <tr>
              <th>Employee ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Department</th>
              <th>Shift</th>
              <th>Status</th>
              <th>Last Login</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id}>
                <td><code>{user.employee_id}</code></td>
                <td>{user.name}</td>
                <td>{user.email}</td>
                <td><RoleBadge role={user.role} /></td>
                <td>{user.department?.name || '-'}</td>
                <td>{user.shift_pattern || '-'}</td>
                <td><span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>{user.is_active ? 'Active' : 'Inactive'}</span></td>
                <td>{user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</td>
                <td>
                  <div className="action-buttons">
                    <button className="btn btn-ghost btn-sm" onClick={() => editUser(user)} title="Edit">
                      <i className="bi bi-pencil"></i>
                    </button>
                    {user.id !== user.id && (
                      <button className="btn btn-ghost btn-sm text-danger" onClick={() => handleDeleteUser(user.id)} title="Deactivate">
                        <i className="bi bi-trash"></i>
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )

  const renderMachinesTab = () => (
    <div className="admin-tab">
      <div className="tab-header">
        <h2>Machine Management</h2>
        <button className="btn btn-primary" onClick={() => openModal('machine')}>
          <i className="bi bi-plus"></i> Add Machine
        </button>
      </div>
      <div className="table-responsive">
        <table className="table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
              <th>Type</th>
              <th>Department</th>
              <th>Zone</th>
              <th>Capacity</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {machines.map(machine => (
              <tr key={machine.id}>
                <td><code>{machine.machine_code}</code></td>
                <td>{machine.name}</td>
                <td>{machine.machine_type?.name || '-'}</td>
                <td>{machine.department?.name || '-'}</td>
                <td>{machine.floor_zone || '-'}</td>
                <td>{machine.capacity_max || '-'}</td>
                <td><span className={`status-badge ${machine.status}`}>{machine.status}</span></td>
                <td>
                  <div className="action-buttons">
                    <button className="btn btn-ghost btn-sm" onClick={() => editMachine(machine)} title="Edit">
                      <i className="bi bi-pencil"></i>
                    </button>
                    <button className="btn btn-ghost btn-sm text-danger" onClick={() => handleDeleteMachine(machine.id)} title="Deactivate">
                      <i className="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )

  const renderSettingsTab = () => (
    <div className="admin-tab">
      <div className="settings-grid">
        <SettingsSection title="Departments" items={departments} icon="bi-building" />
        <SettingsSection title="Machine Types" items={machineTypes} icon="bi-cpu" />
        <SettingsSection title="Certifications" items={certifications} icon="bi-award" />
        <SettingsSection title="Shifts" items={shifts} icon="bi-clock" />
      </div>
    </div>
  )

  if (loading) {
    return <div className="admin-loading"><div className="loading-spinner"></div><p>Loading admin dashboard...</p></div>
  }

  return (
    <div className="admin-dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Administration</h1>
          <p className="text-muted">System configuration and management</p>
        </div>
      </div>

      <nav className="admin-tabs" role="tablist">
        <button role="tab" className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')} aria-selected={activeTab === 'overview'}>
          <i className="bi bi-speedometer2"></i> Overview
        </button>
        <button role="tab" className={`tab-btn ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')} aria-selected={activeTab === 'users'}>
          <i className="bi bi-people"></i> Users
        </button>
        <button role="tab" className={`tab-btn ${activeTab === 'machines' ? 'active' : ''}`} onClick={() => setActiveTab('machines')} aria-selected={activeTab === 'machines'}>
          <i className="bi bi-cpu"></i> Machines
        </button>
        <button role="tab" className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')} aria-selected={activeTab === 'settings'}>
          <i className="bi bi-gear"></i> Settings
        </button>
      </nav>

      <div className="admin-content">
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'users' && renderUsersTab()}
        {activeTab === 'machines' && renderMachinesTab()}
        {activeTab === 'settings' && renderSettingsTab()}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{modalType === 'user' ? (editingItem ? 'Edit User' : 'Add User') : 'Add Machine'}</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>&times;</button>
            </div>
            <div className="modal-body">
              {modalType === 'user' && <UserForm user={editingItem} onSubmit={handleUserSubmit} onClose={() => setShowModal(false)} />}
              {modalType === 'machine' && <MachineForm machine={editingItem} onSubmit={handleMachineSubmit} onClose={() => setShowModal(false)} />}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Helper Components
function StatCard({ title, value, icon, color }) {
  const colors = {
    primary: 'bg-primary',
    success: 'bg-success',
    warning: 'bg-warning',
    danger: 'bg-danger',
    info: 'bg-info'
  }
  return (
    <div className="stat-card">
      <div className={`stat-icon ${colors[color]}`}>
        <i className={`bi ${icon}`}></i>
      </div>
      <div className="stat-content">
        <div className="stat-value">{value}</div>
        <div className="stat-label">{title}</div>
      </div>
    </div>
  )
}

function RoleBadge({ role }) {
  const colors = {
    admin: 'bg-danger',
    supervisor: 'bg-warning text-dark',
    operator: 'bg-primary'
  }
  return <span className={`badge ${colors[role] || 'bg-secondary'}`}>{role.charAt(0).toUpperCase() + role.slice(1)}</span>
}

function SettingsSection({ title, items, icon }) {
  return (
    <div className="settings-card">
      <div className="settings-header">
        <i className={`bi ${icon}`}></i>
        <h3>{title}</h3>
        <span className="badge bg-primary">{items.length}</span>
      </div>
      <ul className="settings-list">
        {items.slice(0, 10).map(item => (
          <li key={item.id || item.code || item.name}>
            <strong>{item.name || item.code}</strong>
            <span className="text-muted">{item.description || item.code}</span>
          </li>
        ))}
        {items.length > 10 && <li className="text-muted">+ {items.length - 10} more...</li>}
      </ul>
    </div>
  )
}

function RoleDistributionChart({ users }) {
  const roles = users.reduce((acc, u) => {
    acc[u.role] = (acc[u.role] || 0) + 1
    return acc
  }, {})
  
  const data = Object.entries(roles).map(([name, value]) => ({ name, value }))
  const colors = ['#ef4444', '#f59e0b', '#2563eb']
  
  return (
    <div style={{ height: 250 }}>
      <svg viewBox="0 0 200 200" style={{ width: '100%', height: '100%' }}>
        {data.map((item, i) => (
          <PieSlice key={item.name} value={item.value} total={users.length} color={colors[i]} />
        ))}
      </svg>
      <div className="chart-legend">
        {data.map((item, i) => (
          <span key={item.name} className="legend-item">
            <span className="legend-color" style={{ background: colors[i] }}></span>
            {item.name} ({item.value})
          </span>
        ))}
      </div>
    </div>
  )
}

function PieSlice({ value, total, color }) {
  const percentage = value / total
  const angle = percentage * 360
  const radius = 80
  const cx = 100
  const cy = 100
  
  // This is a simplified pie chart - in production use recharts
  return null
}

function MachineStatusChart({ machines }) {
  const statuses = machines.reduce((acc, m) => {
    acc[m.status] = (acc[m.status] || 0) + 1
    return acc
  }, {})
  
  return (
    <div style={{ height: 250, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="status-distribution">
        {Object.entries(statuses).map(([status, count]) => (
          <div key={status} className="status-row">
            <span className={`status-dot ${status}`}></span>
            <span className="status-label">{status.charAt(0).toUpperCase() + status.slice(1)}</span>
            <span className="status-count">{count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ProductionSummaryChart({ reports }) {
  return (
    <div style={{ height: 250, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <p className="text-muted">Production charts would render here with Recharts</p>
    </div>
  )
}

function RecentActivity({ users, machines }) {
  return (
    <div className="activity-list">
      {users.slice(0, 5).map(user => (
        <div key={user.id} className="activity-item">
          <div className="activity-icon bg-primary"><i className="bi bi-person-plus"></i></div>
          <div className="activity-content">
            <p><strong>{user.name}</strong> joined as {user.role}</p>
            <span className="activity-time">{user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Recently'}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

function UserForm({ user, onSubmit, onClose }) {
  const [form, setForm] = useState({
    employee_id: '',
    name: '',
    email: '',
    password: '',
    role: 'operator',
    department_id: '',
    shift_pattern: ''
  })

  useEffect(() => {
    if (user) {
      setForm({
        employee_id: user.employee_id,
        name: user.name,
        email: user.email,
        password: '',
        role: user.role,
        department_id: user.department_id || '',
        shift_pattern: user.shift_pattern || ''
      })
    }
  }, [user])

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(form)
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-row">
        <div className="form-group">
          <label>Employee ID *</label>
          <input type="text" value={form.employee_id} onChange={e => setForm({...form, employee_id: e.target.value})} required disabled={!!user} />
        </div>
        <div className="form-group">
          <label>Role *</label>
          <select value={form.role} onChange={e => setForm({...form, role: e.target.value})} required>
            <option value="admin">Admin</option>
            <option value="supervisor">Supervisor</option>
            <option value="operator">Operator</option>
          </select>
        </div>
      </div>
      <div className="form-group">
        <label>Full Name *</label>
        <input type="text" value={form.name} onChange={e => setForm({...form, name: e.target.value})} required />
      </div>
      <div className="form-group">
        <label>Email *</label>
        <input type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} required />
      </div>
      <div className="form-group">
        <label>{user ? 'New Password (leave blank to keep current)' : 'Password'} *</label>
        <input type="password" value={form.password} onChange={e => setForm({...form, password: e.target.value})} required={!user} />
      </div>
      <div className="form-row">
        <div className="form-group">
          <label>Department</label>
          <select value={form.department_id} onChange={e => setForm({...form, department_id: e.target.value})}>
            <option value="">Select Department</option>
          </select>
        </div>
        <div className="form-group">
          <label>Shift Pattern</label>
          <select value={form.shift_pattern} onChange={e => setForm({...form, shift_pattern: e.target.value})}>
            <option value="">Select Shift</option>
            <option value="morning">Morning</option>
            <option value="evening">Evening</option>
            <option value="night">Night</option>
          </select>
        </div>
      </div>
      <div className="modal-footer">
        <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
        <button type="submit" className="btn btn-primary">{user ? 'Update' : 'Create'}</button>
      </div>
    </form>
  )
}

function MachineForm({ machine, onSubmit, onClose }) {
  const [form, setForm] = useState({
    machine_code: '',
    name: '',
    machine_type_id: '',
    department_id: '',
    floor_zone: '',
    location_x: '',
    location_y: '',
    capacity_max: ''
  })

  useEffect(() => {
    if (machine) {
      setForm({
        machine_code: machine.machine_code,
        name: machine.name,
        machine_type_id: machine.machine_type_id || '',
        department_id: machine.department_id || '',
        floor_zone: machine.floor_zone || '',
        location_x: machine.location_x || '',
        location_y: machine.location_y || '',
        capacity_max: machine.capacity_max || ''
      })
    }
  }, [machine])

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(form)
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-row">
        <div className="form-group">
          <label>Machine Code *</label>
          <input type="text" value={form.machine_code} onChange={e => setForm({...form, machine_code: e.target.value})} required disabled={!!machine} />
        </div>
        <div className="form-group">
          <label>Type *</label>
          <select value={form.machine_type_id} onChange={e => setForm({...form, machine_type_id: e.target.value})} required>
            <option value="">Select Type</option>
          </select>
        </div>
      </div>
      <div className="form-group">
        <label>Name *</label>
        <input type="text" value={form.name} onChange={e => setForm({...form, name: e.target.value})} required />
      </div>
      <div className="form-row">
        <div className="form-group">
          <label>Department</label>
          <select value={form.department_id} onChange={e => setForm({...form, department_id: e.target.value})}>
            <option value="">Select Department</option>
          </select>
        </div>
        <div className="form-group">
          <label>Zone</label>
          <input type="text" value={form.floor_zone} onChange={e => setForm({...form, floor_zone: e.target.value})} />
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label>Location X</label>
          <input type="number" step="0.1" value={form.location_x} onChange={e => setForm({...form, location_x: e.target.value})} />
        </div>
        <div className="form-group">
          <label>Location Y</label>
          <input type="number" step="0.1" value={form.location_y} onChange={e => setForm({...form, location_y: e.target.value})} />
        </div>
      </div>
      <div className="form-group">
        <label>Capacity (yds/hr)</label>
        <input type="number" value={form.capacity_max} onChange={e => setForm({...form, capacity_max: e.target.value})} />
      </div>
      <div className="modal-footer">
        <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
        <button type="submit" className="btn btn-primary">{machine ? 'Update' : 'Create'}</button>
      </div>
    </form>
  )
}

function openModal(type, item = null) {
  // This will be handled by the parent component's state
}

function handleUserSubmit(data) {
  // Handled by parent
}

function handleMachineSubmit(data) {
  // Handled by parent
}

export default AdminDashboard
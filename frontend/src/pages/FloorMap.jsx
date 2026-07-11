import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth, useSocket } from '../App'
import { machineService } from '../services/api'
import toast from 'react-hot-toast'
import './FloorMap.css'

function FloorMap() {
  const { isSupervisor } = useAuth()
  const { socket, on, off } = useSocket()
  const navigate = useNavigate()
  
  const [machines, setMachines] = useState([])
  const [zones, setZones] = useState({})
  const [selectedMachine, setSelectedMachine] = useState(null)
  const [viewMode, setViewMode] = useState('zones') // 'zones' or 'list'
  const [loading, setLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const svgRef = useRef(null)
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 })
  const [isPanning, setIsPanning] = useState(false)
  const [panStart, setPanStart] = useState({ x: 0, y: 0 })

  useEffect(() => {
    fetchFloorMap()
    setupSocketListeners()
    return () => cleanupSocketListeners()
  }, [])

  const setupSocketListeners = () => {
    if (!socket) return
    socket.on('machine_status_update', handleMachineUpdate)
    socket.on('machine_telemetry', handleTelemetryUpdate)
  }

  const cleanupSocketListeners = () => {
    if (!socket) return
    socket.off('machine_status_update', handleMachineUpdate)
    socket.off('machine_telemetry', handleTelemetryUpdate)
  }

  const handleMachineUpdate = (data) => {
    setMachines(prev => prev.map(m => 
      m.id === data.machine_id ? { ...m, status: data.status, latest_telemetry: data.telemetry } : m
    ))
  }

  const handleTelemetryUpdate = (data) => {
    setMachines(prev => prev.map(m => 
      m.id === data.machine_id ? { ...m, latest_telemetry: data.telemetry } : m
    ))
  }

  const fetchFloorMap = async () => {
    try {
      const res = await machineService.getFloorMap()
      const machinesData = res.data.machines || []
      setMachines(machinesData)
      
      // Group by zone
      const zoneMap = {}
      machinesData.forEach(machine => {
        const zone = machine.floor_zone || 'General'
        if (!zoneMap[zone]) zoneMap[zone] = []
        zoneMap[zone].push(machine)
      })
      setZones(zoneMap)
    } catch (error) {
      toast.error('Failed to load floor map')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleMachineClick = (machine, e) => {
    e.stopPropagation()
    setSelectedMachine(machine)
  }

  const handleWheel = (e) => {
    e.preventDefault()
    const scaleFactor = e.deltaY > 0 ? 0.9 : 1.1
    const newScale = Math.min(Math.max(transform.scale * scaleFactor, 0.3), 3)
    
    const rect = svgRef.current?.getBoundingClientRect()
    if (!rect) return
    
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top
    
    const newX = mouseX - (mouseX - transform.x) * (newScale / transform.scale)
    const newY = mouseY - (mouseY - transform.y) * (newScale / transform.scale)
    
    setTransform({ x: newX, y: newY, scale: newScale })
  }

  const handleMouseDown = (e) => {
    if (e.target === svgRef.current || e.target.classList.contains('floor-map-bg')) {
      setIsPanning(true)
      setPanStart({ x: e.clientX - transform.x, y: e.clientY - transform.y })
      e.preventDefault()
    }
  }

  const handleMouseMove = (e) => {
    if (!isPanning) return
    setTransform(prev => ({
      ...prev,
      x: e.clientX - panStart.x,
      y: e.clientY - panStart.y
    }))
  }

  const handleMouseUp = () => {
    setIsPanning(false)
  }

  const resetView = () => {
    setTransform({ x: 0, y: 0, scale: 1 })
  }

  const filteredMachines = machines.filter(machine => {
    const matchesStatus = filterStatus === 'all' || machine.status === filterStatus
    const matchesSearch = searchQuery === '' || 
      machine.machine_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      machine.name.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesStatus && matchesSearch
  })

  const statusColors = {
    active: '#10b981',
    idle: '#f59e0b',
    maintenance: '#06b6d4',
    fault: '#ef4444',
    offline: '#64748b',
    disconnected: '#9ca3af'
  }

  const getMachineColor = (status) => statusColors[status] || '#64748b'

  if (loading) {
    return (
      <div className="floor-map-loading">
        <div className="loading-spinner"></div>
        <p>Loading floor map...</p>
      </div>
    )
  }

  return (
    <div className="floor-map-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>Interactive Floor Map</h1>
          <p className="text-muted">Real-time machine monitoring across all zones</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={resetView}>
            <i className="bi bi-arrows-fullscreen"></i> Reset View
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/scheduler')}>
            <i className="bi bi-calendar-plus"></i> Open Scheduler
          </button>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="stats-bar">
        <div className="stat-item">
          <span className="stat-value">{machines.length}</span>
          <span className="stat-label">Total Machines</span>
        </div>
        <div className="stat-item">
          <span className="stat-value" style={{color: '#10b981'}}>{machines.filter(m => m.status === 'active').length}</span>
          <span className="stat-label">Active</span>
        </div>
        <div className="stat-item">
          <span className="stat-value" style={{color: '#f59e0b'}}>{machines.filter(m => m.status === 'idle').length}</span>
          <span className="stat-label">Idle</span>
        </div>
        <div className="stat-item">
          <span className="stat-value" style={{color: '#ef4444'}}>{machines.filter(m => m.status === 'fault').length}</span>
          <span className="stat-label">Faults</span>
        </div>
        <div className="stat-item">
          <span className="stat-value" style={{color: '#06b6d4'}}>{machines.filter(m => m.status === 'maintenance').length}</span>
          <span className="stat-label">Maintenance</span>
        </div>
      </div>

      {/* Controls */}
      <div className="map-controls">
        <div className="controls-left">
          <div className="search-box">
            <i className="bi bi-search"></i>
            <input
              type="text"
              placeholder="Search machines by code or name..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
          </div>
          <select 
            className="filter-select"
            value={filterStatus}
            onChange={e => setFilterStatus(e.target.value)}
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="idle">Idle</option>
            <option value="fault">Fault</option>
            <option value="maintenance">Maintenance</option>
            <option value="offline">Offline</option>
          </select>
          <div className="view-toggle">
            <button 
              className={viewMode === 'zones' ? 'active' : ''}
              onClick={() => setViewMode('zones')}
              title="Zone View"
            >
              <i className="bi bi-grid-3x3-gap"></i>
            </button>
            <button 
              className={viewMode === 'list' ? 'active' : ''}
              onClick={() => setViewMode('list')}
              title="List View"
            >
              <i className="bi bi-list"></i>
            </button>
          </div>
        </div>
        <div className="controls-right">
          <div className="zoom-controls">
            <button className="btn btn-ghost btn-sm" onClick={() => setTransform(p => ({...p, scale: Math.min(p.scale * 1.2, 3)}))} title="Zoom In">
              <i className="bi bi-zoom-in"></i>
            </button>
            <button className="btn btn-ghost btn-sm" onClick={() => setTransform(p => ({...p, scale: Math.max(p.scale / 1.2, 0.3)}))} title="Zoom Out">
              <i className="bi bi-zoom-out"></i>
            </button>
            <span className="zoom-level">{Math.round(transform.scale * 100)}%</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="map-content">
        {/* Zone View - Interactive SVG Map */}
        {viewMode === 'zones' && (
          <div className="map-viewport" onWheel={handleWheel} onMouseDown={handleMouseDown} onMouseMove={handleMouseMove} onMouseUp={handleMouseUp} onMouseLeave={handleMouseUp}>
            <svg 
              ref={svgRef}
              className="floor-map-svg"
              style={{ transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`, transformOrigin: '0 0' }}
              viewBox="0 0 1200 800"
              preserveAspectRatio="xMidYMid meet"
            >
              {/* Background Grid */}
              <defs>
                <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
                  <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#e2e8f0" strokeWidth="0.5"/>
                </pattern>
              </defs>
              <rect className="floor-map-bg" width="1200" height="800" fill="url(#grid)" />
              
              {/* Zone Areas */}
              {Object.entries(zones).map(([zoneName, zoneMachines], zoneIndex) => {
                // Calculate bounding box for zone
                const positions = zoneMachines
                  .filter(m => m.location_x != null && m.location_y != null)
                  .map(m => ({ x: m.location_x, y: m.location_y }))
                
                if (positions.length === 0) return null
                
                const minX = Math.min(...positions.map(p => p.x)) - 50
                const minY = Math.min(...positions.map(p => p.y)) - 50
                const maxX = Math.max(...positions.map(p => p.x)) + 50
                const maxY = Math.max(...positions.map(p => p.y)) + 50
                
                const zoneColors = ['rgba(37, 99, 235, 0.05)', 'rgba(16, 185, 129, 0.05)', 'rgba(245, 158, 11, 0.05)', 'rgba(239, 68, 68, 0.05)', 'rgba(6, 182, 212, 0.05)']
                const zoneBorderColors = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#06b6d4']
                
                return (
                  <g key={zoneName}>
                    <rect
                      x={minX}
                      y={minY}
                      width={maxX - minX}
                      height={maxY - minY}
                      fill={zoneColors[zoneIndex % zoneColors.length]}
                      stroke={zoneBorderColors[zoneIndex % zoneBorderColors.length]}
                      strokeWidth="2"
                      strokeDasharray="5,5"
                      rx="8"
                    />
                    <text
                      x={minX + 15}
                      y={minY + 25}
                      fontSize="14"
                      fontWeight="600"
                      fill={zoneBorderColors[zoneIndex % zoneBorderColors.length]}
                    >
                      Zone {zoneName}
                    </text>
                  </g>
                )
              })}
              
              {/* Machines */}
              {filteredMachines.map(machine => {
                if (machine.location_x == null || machine.location_y == null) return null
                
                const color = getMachineColor(machine.status)
                const isSelected = selectedMachine?.id === machine.id
                const hasOperator = !!machine.current_operator
                
                return (
                  <g 
                    key={machine.id}
                    className={`machine-node ${isSelected ? 'selected' : ''} ${machine.status}`}
                    onClick={() => handleMachineClick(machine, { stopPropagation: () => {} })}
                    style={{ cursor: 'pointer' }}
                  >
                    {/* Machine Circle */}
                    <circle
                      cx={machine.location_x}
                      cy={machine.location_y}
                      r={isSelected ? 20 : 16}
                      fill={color}
                      stroke={isSelected ? '#fff' : '#fff'}
                      strokeWidth={isSelected ? 3 : 2}
                      filter="drop-shadow(0 2px 4px rgba(0,0,0,0.1))"
                      transition="all 0.2s"
                    />
                    
                    {/* Status Ring */}
                    <circle
                      cx={machine.location_x}
                      cy={machine.location_y}
                      r={24}
                      fill="none"
                      stroke={color}
                      strokeWidth={2}
                      strokeDasharray={machine.status === 'active' ? '10 5' : 'none'}
                      style={{ animation: machine.status === 'active' ? 'dash 1s linear infinite' : 'none' }}
                    />
                    
                    {/* Machine Code Label */}
                    <text
                      x={machine.location_x}
                      y={machine.location_y - 30}
                      textAnchor="middle"
                      fontSize="11"
                      fontWeight="600"
                      fill="#1e293b"
                      style={{ pointerEvents: 'none', userSelect: 'none' }}
                    >
                      {machine.machine_code}
                    </text>
                    
                    {/* Operator Indicator */}
                    {hasOperator && (
                      <circle
                        cx={machine.location_x + 12}
                        cy={machine.location_y - 12}
                        r={8}
                        fill="#10b981"
                        stroke="#fff"
                        strokeWidth={2}
                      />
                    )}
                    
                    {/* Selection Ring */}
                    {isSelected && (
                      <circle
                        cx={machine.location_x}
                        cy={machine.location_y}
                        r={28}
                        fill="none"
                        stroke="#2563eb"
                        strokeWidth={2}
                        strokeDasharray="5,5"
                      />
                    )}
                  </g>
                )
              })}
            </svg>
            
            {/* Legend */}
            <div className="map-legend">
              <div className="legend-title">Machine Status</div>
              <div className="legend-items">
                {Object.entries(statusColors).map(([status, color]) => (
                  <div key={status} className="legend-item">
                    <span className="legend-dot" style={{ background: color }}></span>
                    <span className="legend-text">{status.charAt(0).toUpperCase() + status.slice(1)}</span>
                    <span className="legend-count">({machines.filter(m => m.status === status).length})</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        
        {/* List View */}
        {viewMode === 'list' && (
          <div className="list-view">
            <div className="list-header">
              <h3>Machine List ({filteredMachines.length} machines)</h3>
            </div>
            <div className="machines-table-container">
              <table className="machines-table">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Zone</th>
                    <th>Status</th>
                    <th>Operator</th>
                    <th>Output</th>
                    <th>RPM</th>
                    <th>Temp</th>
                    <th>Last Update</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredMachines.map(machine => (
                    <tr 
                      key={machine.id} 
                      onClick={() => handleMachineClick(machine, { stopPropagation: () => {} })}
                      className={selectedMachine?.id === machine.id ? 'selected' : ''}
                    >
                      <td><strong>{machine.machine_code}</strong></td>
                      <td>{machine.name}</td>
                      <td>{machine.machine_type?.name || 'N/A'}</td>
                      <td>{machine.floor_zone || 'General'}</td>
                      <td>
                        <span className={`status-badge status-${machine.status}`}>
                          <span className="status-dot"></span>
                          {machine.status.charAt(0).toUpperCase() + machine.status.slice(1)}
                        </span>
                      </td>
                      <td>{machine.current_operator?.name || '<span class="text-muted">Unassigned</span>'}</td>
                      <td>{machine.latest_telemetry?.output_count || 0} yds</td>
                      <td>{machine.latest_telemetry?.rpm || 0}</td>
                      <td>{machine.latest_telemetry?.temperature || 0}°C</td>
                      <td className="text-muted">
                        {machine.last_telemetry_at ? new Date(machine.last_telemetry_at).toLocaleTimeString() : 'Never'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Machine Detail Panel */}
        {selectedMachine && (
          <div className="machine-detail-panel">
            <div className="panel-header">
              <div>
                <span className="machine-code">{selectedMachine.machine_code}</span>
                <h3>{selectedMachine.name}</h3>
              </div>
              <button className="btn btn-ghost btn-sm" onClick={() => setSelectedMachine(null)}>
                <i className="bi bi-x"></i>
              </button>
            </div>
            
            <div className="panel-body">
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">Type</span>
                  <span className="detail-value">{selectedMachine.machine_type?.name || 'N/A'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Zone</span>
                  <span className="detail-value">{selectedMachine.floor_zone || 'General'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Status</span>
                  <span className="detail-value">
                    <span className={`status-badge status-${selectedMachine.status}`}>
                      <span className="status-dot"></span>
                      {selectedMachine.status.charAt(0).toUpperCase() + selectedMachine.status.slice(1)}
                    </span>
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Capacity</span>
                  <span className="detail-value">{selectedMachine.capacity_max || 'N/A'} yds/hr</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Operator</span>
                  <span className="detail-value">
                    {selectedMachine.current_operator ? (
                      <>
                        {selectedMachine.current_operator.name}
                        <span className="badge bg-success ms-2">{selectedMachine.current_operator.role}</span>
                      </>
                    ) : (
                      <span className="text-muted">Unassigned</span>
                    )}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Last Maintenance</span>
                  <span className="detail-value">
                    {selectedMachine.last_maintenance ? new Date(selectedMachine.last_maintenance).toLocaleDateString() : 'Never'}
                  </span>
                </div>
              </div>
              
              {/* Telemetry */}
              {selectedMachine.latest_telemetry && (
                <div className="telemetry-section">
                  <h4>Live Telemetry</h4>
                  <div className="telemetry-grid">
                    <TelemetryCard label="Output" value={`${selectedMachine.latest_telemetry.output_count || 0} yds`} icon="bi-graph-up" color="primary" />
                    <TelemetryCard label="RPM" value={selectedMachine.latest_telemetry.rpm || 0} icon="bi-speedometer" color="info" />
                    <TelemetryCard label="Temperature" value={`${selectedMachine.latest_telemetry.temperature || 0}°C`} icon="bi-thermometer" color="warning" />
                    <TelemetryCard label="Vibration" value={`${selectedMachine.latest_telemetry.vibration || 0} mm/s`} icon="bi-activity" color="danger" />
                    <TelemetryCard label="Status" value={selectedMachine.latest_telemetry.status || 'N/A'} icon="bi-broadcast" color="success" />
                    <TelemetryCard label="Error Code" value={selectedMachine.latest_telemetry.error_code || 'None'} icon="bi-exclamation-triangle" color={selectedMachine.latest_telemetry.error_code ? 'danger' : 'success'} />
                  </div>
                </div>
              )}
              
              {/* Actions */}
              <div className="panel-actions">
                <button className="btn btn-outline-primary" onClick={() => navigate(`/machines/${selectedMachine.id}`)}>
                  <i className="bi bi-eye"></i> View Details
                </button>
                {isSupervisor && (
                  <>
                    <button className="btn btn-outline-warning" onClick={() => navigate(`/scheduler?machine=${selectedMachine.id}`)}>
                      <i className="bi bi-calendar-plus"></i> Assign Shift
                    </button>
                    <button className="btn btn-outline-danger" onClick={() => handleRequestMaintenance(selectedMachine.id)}>
                      <i className="bi bi-tools"></i> Request Maintenance
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function TelemetryCard({ label, value, icon, color }) {
  const colors = {
    primary: '#2563eb',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4'
  }
  
  return (
    <div className="telemetry-card">
      <div className="telemetry-icon" style={{ background: `${colors[color]}15`, color: colors[color] }}>
        <i className={`bi ${icon}`}></i>
      </div>
      <div className="telemetry-content">
        <span className="telemetry-label">{label}</span>
        <span className="telemetry-value">{value}</span>
      </div>
    </div>
  )
}

export default FloorMap
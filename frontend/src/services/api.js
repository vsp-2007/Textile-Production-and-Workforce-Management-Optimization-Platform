import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true
})

// Request interceptor for auth
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {}, {
            headers: { Authorization: `Bearer ${refreshToken}` },
            withCredentials: true
          })
          
          const { access_token } = response.data
          localStorage.setItem('access_token', access_token)
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          
          return api(originalRequest)
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }
    
    return Promise.reject(error)
  }
)

export const authService = {
  login: (employeeId, password) => api.post('/auth/login', { employee_id: employeeId, password }),
  logout: () => api.post('/auth/logout'),
  refresh: () => api.post('/auth/refresh'),
  getMe: () => api.get('/auth/me'),
  changePassword: (currentPassword, newPassword) => api.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword }),
  validateSession: () => api.get('/auth/validate-session'),
  createUser: (data) => api.post('/auth/users', data),
  listUsers: (params) => api.get('/auth/users', { params }),
  updateUser: (id, data) => api.put(`/auth/users/${id}`, data),
  deleteUser: (id) => api.delete(`/auth/users/${id}`)
}

export const machineService = {
  list: (params) => api.get('/machines', { params }),
  get: (id) => api.get(`/machines/${id}`),
  create: (data) => api.post('/machines', data),
  update: (id, data) => api.put(`/machines/${id}`, data),
  updateStatus: (id, data) => api.put(`/machines/${id}/status`, data),
  getTelemetry: (id, params) => api.get(`/machines/${id}/telemetry`, { params }),
  getDowntime: (id, params) => api.get(`/machines/${id}/downtime`, { params }),
  listTypes: () => api.get('/machines/types'),
  createType: (data) => api.post('/machines/types', data),
  getFloorMap: () => api.get('/machines/floor-map'),
  getStats: () => api.get('/machines/stats/summary')
}

export const operatorService = {
  list: (params) => api.get('/operators', { params }),
  get: (id) => api.get(`/operators/${id}`),
  getSchedule: (id, params) => api.get(`/operators/${id}/schedule`, { params }),
  addCertification: (id, data) => api.post(`/operators/${id}/certifications`, data),
  updateCertification: (id, certId, data) => api.put(`/operators/${id}/certifications/${certId}`, data),
  revokeCertification: (id, certId) => api.delete(`/operators/${id}/certifications/${certId}`),
  listCertifications: () => api.get('/operators/certifications'),
  createCertification: (data) => api.post('/operators/certifications', data),
  getAvailableForMachine: (machineId, params) => api.get(`/operators/available-for-machine/${machineId}`, { params })
}

export const shiftService = {
  list: () => api.get('/shifts'),
  create: (data) => api.post('/shifts', data),
  get: (id) => api.get(`/shifts/${id}`),
  getAssignments: (id) => api.get(`/shifts/${id}/assignments`),
  createAssignment: (shiftId, data) => api.post(`/shifts/${shiftId}/assignments`, data),
  updateAssignment: (id, data) => api.put(`/shifts/assignments/${id}`, data),
  deleteAssignment: (id) => api.delete(`/shifts/assignments/${id}`),
  validateAssignment: (data) => api.post('/shifts/assignments/validate', data),
  getUnassignedMachines: (shiftId) => api.get(`/shifts/${shiftId}/unassigned-machines`),
  getAvailableOperators: (shiftId, params) => api.get(`/shifts/${shiftId}/available-operators`, { params }),
  getTodayShifts: () => api.get('/shifts/today'),
  startShift: (shiftId) => api.post(`/shifts/${shiftId}/start`),
  endShift: (shiftId) => api.post(`/shifts/${shiftId}/end`)
}

export const reallocationService = {
  recommend: (data) => api.post('/reallocation/recommend', data),
  approve: (data) => api.post('/reallocation/approve', data),
  getHistory: (params) => api.get('/reallocation/history', { params }),
  autoSuggest: (shiftId) => api.post('/reallocation/auto-suggest', { shift_id: shiftId })
}

export const reportService = {
  getDaily: (params) => api.get('/reports/daily', { params }),
  getShift: (shiftId, params) => api.get(`/reports/shift/${shiftId}`, { params }),
  getMachine: (machineId, params) => api.get(`/reports/machine/${machineId}`, { params }),
  getOperator: (operatorId, params) => api.get(`/reports/operator/${operatorId}`, { params }),
  export: (data) => api.post('/reports/export', data, { responseType: 'blob' }),
  getMachineOEE: (machineId, params) => api.get(`/reports/oee/${machineId}`, { params }),
  getSummary: (params) => api.get('/reports/summary', { params })
}

export const alertService = {
  list: (params) => api.get('/alerts', { params }),
  getUnreadCount: () => api.get('/alerts/unread-count'),
  acknowledge: (id) => api.put(`/alerts/${id}/acknowledge`),
  acknowledgeAll: (data) => api.put('/alerts/acknowledge-all', data),
  listTypes: () => api.get('/alerts/types')
}

export default api
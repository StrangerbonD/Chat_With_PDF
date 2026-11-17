import axios from 'axios'

let accessToken = null
let isRefreshing = false
let failedQueue = []

function processQueue(error, token = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

export function setAccessToken(token) {
  accessToken = token
}

export function getAccessToken() {
  return accessToken
}

const rawBaseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const baseURL = String(rawBaseURL).trim().replace(/\/+$/, '')

const api = axios.create({
  baseURL,
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers['Authorization'] = `Bearer ${accessToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Normalize validation errors (422 array of objects) to a single readable string
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail
      if (Array.isArray(detail)) {
        error.response.data.detail = detail
          .map((item) =>
            item.msg
              ? item.msg.replace(/^Value error,\s*/i, '')
              : typeof item === 'string'
              ? item
              : JSON.stringify(item)
          )
          .join('. ')
      } else if (typeof detail === 'object') {
        error.response.data.detail = detail.msg || JSON.stringify(detail)
      }
    }

    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (
        originalRequest.url?.includes('/api/auth/login') ||
        originalRequest.url?.includes('/api/auth/refresh')
      ) {
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers['Authorization'] = `Bearer ${token}`
            return api(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const response = await api.post('/api/auth/refresh')
        const newToken = response.data.access_token
        setAccessToken(newToken)
        processQueue(null, newToken)
        originalRequest.headers['Authorization'] = `Bearer ${newToken}`
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        window.dispatchEvent(new Event('auth:logout'))
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default api

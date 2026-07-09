import axios from 'axios'

const client = axios.create({ baseURL: '/api/v1' })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// A 401 from these endpoints means "wrong credentials" or "no session to
// refresh", not "session expired mid-use" -- letting the retry-refresh
// logic below run for them was causing a real bug: a wrong password
// produced a 401, which triggered a refresh attempt with no valid refresh
// token, which failed and force-reloaded the page to /login before the
// user ever saw the "Invalid username or password" toast Login.jsx was
// about to show. The reload silently ate the error message.
const AUTH_ENDPOINTS = ['/auth/login/', '/auth/register/', '/auth/token/refresh/']

client.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config
    const isAuthEndpoint = AUTH_ENDPOINTS.some((path) => original.url?.includes(path))
    if (err.response?.status === 401 && !original._retry && !isAuthEndpoint) {
      original._retry = true
      try {
        const refresh = localStorage.getItem('refresh_token')
        const { data } = await axios.post('/api/v1/auth/token/refresh/', { refresh })
        localStorage.setItem('access_token', data.access)
        original.headers.Authorization = `Bearer ${data.access}`
        return client(original)
      } catch {
        localStorage.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default client

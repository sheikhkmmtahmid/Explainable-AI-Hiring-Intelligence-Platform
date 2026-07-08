import { createContext, useContext, useEffect, useState } from 'react'
import { getMe, login as apiLogin, logout as apiLogout } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      getMe()
        .then(({ data }) => setUser(data))
        .catch(() => localStorage.clear())
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (username, password) => {
    const { data } = await apiLogin(username, password)
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    setUser(data.user)
    return data
  }

  const logout = async () => {
    const refresh = localStorage.getItem('refresh_token')
    localStorage.clear()
    setUser(null)
    if (refresh) {
      apiLogout(refresh).catch(() => {})
    }
  }

  // Re-fetch the current user -- used after something server-side changes
  // that /me reflects but our cached user object doesn't yet, e.g. editing
  // the organization's country on the Billing page.
  const refreshUser = async () => {
    const { data } = await getMe()
    setUser(data)
    return data
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)

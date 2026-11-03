import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authAPI } from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)  // true on initial load

  // ─── Restore session on mount; a local PAET logs straight in ──────────────
  useEffect(() => {
    const localLogin = () => authAPI.localLogin()
      .then(({ data }) => {
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        return authAPI.getMe()
      })
      .then(({ data }) => setUser(data))
      .catch(() => {})

    const token = localStorage.getItem('access_token')
    const restore = token
      ? authAPI.getMe().then(({ data }) => setUser(data)).catch(() => { localStorage.clear(); return localLogin() })
      : localLogin()
    restore.finally(() => setLoading(false))
  }, [])

  // ─── Register ─────────────────────────────────────────────────────────────
  const register = useCallback(async (formData) => {
    const { data } = await authAPI.register(formData)
    return data  // returns user profile; then redirect to login
  }, [])

  // ─── Login step 1: password check → returns {otp_token, email_hint} ─────
  const loginStep1 = useCallback(async (email, password) => {
    const { data } = await authAPI.login({ email, password })
    // data = { otp_token, email_hint, message }
    return data
  }, [])

  // ─── Login step 2: OTP verify → stores tokens, fetches profile ───────────
  const loginStep2 = useCallback(async (otp_token, otp) => {
    const { data } = await authAPI.verifyOtp({ otp_token, otp })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    const { data: profile } = await authAPI.getMe()
    setUser(profile)
    return profile
  }, [])

  // ─── Dev login: no password, no OTP. Backend 404s unless it is enabled ────
  const devLogin = useCallback(async () => {
    const { data } = await authAPI.devLogin()
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    const { data: profile } = await authAPI.getMe()
    setUser(profile)
    return profile
  }, [])

  // ─── Logout ───────────────────────────────────────────────────────────────
  const logout = useCallback(async () => {
    try { await authAPI.logout() } catch { /* ignore */ }
    localStorage.clear()
    setUser(null)
  }, [])

  // ─── Update local user state (after profile edit) ─────────────────────────
  const updateUser = useCallback((updatedUser) => {
    setUser((prev) => ({ ...prev, ...updatedUser }))
  }, [])

  const refreshUser = useCallback(async () => {
    const { data } = await authAPI.getMe()
    setUser(data)
    return data
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, loginStep1, loginStep2, devLogin, logout, register, updateUser, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
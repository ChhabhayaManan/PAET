import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import LogoMark from '../ui/LogoMark'

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex min-h-[100dvh] flex-col items-center justify-center gap-4" role="status">
        <LogoMark className="h-11 w-11 motion-safe:animate-pulse" />
        <p className="text-sm text-ink-subtle">Loading PAET…</p>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (user.role === 'student' && !user.onboarding_done && location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" replace />
  }

  return children
}
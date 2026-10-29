import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { ArrowLeft, ArrowRight, CircleCheck, Eye, EyeOff, KeyRound, Lock, Mail, RefreshCw, ShieldCheck, Terminal } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../hooks/useAuth'
import { authAPI, getErrorMessage } from '../utils/api'
import AuthLayout from '../components/auth/AuthLayout'
import Button from '../components/ui/Button'
import { TextField } from '../components/ui/Field'

// One invisible input drawn as 6 boxes, so typing, paste and SMS autofill all work.
function OtpInput({ value, onChange, error, autoFocus, label }) {
  const digits = (value + '      ').slice(0, 6).split('')
  return (
    <div className="relative mx-auto w-fit rounded-2xl focus-within:ring-2 focus-within:ring-brand-400/70 focus-within:ring-offset-4 focus-within:ring-offset-tile">
      <div className="pointer-events-none flex select-none gap-2" aria-hidden="true">
        {digits.map((d, i) => (
          <div
            key={i}
            className={`flex h-14 w-11 items-center justify-center rounded-xl border font-mono text-xl font-semibold transition-colors sm:w-12 ${
              error ? 'border-pop-coral/60 bg-pop-coral/[0.06] text-pop-coral'
                : d.trim() ? 'border-ink bg-tile-3 text-ink'
                : value.length === i ? 'border-brand-400/80 bg-tile-2'
                : 'border-line-strong bg-tile-2'
            }`}
          >
            {d.trim() ? d : value.length === i ? <span className="h-6 w-0.5 bg-brand-400 motion-safe:animate-blink" /> : null}
          </div>
        ))}
      </div>
      <input
        type="text"
        inputMode="numeric"
        autoComplete="one-time-code"
        aria-label={label}
        aria-invalid={Boolean(error) || undefined}
        autoFocus={autoFocus}
        value={value}
        maxLength={6}
        onChange={e => onChange(e.target.value.replace(/\D/g, '').slice(0, 6))}
        className="absolute inset-0 w-full cursor-text opacity-0"
      />
    </div>
  )
}

function OtpNote({ hint }) {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-line-strong bg-tile-2 p-4">
      <ShieldCheck size={18} className="mt-0.5 shrink-0 text-pop-mint" />
      <p className="text-sm text-ink-muted">We sent a 6-digit code to <span className="font-medium text-ink">{hint}</span>. It expires in 10 minutes.</p>
    </div>
  )
}

function PasswordToggle({ shown, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={shown ? 'Hide password' : 'Show password'}
      className="flex h-9 w-9 items-center justify-center rounded-full text-ink-subtle hover:bg-white/[0.06] hover:text-ink"
    >
      {shown ? <EyeOff size={16} /> : <Eye size={16} />}
    </button>
  )
}

export default function LoginPage() {
  const { loginStep1, loginStep2, devLogin } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/dashboard'
  const justRegistered = location.state?.registered

  const [mode, setMode] = useState('login')

  const [form, setForm] = useState({ email: location.state?.email || '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)

  // Asked of the backend rather than read from a build flag: the frontend ships
  // as a production build even in local Docker, so import.meta.env.DEV is false.
  const [devAvailable, setDevAvailable] = useState(false)
  const [devEmail, setDevEmail] = useState('')
  const [devLoading, setDevLoading] = useState(false)

  useEffect(() => {
    authAPI.devLoginAvailable()
      .then(({ data }) => { setDevEmail(data.message); setDevAvailable(true) })
      .catch(() => setDevAvailable(false))
  }, [])

  const handleDevLogin = async () => {
    setDevLoading(true)
    try {
      await devLogin()
      navigate(from, { replace: true })
    } catch {
      setDevAvailable(false)
    } finally {
      setDevLoading(false)
    }
  }

  const [step, setStep] = useState(1)
  const [otpToken, setOtpToken] = useState('')
  const [emailHint, setEmailHint] = useState('')
  const [otp, setOtp] = useState('')
  const [otpError, setOtpError] = useState('')
  const [verifying, setVerifying] = useState(false)
  const [resending, setResending] = useState(false)
  const [countdown, setCountdown] = useState(0)

  const [fpEmail, setFpEmail] = useState('')
  const [fpEmailError, setFpEmailError] = useState('')
  const [fpStep, setFpStep] = useState(1)
  const [fpOtpToken, setFpOtpToken] = useState('')
  const [fpEmailHint, setFpEmailHint] = useState('')
  const [fpOtp, setFpOtp] = useState('')
  const [fpOtpError, setFpOtpError] = useState('')
  const [fpNewPassword, setFpNewPassword] = useState('')
  const [fpPwError, setFpPwError] = useState('')
  const [fpShowPw, setFpShowPw] = useState(false)
  const [fpLoading, setFpLoading] = useState(false)
  const [fpCountdown, setFpCountdown] = useState(0)

  useEffect(() => {
    if (countdown <= 0) return
    const t = setTimeout(() => setCountdown(c => c - 1), 1000)
    return () => clearTimeout(t)
  }, [countdown])

  useEffect(() => {
    if (fpCountdown <= 0) return
    const t = setTimeout(() => setFpCountdown(c => c - 1), 1000)
    return () => clearTimeout(t)
  }, [fpCountdown])

  useEffect(() => {
    if (otp.length === 6) handleVerifyOtp(otp)
  }, [otp])

  useEffect(() => {
    if (fpOtp.length === 6 && fpStep === 2) handleFpVerifyOtp(fpOtp)
  }, [fpOtp])

  const validateStep1 = () => {
    const e = {}
    if (!form.email) e.email = 'Enter your email'
    else if (!/\S+@\S+\.\S+/.test(form.email)) e.email = 'That email looks incomplete'
    if (!form.password) e.password = 'Enter your password'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleStep1 = async (e) => {
    e.preventDefault()
    if (!validateStep1()) return
    setLoading(true)
    try {
      const data = await loginStep1(form.email, form.password)
      setOtpToken(data.otp_token); setEmailHint(data.email_hint)
      setStep(2); setCountdown(30); setOtp('')
      toast.success('Code sent to your email')
    } catch (err) {
      setErrors({ general: getErrorMessage(err, "Couldn't sign you in.") })
    } finally { setLoading(false) }
  }

  const handleVerifyOtp = async (code = otp) => {
    if (code.length < 6) { setOtpError('Enter all 6 digits'); return }
    if (verifying) return
    setVerifying(true); setOtpError('')
    try {
      const user = await loginStep2(otpToken, code)
      toast.success(`Welcome back, ${user.full_name?.split(' ')[0] || user.username}`)
      navigate(from, { replace: true })
    } catch (err) {
      setOtpError(getErrorMessage(err, 'That code is not right. Try again.')); setOtp('')
    } finally { setVerifying(false) }
  }

  const handleResend = async () => {
    if (countdown > 0) return
    setResending(true)
    try {
      const data = await loginStep1(form.email, form.password)
      setOtpToken(data.otp_token); setOtp(''); setOtpError(''); setCountdown(30)
      toast.success('New code sent')
    } catch { toast.error("Couldn't send a new code. Try again in a minute.") }
    finally { setResending(false) }
  }

  const handleFpSendOtp = async (e) => {
    e.preventDefault()
    if (!fpEmail || !/\S+@\S+\.\S+/.test(fpEmail)) { setFpEmailError('Enter the email you signed up with'); return }
    setFpEmailError('')
    setFpLoading(true)
    try {
      const { data } = await authAPI.forgotPassword(fpEmail)
      setFpOtpToken(data.otp_token); setFpEmailHint(data.email_hint)
      setFpStep(2); setFpCountdown(30); setFpOtp('')
      toast.success('Code sent. Check your email.')
    } catch { setFpEmailError('Something went wrong. Try again in a minute.') }
    finally { setFpLoading(false) }
  }

  const handleFpVerifyOtp = (code = fpOtp) => {
    if (code.length < 6) { setFpOtpError('Enter all 6 digits'); return }
    setFpStep(3)
  }

  const handleFpResend = async () => {
    if (fpCountdown > 0) return
    setFpLoading(true)
    try {
      const { data } = await authAPI.forgotPassword(fpEmail)
      setFpOtpToken(data.otp_token); setFpOtp(''); setFpOtpError(''); setFpCountdown(30)
      toast.success('New code sent')
    } catch { toast.error("Couldn't send a new code.") }
    finally { setFpLoading(false) }
  }

  const handleFpReset = async (e) => {
    e.preventDefault()
    if (!fpNewPassword || fpNewPassword.length < 8) { setFpPwError('Use at least 8 characters, 1 uppercase letter and 1 digit'); return }
    setFpPwError('')
    setFpLoading(true)
    try {
      await authAPI.resetPassword({ otp_token: fpOtpToken, otp: fpOtp, new_password: fpNewPassword })
      toast.success('Password reset. You can log in now.')
      setMode('login'); setFpStep(1); setFpEmail(''); setFpOtp(''); setFpNewPassword('')
    } catch (err) {
      setFpPwError(getErrorMessage(err, "Couldn't reset your password."))
    } finally { setFpLoading(false) }
  }

  const title = mode === 'forgot'
    ? fpStep === 1 ? 'Reset your password' : fpStep === 2 ? 'Check your email' : 'Set a new password'
    : step === 1 ? 'Log in to PAET' : 'Check your email'

  const subtitle = mode === 'forgot'
    ? fpStep === 1 ? "Enter your email and we'll send you a 6-digit code." : fpStep === 2 ? 'Type the code from the email.' : 'Almost there.'
    : step === 1 ? 'Pick up your practice where you left off.' : 'Type the 6-digit code we just sent you.'

  const footer = mode === 'login' && step === 1 && (
    <>New to PAET? <Link to="/register" className="font-medium text-ink underline decoration-ink-faint underline-offset-4 hover:decoration-ink">Create an account</Link></>
  )

  return (
    <AuthLayout title={title} subtitle={subtitle} footer={footer}>
      {mode === 'login' && step === 1 && (
        <>
          {justRegistered && !errors.general && (
            <div className="mb-5 flex items-start gap-2.5 rounded-2xl border border-pop-mint/25 bg-pop-mint/[0.07] px-4 py-3 text-sm text-ink-muted" role="status">
              <CircleCheck size={16} className="mt-0.5 shrink-0 text-pop-mint" /> Account created. Log in to start your setup.
            </div>
          )}
          {errors.general && (
            <div className="mb-5 rounded-2xl border border-pop-coral/25 bg-pop-coral/[0.07] px-4 py-3 text-sm text-pop-coral" role="alert">
              {errors.general}
            </div>
          )}
          <form onSubmit={handleStep1} className="space-y-5" noValidate>
            <TextField
              label="Email"
              type="email"
              icon={Mail}
              value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              placeholder="you@college.edu"
              autoComplete="email"
              error={errors.email}
            />
            <div>
              <TextField
                label="Password"
                type={showPassword ? 'text' : 'password'}
                icon={Lock}
                value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                placeholder="Your password"
                autoComplete="current-password"
                error={errors.password}
                trailing={<PasswordToggle shown={showPassword} onToggle={() => setShowPassword(v => !v)} />}
              />
              <button type="button" onClick={() => setMode('forgot')} className="mt-2 text-xs font-medium text-ink-subtle underline-offset-4 hover:text-ink hover:underline">
                Forgot your password?
              </button>
            </div>
            <Button type="submit" size="lg" iconRight={ArrowRight} busy={loading} className="w-full">
              {loading ? 'Sending code…' : 'Continue'}
            </Button>
          </form>
          {/* Hides itself in any deploy without DEV_LOGIN_EMAIL: the endpoint 404s. */}
          {devAvailable && (
            <button
              type="button"
              onClick={handleDevLogin}
              disabled={devLoading}
              className="mt-3 flex h-11 w-full items-center justify-center gap-2 rounded-full border border-dashed border-line-strong font-mono text-xs text-ink-subtle transition-colors hover:border-ink-faint hover:text-ink"
            >
              <Terminal size={13} /> {devLoading ? 'Signing in…' : `Dev login · ${devEmail || 'skip the code'}`}
            </button>
          )}
        </>
      )}

      {mode === 'login' && step === 2 && (
        <div className="space-y-6">
          <OtpNote hint={emailHint} />
          <div>
            <OtpInput value={otp} onChange={v => { setOtp(v); setOtpError('') }} error={otpError} autoFocus label="6-digit code" />
            <p className={`mt-3 text-center text-xs ${otpError ? 'text-pop-coral' : 'text-ink-subtle'}`} role={otpError ? 'alert' : undefined}>
              {otpError || (verifying ? 'Checking the code…' : 'You can paste the code too.')}
            </p>
          </div>
          <Button size="lg" icon={ShieldCheck} onClick={() => handleVerifyOtp()} busy={verifying} disabled={otp.length < 6} className="w-full">
            {verifying ? 'Checking…' : 'Verify and log in'}
          </Button>
          <div className="flex items-center justify-between text-sm">
            <Button variant="ghost" size="sm" icon={ArrowLeft} onClick={() => { setStep(1); setOtp(''); setOtpError('') }}>Back</Button>
            <Button variant="ghost" size="sm" icon={RefreshCw} onClick={handleResend} disabled={countdown > 0} busy={resending}>
              {countdown > 0 ? `Resend in ${countdown}s` : 'Send a new code'}
            </Button>
          </div>
        </div>
      )}

      {mode === 'forgot' && fpStep === 1 && (
        <form onSubmit={handleFpSendOtp} className="space-y-5" noValidate>
          <TextField label="Email" type="email" icon={Mail} value={fpEmail} onChange={e => setFpEmail(e.target.value)}
            placeholder="you@college.edu" autoFocus error={fpEmailError} />
          <Button type="submit" size="lg" icon={KeyRound} busy={fpLoading} className="w-full">
            {fpLoading ? 'Sending code…' : 'Send reset code'}
          </Button>
          <Button variant="ghost" size="sm" icon={ArrowLeft} onClick={() => setMode('login')}>Back to log in</Button>
        </form>
      )}

      {mode === 'forgot' && fpStep === 2 && (
        <div className="space-y-6">
          <OtpNote hint={fpEmailHint} />
          <div>
            <OtpInput value={fpOtp} onChange={v => { setFpOtp(v); setFpOtpError('') }} error={fpOtpError} autoFocus label="6-digit reset code" />
            {fpOtpError && <p className="mt-3 text-center text-xs text-pop-coral" role="alert">{fpOtpError}</p>}
          </div>
          <Button size="lg" icon={ShieldCheck} onClick={() => handleFpVerifyOtp()} disabled={fpOtp.length < 6} className="w-full">Continue</Button>
          <div className="flex items-center justify-between">
            <Button variant="ghost" size="sm" icon={ArrowLeft} onClick={() => setFpStep(1)}>Back</Button>
            <Button variant="ghost" size="sm" icon={RefreshCw} onClick={handleFpResend} disabled={fpCountdown > 0} busy={fpLoading}>
              {fpCountdown > 0 ? `Resend in ${fpCountdown}s` : 'Send a new code'}
            </Button>
          </div>
        </div>
      )}

      {mode === 'forgot' && fpStep === 3 && (
        <form onSubmit={handleFpReset} className="space-y-5" noValidate>
          <TextField
            label="New password"
            type={fpShowPw ? 'text' : 'password'}
            icon={Lock}
            value={fpNewPassword}
            onChange={e => setFpNewPassword(e.target.value)}
            placeholder="Min 8 chars, 1 uppercase, 1 digit"
            helper="Min 8 chars, 1 uppercase, 1 digit"
            autoComplete="new-password"
            autoFocus
            error={fpPwError}
            trailing={<PasswordToggle shown={fpShowPw} onToggle={() => setFpShowPw(v => !v)} />}
          />
          <Button type="submit" size="lg" icon={KeyRound} busy={fpLoading} className="w-full">
            {fpLoading ? 'Saving…' : 'Reset password'}
          </Button>
        </form>
      )}
    </AuthLayout>
  )
}

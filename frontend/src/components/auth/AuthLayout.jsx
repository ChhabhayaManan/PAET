import { CircleCheck, Lightbulb, Play } from 'lucide-react'
import LogoMark, { Wordmark } from '../ui/LogoMark'

const POINTS = [
  { icon: Play, tone: 'bg-pop-mint text-canvas', text: 'Your code runs against real tests, so grading is never a guess.' },
  { icon: Lightbulb, tone: 'bg-pop-sun text-canvas', text: 'Stuck? Hints get stronger step by step and never give the answer away.' },
  { icon: CircleCheck, tone: 'bg-pop-aqua text-canvas', text: 'Each answer moves your topic levels and picks what you practise next.' },
]

export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="flex min-h-[100dvh] items-center px-4 py-10 sm:px-6">
      <div className="mx-auto grid w-full max-w-5xl grid-cols-1 items-center gap-10 lg:grid-cols-[minmax(0,1fr)_440px] lg:gap-16">
        <div className="hidden lg:block">
          <div className="flex items-center gap-2.5">
            <LogoMark className="h-9 w-9" />
            <Wordmark className="text-xl" />
          </div>
          <h2 className="mt-10 max-w-[18ch] text-[40px] font-semibold leading-[1.1] tracking-tight text-ink">
            Practise programming, one honest step at a time.
          </h2>
          <ul className="mt-8 space-y-4">
            {POINTS.map(({ icon: Icon, tone, text }) => (
              <li key={text} className="flex max-w-md items-start gap-3 text-[15px] leading-relaxed text-ink-muted">
                <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${tone}`}><Icon size={16} /></span>
                <span className="pt-1">{text}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="w-full motion-safe:animate-rise">
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <LogoMark className="h-9 w-9" />
            <Wordmark className="text-xl" />
          </div>
          <div className="tile p-6 sm:p-8">
            <h1 className="text-2xl font-semibold tracking-tight text-ink">{title}</h1>
            {subtitle && <p className="mt-2 text-sm leading-relaxed text-ink-subtle">{subtitle}</p>}
            <div className="mt-7">{children}</div>
          </div>
          {footer && <div className="mt-5 text-center text-sm text-ink-subtle">{footer}</div>}
        </div>
      </div>
    </div>
  )
}

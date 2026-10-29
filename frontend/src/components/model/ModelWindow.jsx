import { useEffect, useId, useState } from 'react'
import { KeyRound, PlugZap, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { getErrorMessage, modelAPI } from '../../utils/api'
import Button from '../ui/Button'
import { ChoiceChips, SelectField, TextField } from '../ui/Field'

const MODES = [
  { value: 'default', label: 'PAET default' },
  { value: 'own', label: 'My key' },
  { value: 'local', label: 'Local model' },
]

function providersFor(settings, mode) {
  return settings.providers.filter(p => (mode === 'local' ? p.local_only : !p.local_only))
}

function startingProvider(settings, mode) {
  return settings.source === mode ? settings.provider : providersFor(settings, mode)[0]?.id || ''
}

export default function ModelWindow({ settings, onClose, onChange }) {
  const [mode, setMode] = useState(settings.source)
  const [provider, setProvider] = useState(() => startingProvider(settings, settings.source))
  const [apiKey, setApiKey] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [model, setModel] = useState(settings.source === 'default' ? '' : settings.model)
  const [models, setModels] = useState([])
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState('')
  const listId = useId()

  const info = settings.providers.find(p => p.id === provider)
  const savedKey = settings.source !== 'default' && settings.provider === provider && settings.key_hint
  const modes = MODES.filter(m => m.value !== 'local' || settings.deploy_mode === 'local')

  useEffect(() => {
    const onKey = e => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  useEffect(() => { setBaseUrl(info?.base_url || '') }, [info])

  const switchMode = next => {
    setMode(next)
    setProvider(startingProvider(settings, next))
    setModel(settings.source === next ? settings.model : '')
    setModels([])
    setError(null)
  }

  const switchProvider = next => {
    setProvider(next)
    setModel('')
    setModels([])
    setError(null)
  }

  const body = () => ({ provider, model: model.trim(), api_key: apiKey.trim(), base_url: info?.local_only ? baseUrl.trim() : '' })

  const run = async (kind, request) => {
    setBusy(kind)
    setError(null)
    try {
      return await request()
    } catch (err) {
      setError({ detail: getErrorMessage(err), said: err?.response?.data?.provider_message })
      return null
    } finally {
      setBusy('')
    }
  }

  const test = () => run('test', async () => {
    const { data } = await modelAPI.test(body())
    setModels(data.models)
    if (!model && data.models.length) setModel(data.models[0])
    toast.success(data.models.length ? `Connected. ${data.models.length} models found.` : 'Connected.')
  })

  const save = () => run('save', async () => {
    const { data } = await modelAPI.save(body())
    onChange(data)
    toast.success(`Now using ${data.model}`)
    onClose()
  })

  const useDefault = () => run('remove', async () => {
    const { data } = await modelAPI.remove()
    onChange(data)
    toast.success('Back to PAET default')
    onClose()
  })

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center" role="dialog" aria-modal="true" aria-labelledby="model-window-title">
      <button type="button" aria-label="Close" onClick={onClose} className="absolute inset-0 bg-canvas/75 backdrop-blur-sm motion-safe:animate-fade-in" />
      <div className="tile relative max-h-[calc(100dvh-2rem)] w-full max-w-lg overflow-y-auto p-6 motion-safe:animate-rise">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id="model-window-title" className="text-xl font-semibold tracking-tight text-ink">Model</h2>
            <p className="mt-1 text-[13px] text-ink-subtle">
              In use: <span className="font-mono text-ink-muted">{settings.model}</span>
            </p>
          </div>
          <button type="button" autoFocus onClick={onClose} aria-label="Close" className="flex h-9 w-9 items-center justify-center rounded-full text-ink-muted hover:bg-white/[0.06] hover:text-ink">
            <X size={18} />
          </button>
        </div>

        <div className="mt-5">
          <ChoiceChips label="Model source" options={modes} value={mode} onChange={switchMode} />
        </div>

        {mode === 'default' ? (
          <div className="mt-5 flex flex-col gap-4">
            <p className="text-sm leading-relaxed text-ink-muted">PAET&apos;s own model answers chat, hints, grading and feedback.</p>
            {settings.source !== 'default' && (
              <Button busy={busy === 'remove'} onClick={useDefault} className="self-start">Use PAET default</Button>
            )}
          </div>
        ) : (
          <form className="mt-5 flex flex-col gap-4" onSubmit={e => { e.preventDefault(); save() }}>
            <SelectField label="Provider" value={provider} onChange={e => switchProvider(e.target.value)}>
              {providersFor(settings, mode).map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
            </SelectField>

            {info?.local_only && (
              <TextField label="Server address" value={baseUrl} onChange={e => setBaseUrl(e.target.value)} inputClassName="font-mono text-sm" spellCheck={false} />
            )}

            {(info?.needs_key || info?.local_only) && (
              <TextField
                label="API key"
                optional={!info?.needs_key}
                type="password"
                autoComplete="off"
                icon={KeyRound}
                value={apiKey}
                onChange={e => setApiKey(e.target.value)}
                placeholder={savedKey ? `Saved key ··${settings.key_hint}` : 'Paste your key'}
                helper="Your key stays in this browser, encrypted. PAET never stores it."
              />
            )}

            <TextField
              label="Model"
              value={model}
              onChange={e => setModel(e.target.value)}
              list={listId}
              placeholder={models.length ? 'Pick or type a model' : 'Test the connection to list models'}
              inputClassName="font-mono text-sm"
              spellCheck={false}
            />
            <datalist id={listId}>
              {models.map(m => <option key={m} value={m} />)}
            </datalist>

            {error && (
              <div role="alert" className="rounded-md border border-pop-coral/40 bg-pop-coral/10 p-3 text-[13px] text-ink">
                <p>{error.detail}</p>
                {error.said && <p className="mt-1.5 font-mono text-[11px] text-ink-subtle">{error.said}</p>}
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" icon={PlugZap} busy={busy === 'test'} disabled={Boolean(busy)} onClick={test}>Test connection</Button>
              <Button type="submit" busy={busy === 'save'} disabled={Boolean(busy) || !model.trim()}>Save</Button>
              {settings.source === mode && (
                <Button variant="ghost" busy={busy === 'remove'} disabled={Boolean(busy)} onClick={useDefault} className="sm:ml-auto">Remove key</Button>
              )}
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

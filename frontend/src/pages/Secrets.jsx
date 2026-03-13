import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { getSecrets, upsertSecret } from '../api/settings'
import { Eye, EyeOff, Save, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'

const SECRET_LABELS = {
  BINANCE_API_KEY: 'Binance API Key',
  BINANCE_SECRET_KEY: 'Binance Secret Key',
  PLAID_CLIENT_ID: 'Plaid Client ID',
  PLAID_SECRET_SANDBOX: 'Plaid Secret (Sandbox)',
  PLAID_SECRET_PRODUCTION: 'Plaid Secret (Production)',
  OPENAI_API_KEY: 'OpenAI API Key',
  TELEGRAM_BOT_TOKEN: 'Telegram Bot Token',
  TELEGRAM_CHAT_ID: 'Telegram Chat ID',
}

function SecretRow({ secret }) {
  const qc = useQueryClient()
  const [value, setValue] = useState('')
  const [show, setShow] = useState(false)
  const [editing, setEditing] = useState(false)

  const mut = useMutation(() => upsertSecret(secret.key, value), {
    onSuccess: () => {
      toast.success(`${SECRET_LABELS[secret.key] || secret.key} saved`)
      setValue('')
      setEditing(false)
      qc.invalidateQueries('secrets')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Save failed'),
  })

  return (
    <div className="flex items-center justify-between py-4 border-b border-binance-gray-light last:border-0">
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium">{SECRET_LABELS[secret.key] || secret.key}</p>
          {secret.is_set && (
            <span className="flex items-center gap-1 text-xs text-green-400">
              <CheckCircle size={10} /> Set
            </span>
          )}
        </div>
        <p className="text-xs text-binance-text-secondary mt-0.5 font-mono">
          {secret.is_set ? '••••••••••••' : 'Not configured'}
        </p>
      </div>

      <div className="flex items-center gap-2 ml-4">
        {editing ? (
          <>
            <div className="relative">
              <input
                type={show ? 'text' : 'password'}
                className="input-field pr-8 text-sm w-56"
                placeholder="Enter new value..."
                value={value}
                onChange={(e) => setValue(e.target.value)}
                autoFocus
              />
              <button
                className="absolute right-2 top-2.5 text-binance-text-secondary"
                onClick={() => setShow(!show)}
                type="button"
              >
                {show ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
            <button
              className="btn-primary text-sm flex items-center gap-1"
              onClick={() => value.trim() && mut.mutate()}
              disabled={mut.isLoading || !value.trim()}
            >
              <Save size={13} /> Save
            </button>
            <button className="btn-secondary text-sm" onClick={() => { setEditing(false); setValue('') }}>
              Cancel
            </button>
          </>
        ) : (
          <button
            className="btn-secondary text-sm"
            onClick={() => setEditing(true)}
          >
            {secret.is_set ? 'Rotate' : 'Set'}
          </button>
        )}
      </div>
    </div>
  )
}

export default function Secrets() {
  const { data, isLoading } = useQuery('secrets', getSecrets)
  const secrets = data?.secrets || []

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-bold">Integrations & Secrets</h1>
        <p className="text-sm text-binance-text-secondary mt-1">
          All secrets are encrypted at rest and never shown in plain text after saving.
        </p>
      </div>

      <div className="card">
        {isLoading && <p className="text-binance-text-secondary text-sm">Loading...</p>}
        {secrets.map((s) => (
          <SecretRow key={s.key} secret={s} />
        ))}
      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { useQuery, useMutation } from 'react-query'
import { getSettings, updateSettings } from '../api/settings'
import { AlertTriangle, Shield } from 'lucide-react'
import toast from 'react-hot-toast'

function Toggle({ label, description, checked, onChange, disabled = false }) {
  return (
    <div className="flex items-start justify-between py-4 border-b border-binance-gray-light last:border-0">
      <div className="flex-1 mr-4">
        <p className="text-sm font-medium">{label}</p>
        {description && <p className="text-xs text-binance-text-secondary mt-1">{description}</p>}
      </div>
      <button
        onClick={() => !disabled && onChange(!checked)}
        disabled={disabled}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          checked ? 'bg-binance-yellow' : 'bg-binance-gray-light'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
      >
        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${checked ? 'translate-x-6' : 'translate-x-1'}`} />
      </button>
    </div>
  )
}

export default function Settings() {
  const { data, isLoading, refetch } = useQuery('settings', getSettings)
  const [local, setLocal] = useState(null)
  const [promptText, setPromptText] = useState('')

  useEffect(() => {
    if (data) {
      setLocal(data)
      setPromptText(data.ai_system_prompt || '')
    }
  }, [data])

  const mut = useMutation(updateSettings, {
    onSuccess: (res) => {
      toast.success('Settings updated')
      refetch()
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Update failed'),
  })

  const update = (patch) => {
    setLocal(prev => ({ ...prev, ...patch }))
    mut.mutate(patch)
  }

  if (isLoading || !local) return <p className="text-binance-text-secondary">Loading settings...</p>

  const isManualReview = local.verification_mode === 'manual_review'

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Settings & Controls</h1>
        {local.kill_switch && (
          <span className="flex items-center gap-2 bg-red-900 text-red-300 text-xs px-3 py-1.5 rounded-full animate-pulse">
            <AlertTriangle size={12} /> KILL SWITCH ACTIVE
          </span>
        )}
      </div>

      {/* Verification Mode */}
      <div className="card mb-4">
        <h2 className="font-semibold mb-4 flex items-center gap-2">
          <Shield size={16} className="text-binance-yellow" /> Verification Mode
        </h2>
        <div className="grid grid-cols-2 gap-3">
          {['manual_review', 'plaid'].map((mode) => (
            <button
              key={mode}
              onClick={() => update({ verification_mode: mode })}
              className={`p-3 rounded border text-sm font-medium transition-colors ${
                local.verification_mode === mode
                  ? 'border-binance-yellow bg-yellow-900 bg-opacity-20 text-binance-yellow'
                  : 'border-binance-gray-light text-binance-text-secondary hover:border-binance-text-secondary'
              }`}
            >
              {mode === 'manual_review' ? '👁 Manual Review' : '🏦 Plaid Verification'}
            </button>
          ))}
        </div>
        <p className="text-xs text-binance-text-secondary mt-2">
          {isManualReview
            ? 'No auto-verification. Operator manually confirms payment externally.'
            : 'Plaid checks bank transactions to confirm payment automatically.'}
        </p>
      </div>

      {/* Release Mode */}
      <div className="card mb-4">
        <h2 className="font-semibold mb-4">Release Mode</h2>
        <div className="grid grid-cols-2 gap-3">
          {[
            { value: 'manual', label: '🖱 Manual Release' },
            { value: 'auto', label: '⚡ Auto Release', disabled: isManualReview },
          ].map(({ value, label, disabled }) => (
            <button
              key={value}
              onClick={() => !disabled && update({ release_mode: value })}
              disabled={disabled}
              title={disabled ? 'Auto Release requires Plaid verification' : undefined}
              className={`p-3 rounded border text-sm font-medium transition-colors ${
                local.release_mode === value
                  ? 'border-binance-yellow bg-yellow-900 bg-opacity-20 text-binance-yellow'
                  : 'border-binance-gray-light text-binance-text-secondary hover:border-binance-text-secondary'
              } ${disabled ? 'opacity-40 cursor-not-allowed' : ''}`}
            >
              {label}
            </button>
          ))}
        </div>
        {isManualReview && (
          <p className="text-xs text-red-400 mt-2">
            ⚠ Auto Release is disabled — requires an active verification provider (Plaid).
          </p>
        )}
      </div>

      {/* Toggles */}
      <div className="card mb-4">
        <h2 className="font-semibold mb-2">Controls</h2>
        <Toggle
          label="AI Auto-Reply"
          description="Let AI automatically generate and send chat replies"
          checked={local.ai_auto_reply}
          onChange={(val) => update({ ai_auto_reply: val })}
        />
        <Toggle
          label="🔴 Emergency Kill Switch"
          description="Immediately block all auto-release actions"
          checked={local.kill_switch}
          onChange={(val) => update({ kill_switch: val })}
        />
      </div>

      {/* AI Prompt */}
      <div className="card">
        <h2 className="font-semibold mb-3">AI System Prompt</h2>
        <textarea
          className="input-field h-32 resize-none"
          value={promptText}
          onChange={(e) => setPromptText(e.target.value)}
          placeholder="Enter custom instructions for the AI..."
        />
        <button
          className="btn-primary mt-3"
          onClick={() => update({ ai_system_prompt: promptText })}
          disabled={mut.isLoading}
        >
          Save Prompt
        </button>
      </div>
    </div>
  )
}

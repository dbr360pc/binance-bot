import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from 'react-query'
import { verifyTOTP } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import { ShieldCheck } from 'lucide-react'
import toast from 'react-hot-toast'

export default function MFA() {
  const [code, setCode] = useState('')
  const { login: setAuth } = useAuth()
  const navigate = useNavigate()

  const mut = useMutation(() => {
    const temp_token = sessionStorage.getItem('temp_token')
    if (!temp_token) throw new Error('Session expired. Please login again.')
    return verifyTOTP(temp_token, code)
  }, {
    onSuccess: (data) => {
      sessionStorage.removeItem('temp_token')
      setAuth(data.access_token, {})
      navigate('/orders')
    },
    onError: (e) => toast.error(e.response?.data?.detail || e.message || 'Invalid code'),
  })

  return (
    <div className="min-h-screen flex items-center justify-center bg-binance-dark">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <ShieldCheck size={40} className="text-binance-yellow mx-auto mb-2" />
          <h1 className="text-xl font-bold">Two-Factor Authentication</h1>
          <p className="text-binance-text-secondary text-sm mt-1">Enter the code from your authenticator app</p>
        </div>

        <div className="card">
          <div className="space-y-4">
            <div>
              <label className="label">6-Digit Code</label>
              <input
                className="input-field text-center text-2xl tracking-widest"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                maxLength={6}
                autoFocus
                onKeyDown={(e) => e.key === 'Enter' && code.length === 6 && mut.mutate()}
              />
            </div>
            <button
              className="btn-primary w-full"
              onClick={() => mut.mutate()}
              disabled={code.length !== 6 || mut.isLoading}
            >
              {mut.isLoading ? 'Verifying...' : 'Verify'}
            </button>
            <button
              className="text-sm text-binance-text-secondary hover:text-white w-full text-center"
              onClick={() => navigate('/login')}
            >
              Back to Login
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

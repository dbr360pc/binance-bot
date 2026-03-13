import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from 'react-query'
import { login } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import { Zap } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Login() {
  const [form, setForm] = useState({ username: '', password: '' })
  const { login: setAuth } = useAuth()
  const navigate = useNavigate()

  const mut = useMutation(({ username, password }) => login(username, password), {
    onSuccess: (data) => {
      if (data.totp_required) {
        sessionStorage.setItem('temp_token', data.temp_token)
        navigate('/mfa')
      } else {
        setAuth(data.access_token, { username: form.username })
        navigate('/orders')
      }
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Login failed'),
  })

  const onSubmit = (e) => {
    e.preventDefault()
    mut.mutate(form)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-binance-dark">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Zap size={28} className="text-binance-yellow" />
            <span className="text-2xl font-bold text-binance-yellow">P2P Bot</span>
          </div>
          <p className="text-binance-text-secondary text-sm">Internal Operations Dashboard</p>
        </div>

        <div className="card">
          <h1 className="text-lg font-semibold mb-6">Sign In</h1>
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="label">Username</label>
              <input
                className="input-field"
                value={form.username}
                onChange={(e) => setForm(f => ({ ...f, username: e.target.value }))}
                required
                autoFocus
              />
            </div>
            <div>
              <label className="label">Password</label>
              <input
                type="password"
                className="input-field"
                value={form.password}
                onChange={(e) => setForm(f => ({ ...f, password: e.target.value }))}
                required
              />
            </div>
            <button type="submit" className="btn-primary w-full mt-2" disabled={mut.isLoading}>
              {mut.isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

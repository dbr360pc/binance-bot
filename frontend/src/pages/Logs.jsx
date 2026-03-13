import { useState } from 'react'
import { useQuery } from 'react-query'
import { getAdminLogs, getReleaseLogs } from '../api/settings'
import { format } from 'date-fns'

function LogTable({ logs, columns }) {
  if (!logs.length) return <p className="text-binance-text-secondary text-sm py-4">No entries</p>
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-binance-gray-light">
            {columns.map(col => (
              <th key={col.key} className="text-left text-binance-text-secondary text-xs py-2 pr-4 font-medium">{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {logs.map((row, i) => (
            <tr key={i} className="border-b border-binance-gray-light border-opacity-40 hover:bg-binance-gray-light hover:bg-opacity-30">
              {columns.map(col => (
                <td key={col.key} className="py-2 pr-4 text-xs font-mono align-top max-w-xs truncate">
                  {col.render ? col.render(row[col.key], row) : (row[col.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Logs() {
  const [tab, setTab] = useState('releases')

  const { data: releaseData, isLoading: rLoading } = useQuery('release-logs', () => getReleaseLogs(100), { enabled: tab === 'releases' })
  const { data: adminData, isLoading: aLoading }   = useQuery('admin-logs', () => getAdminLogs(100), { enabled: tab === 'admin' })

  const releaseLogs = releaseData?.logs || []
  const adminLogs   = adminData?.logs || []

  const releaseCols = [
    { key: 'created_at', label: 'Time', render: v => v ? format(new Date(v), 'MM/dd HH:mm:ss') : '—' },
    { key: 'binance_order_id', label: 'Order ID' },
    { key: 'released_by', label: 'By' },
    { key: 'verification_mode', label: 'Verify Mode' },
    { key: 'release_mode', label: 'Release Mode' },
    { key: 'success', label: 'Success', render: v => v ? <span className="text-green-400">✓</span> : <span className="text-red-400">✗</span> },
    { key: 'ip_address', label: 'IP' },
  ]

  const adminCols = [
    { key: 'created_at', label: 'Time', render: v => v ? format(new Date(v), 'MM/dd HH:mm:ss') : '—' },
    { key: 'username', label: 'User' },
    { key: 'action', label: 'Action' },
    { key: 'detail', label: 'Detail' },
    { key: 'ip_address', label: 'IP' },
  ]

  return (
    <div>
      <h1 className="text-xl font-bold mb-6">Logs</h1>

      <div className="flex gap-1 mb-4">
        {['releases', 'admin'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm rounded font-medium transition-colors ${
              tab === t ? 'bg-binance-yellow text-binance-dark' : 'bg-binance-gray-light text-binance-text-secondary hover:text-white'
            }`}
          >
            {t === 'releases' ? 'Release Audit Log' : 'Admin Activity'}
          </button>
        ))}
      </div>

      <div className="card">
        {tab === 'releases' && (rLoading ? <p className="text-binance-text-secondary text-sm">Loading...</p> : <LogTable logs={releaseLogs} columns={releaseCols} />)}
        {tab === 'admin'    && (aLoading ? <p className="text-binance-text-secondary text-sm">Loading...</p> : <LogTable logs={adminLogs}   columns={adminCols} />)}
      </div>
    </div>
  )
}

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { getItems, syncItem, deactivateItem, getLinkToken, exchangeToken } from '../api/plaid'
import { usePlaidLink } from 'react-plaid-link'
import { RefreshCw, Trash2, Building2 } from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

function PlaidConnectButton({ onSuccess }) {
  const [linkToken, setLinkToken] = useState(null)

  const fetchToken = async () => {
    try {
      const data = await getLinkToken()
      setLinkToken(data.link_token)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to get link token')
    }
  }

  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess: async (public_token, metadata) => {
      try {
        await exchangeToken(
          public_token,
          metadata.institution?.name,
          metadata.institution?.institution_id
        )
        toast.success('Bank connected successfully')
        onSuccess()
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Exchange failed')
      }
    },
  })

  return (
    <button
      className="btn-primary"
      onClick={linkToken ? open : fetchToken}
      disabled={linkToken ? !ready : false}
    >
      {linkToken ? 'Open Plaid Link' : 'Connect Bank Account'}
    </button>
  )
}

export default function Banks() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery('plaid-items', getItems)

  const syncMut = useMutation((item_id) => syncItem(item_id), {
    onSuccess: (data) => {
      toast.success(`Synced: +${data.added} new transactions`)
      qc.invalidateQueries('plaid-items')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Sync failed'),
  })

  const deactivateMut = useMutation((item_id) => deactivateItem(item_id), {
    onSuccess: () => {
      toast.success('Bank disconnected')
      qc.invalidateQueries('plaid-items')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Deactivate failed'),
  })

  const items = data?.items || []

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Connected Banks</h1>
        <PlaidConnectButton onSuccess={() => qc.invalidateQueries('plaid-items')} />
      </div>

      {isLoading && <p className="text-binance-text-secondary">Loading...</p>}

      {!isLoading && items.length === 0 && (
        <div className="card text-center text-binance-text-secondary py-12">
          <Building2 size={40} className="mx-auto mb-3 opacity-30" />
          <p>No bank accounts connected</p>
          <p className="text-xs mt-1">Connect a bank to enable Plaid payment verification</p>
        </div>
      )}

      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.id} className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold">{item.institution_name || 'Unknown Bank'}</p>
                <p className="text-xs text-binance-text-secondary mt-1">Item ID: {item.item_id}</p>
                <p className="text-xs text-binance-text-secondary">
                  Last synced: {item.last_synced_at ? format(new Date(item.last_synced_at), 'MM/dd/yyyy HH:mm') : 'Never'}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-1 rounded-full ${item.is_active ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                  {item.is_active ? 'Active' : 'Inactive'}
                </span>
                <button
                  className="btn-secondary p-2"
                  onClick={() => syncMut.mutate(item.item_id)}
                  disabled={syncMut.isLoading}
                  title="Sync transactions"
                >
                  <RefreshCw size={14} className={syncMut.isLoading ? 'animate-spin' : ''} />
                </button>
                <button
                  className="text-red-400 hover:text-red-300 p-2"
                  onClick={() => deactivateMut.mutate(item.item_id)}
                  title="Disconnect"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

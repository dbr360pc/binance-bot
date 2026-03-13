import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useNavigate } from 'react-router-dom'
import { getOrders, releaseOrder } from '../api/orders'
import StatusBadge from '../components/StatusBadge'
import ConfirmModal from '../components/ConfirmModal'
import { RefreshCw, ChevronRight } from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

export default function Orders() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [releaseTarget, setReleaseTarget] = useState(null)

  const { data, isLoading, error, refetch, isFetching } = useQuery(
    'orders',
    () => getOrders(),
    { refetchInterval: 30000 }
  )

  const releaseMut = useMutation((order_id) => releaseOrder(order_id), {
    onSuccess: () => {
      toast.success('Order released successfully')
      setReleaseTarget(null)
      qc.invalidateQueries('orders')
    },
    onError: (e) => {
      toast.error(e.response?.data?.detail || 'Release failed')
      setReleaseTarget(null)
    },
  })

  const orders = data?.orders || []

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Active Orders</h1>
        <button
          onClick={() => refetch()}
          className="btn-secondary flex items-center gap-2 text-sm"
          disabled={isFetching}
        >
          <RefreshCw size={14} className={isFetching ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {isLoading && <p className="text-binance-text-secondary">Loading orders...</p>}
      {error && (
        <div className="card text-red-400 text-sm">
          {error.response?.data?.detail || 'Failed to load orders. Check Binance credentials.'}
        </div>
      )}

      {!isLoading && orders.length === 0 && (
        <div className="card text-center text-binance-text-secondary py-12">
          No active orders found
        </div>
      )}

      <div className="space-y-3">
        {orders.map((order) => (
          <div key={order.id} className="card hover:border-binance-yellow transition-colors cursor-pointer">
            <div className="flex items-center justify-between">
              <div className="flex-1" onClick={() => navigate(`/orders/${order.binance_order_id}`)}>
                <div className="flex items-center gap-3 mb-2">
                  <span className="font-semibold text-sm">{order.binance_order_id}</span>
                  <StatusBadge status={order.order_status} />
                  <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                    order.trade_side === 'BUY' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
                  }`}>
                    {order.trade_side}
                  </span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-binance-text-secondary text-xs">Asset / Amount</p>
                    <p className="font-medium">{order.amount} {order.asset}</p>
                  </div>
                  <div>
                    <p className="text-binance-text-secondary text-xs">Fiat</p>
                    <p className="font-medium">{order.fiat_amount} {order.fiat_currency}</p>
                  </div>
                  <div>
                    <p className="text-binance-text-secondary text-xs">Counterparty</p>
                    <p className="font-medium truncate">{order.counterparty_name || '—'}</p>
                  </div>
                  <div>
                    <p className="text-binance-text-secondary text-xs">Created</p>
                    <p className="font-medium">
                      {order.created_time ? format(new Date(order.created_time), 'MM/dd HH:mm') : '—'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 ml-4">
                {order.order_status !== 'released' && (
                  <button
                    className="btn-primary text-sm"
                    onClick={() => setReleaseTarget(order)}
                  >
                    Release
                  </button>
                )}
                <ChevronRight
                  size={18}
                  className="text-binance-text-secondary"
                  onClick={() => navigate(`/orders/${order.binance_order_id}`)}
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {releaseTarget && (
        <ConfirmModal
          title="Confirm Release"
          message={`Are you sure you want to release order ${releaseTarget.binance_order_id}? This action is irreversible.`}
          danger
          loading={releaseMut.isLoading}
          onConfirm={() => releaseMut.mutate(releaseTarget.binance_order_id)}
          onCancel={() => setReleaseTarget(null)}
        />
      )}
    </div>
  )
}

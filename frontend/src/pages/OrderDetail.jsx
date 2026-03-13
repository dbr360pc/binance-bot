import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { getOrderDetail, releaseOrder } from '../api/orders'
import StatusBadge from '../components/StatusBadge'
import ConfirmModal from '../components/ConfirmModal'
import ChatPanel from '../components/ChatPanel'
import { ArrowLeft, MessageSquare } from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

export default function OrderDetail() {
  const { orderId } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [showRelease, setShowRelease] = useState(false)
  const [showChat, setShowChat] = useState(false)

  const { data, isLoading } = useQuery(['order', orderId], () => getOrderDetail(orderId))

  const releaseMut = useMutation(() => releaseOrder(orderId), {
    onSuccess: () => {
      toast.success('Order released')
      setShowRelease(false)
      qc.invalidateQueries(['order', orderId])
    },
    onError: (e) => {
      toast.error(e.response?.data?.detail || 'Release failed')
      setShowRelease(false)
    },
  })

  const binance = data?.binance_data?.data || {}
  const local = data?.local_order || {}

  if (isLoading) return <p className="text-binance-text-secondary">Loading...</p>

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/orders')} className="text-binance-text-secondary hover:text-white">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-xl font-bold">Order Detail</h1>
        <span className="text-binance-text-secondary text-sm">{orderId}</span>
        {local.order_status && <StatusBadge status={local.order_status} />}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Order Info */}
        <div className="card">
          <h2 className="font-semibold mb-4">Order Information</h2>
          <div className="space-y-3 text-sm">
            {[
              ['Order No', binance.orderNo || orderId],
              ['Asset', binance.asset],
              ['Trade Side', binance.tradeType],
              ['Amount', `${binance.amount} ${binance.asset}`],
              ['Fiat Amount', `${binance.totalPrice} ${binance.fiat}`],
              ['Price', binance.unitPrice],
              ['Payment Method', binance.payType],
              ['Counterparty', binance.buyerName || binance.sellerName],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between">
                <span className="text-binance-text-secondary">{label}</span>
                <span className="font-medium">{value || '—'}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Release Panel */}
        <div className="card">
          <h2 className="font-semibold mb-4">Release Control</h2>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-binance-text-secondary">Verification Status</span>
              {local.order_status && <StatusBadge status={local.order_status} />}
            </div>
            {local.released_at && (
              <div className="flex justify-between text-sm">
                <span className="text-binance-text-secondary">Released At</span>
                <span>{format(new Date(local.released_at), 'MM/dd/yyyy HH:mm')}</span>
              </div>
            )}
            {local.released_by && (
              <div className="flex justify-between text-sm">
                <span className="text-binance-text-secondary">Released By</span>
                <span>{local.released_by}</span>
              </div>
            )}

            {local.order_status !== 'released' && (
              <button
                className="btn-danger w-full mt-4"
                onClick={() => setShowRelease(true)}
              >
                Release Order
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Chat Panel */}
      <div className="card mt-6">
        <div
          className="flex items-center justify-between cursor-pointer"
          onClick={() => setShowChat(!showChat)}
        >
          <h2 className="font-semibold flex items-center gap-2">
            <MessageSquare size={16} /> Chat
          </h2>
          <span className="text-binance-text-secondary text-sm">{showChat ? 'Hide' : 'Show'}</span>
        </div>
        {showChat && (
          <div className="mt-4">
            <ChatPanel orderId={orderId} />
          </div>
        )}
      </div>

      {showRelease && (
        <ConfirmModal
          title="Confirm Release"
          message={`This will release order ${orderId}. This action is IRREVERSIBLE. Confirm only if you have verified payment.`}
          danger
          loading={releaseMut.isLoading}
          onConfirm={() => releaseMut.mutate()}
          onCancel={() => setShowRelease(false)}
        />
      )}
    </div>
  )
}

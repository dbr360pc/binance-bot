import { useState, useEffect, useRef } from 'react'
import { Send, Bot } from 'lucide-react'
import { useQuery, useMutation } from 'react-query'
import { getMessages, sendMessage } from '../api/orders'
import toast from 'react-hot-toast'

export default function ChatPanel({ orderId }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  const { data, refetch } = useQuery(
    ['chat', orderId],
    () => getMessages(orderId),
    { refetchInterval: 10000 }
  )

  const sendMut = useMutation((msg) => sendMessage(orderId, msg), {
    onSuccess: () => { setInput(''); refetch() },
    onError: (e) => toast.error(e.response?.data?.detail || 'Send failed'),
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [data])

  const logs = data?.local_logs || []

  return (
    <div className="flex flex-col h-96">
      <div className="flex-1 overflow-y-auto space-y-2 mb-3">
        {logs.length === 0 && (
          <p className="text-binance-text-secondary text-sm text-center py-4">No messages yet</p>
        )}
        {logs.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.direction === 'out' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                msg.direction === 'out'
                  ? 'bg-binance-yellow text-binance-dark'
                  : 'bg-binance-gray-light text-binance-text-primary'
              }`}
            >
              {msg.is_ai_generated && (
                <div className="flex items-center gap-1 text-xs mb-1 opacity-70">
                  <Bot size={10} /> AI
                </div>
              )}
              {msg.content}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2">
        <input
          className="input-field flex-1"
          placeholder="Type a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && input.trim() && sendMut.mutate(input.trim())}
        />
        <button
          className="btn-primary px-3"
          onClick={() => input.trim() && sendMut.mutate(input.trim())}
          disabled={sendMut.isLoading || !input.trim()}
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  )
}

import api from './client'

export const getOrders = (page = 1, rows = 20) =>
  api.get('/orders/', { params: { page, rows } }).then(r => r.data)

export const getOrderHistory = (trade_type = 'BUY', page = 1) =>
  api.get('/orders/history', { params: { trade_type, page } }).then(r => r.data)

export const getOrderDetail = (orderId) =>
  api.get(`/orders/${orderId}`).then(r => r.data)

export const releaseOrder = (order_id) =>
  api.post('/release/', { order_id, confirmed: true }).then(r => r.data)

export const getMessages = (orderId) =>
  api.get(`/chat/${orderId}/messages`).then(r => r.data)

export const sendMessage = (order_id, message) =>
  api.post('/chat/send', { order_id, message }).then(r => r.data)

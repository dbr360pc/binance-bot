import api from './client'

export const getLinkToken = () =>
  api.get('/plaid/link-token').then(r => r.data)

export const exchangeToken = (public_token, institution_name, institution_id) =>
  api.post('/plaid/exchange-token', { public_token, institution_name, institution_id }).then(r => r.data)

export const getItems = () =>
  api.get('/plaid/items').then(r => r.data)

export const syncItem = (item_id) =>
  api.post(`/plaid/items/${item_id}/sync`).then(r => r.data)

export const deactivateItem = (item_id) =>
  api.delete(`/plaid/items/${item_id}`).then(r => r.data)

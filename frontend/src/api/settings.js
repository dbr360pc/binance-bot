import api from './client'

export const getSettings = () =>
  api.get('/settings/').then(r => r.data)

export const updateSettings = (data) =>
  api.patch('/settings/', data).then(r => r.data)

export const getSecrets = () =>
  api.get('/secrets/').then(r => r.data)

export const upsertSecret = (key, value) =>
  api.post('/secrets/', { key, value }).then(r => r.data)

export const getAdminLogs = (limit = 50) =>
  api.get('/logs/admin', { params: { limit } }).then(r => r.data)

export const getReleaseLogs = (limit = 50) =>
  api.get('/logs/releases', { params: { limit } }).then(r => r.data)

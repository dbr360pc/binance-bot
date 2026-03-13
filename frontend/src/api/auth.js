import api from './client'

export const login = (username, password) =>
  api.post('/auth/login', { username, password }).then(r => r.data)

export const verifyTOTP = (temp_token, totp_code) =>
  api.post('/auth/totp/verify', { temp_token, totp_code }).then(r => r.data)

export const getTOTPSetup = () =>
  api.get('/auth/totp/setup').then(r => r.data)

export const enableTOTP = (totp_code) =>
  api.post('/auth/totp/enable', { totp_code }).then(r => r.data)

export const getMe = () =>
  api.get('/auth/me').then(r => r.data)

export const register = (username, password) =>
  api.post('/auth/register', { username, password }).then(r => r.data)

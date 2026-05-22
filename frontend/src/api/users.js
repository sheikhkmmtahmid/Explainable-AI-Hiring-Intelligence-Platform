import client from './client'

export const getUsers = () => client.get('/auth/users/')
export const createUser = (data) => client.post('/auth/users/create/', data)

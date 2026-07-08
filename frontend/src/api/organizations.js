import client from './client'

export const getMyOrganization   = ()     => client.get('/organizations/me/')
export const updateMyOrganization = (data) => client.patch('/organizations/me/', data)

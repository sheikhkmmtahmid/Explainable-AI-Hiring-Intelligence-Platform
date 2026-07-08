import client from './client'

export const getApplications      = (params)        => client.get('/applications/', { params })
export const getApplication       = (id)             => client.get(`/applications/${id}/`)
export const updateApplicationStatus = (id, statusValue) =>
  client.patch(`/applications/${id}/update_status/`, { status: statusValue })
export const addApplicationNote   = (id, content)    => client.post(`/applications/${id}/add_note/`, { content })
export const getJobsWithCounts    = (search)         => client.get('/applications/jobs_with_counts/', { params: search ? { search } : {} })

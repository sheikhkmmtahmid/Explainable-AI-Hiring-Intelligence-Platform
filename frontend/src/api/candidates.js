import client from './client'

export const getCandidates    = (params)       => client.get(`/candidates/`, { params })
export const getCandidate     = (id)           => client.get(`/candidates/${id}/`)
export const createCandidate  = (data)         => client.post(`/candidates/`, data)
export const updateCandidate  = (id, data)     => client.patch(`/candidates/${id}/`, data)
export const deleteCandidate  = (id)           => client.delete(`/candidates/${id}/`)
export const uploadCV         = (id, file)     => {
  const form = new FormData()
  form.append('cv', file)
  return client.post(`/candidates/${id}/upload_cv/`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const deleteCV         = (id, cvId)     => client.delete(`/candidates/${id}/cvs/${cvId}/`)
export const getCandidateSkills = (id)         => client.get(`/candidates/${id}/skills/`)

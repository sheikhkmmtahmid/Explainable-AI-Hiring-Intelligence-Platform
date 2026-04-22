import client from './client'

export const getFairnessReport = (jobId) => client.get(`/fairness/${jobId}/`)
export const generateFairnessReport = (jobId, protected_attribute = 'gender') =>
  client.post(`/fairness/${jobId}/`, { protected_attribute })

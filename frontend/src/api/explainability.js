import client from './client'

export const getExplanation = (matchResultId) => client.get(`/explainability/${matchResultId}/`)
export const generateExplanation = (matchResultId, method = 'shap') =>
  client.post(`/explainability/${matchResultId}/`, { method })

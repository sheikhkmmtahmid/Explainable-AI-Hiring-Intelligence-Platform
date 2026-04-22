import client from './client'

export const triggerMatching = (jobId) => client.post(`/matching/trigger/${jobId}/`)
export const getMatchResults = (jobId) => client.get('/matching/results/', { params: { job: jobId } })
export const getMatchResult = (matchId) => client.get(`/matching/results/${matchId}/`)
export const getTopCandidates = (jobId, n = 20) => client.get(`/matching/top-candidates/${jobId}/`, { params: { n } })

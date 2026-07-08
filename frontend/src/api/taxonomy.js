import client from './client'

export const searchSkills        = (query)              => client.get('/taxonomy/skills/', { params: { search: query, page_size: 15 } })
export const proposeSkill        = (name)                => client.post('/taxonomy/skills/propose/', { name })
export const listPendingSkills   = (status = 'pending')  => client.get('/taxonomy/pending-skills/', { params: { status, page_size: 100 } })
export const reviewPendingSkill  = (id, action, category) => client.post(`/taxonomy/pending-skills/${id}/review/`, { action, category })

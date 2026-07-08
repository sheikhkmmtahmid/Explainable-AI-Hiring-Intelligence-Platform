import client from './client'

export const getJobs   = (params)     => client.get(`/jobs/`, { params })
export const getJob    = (id)         => client.get(`/jobs/${id}/`)
export const createJob = (data)       => client.post(`/jobs/`, data)
export const updateJob = (id, data)   => client.patch(`/jobs/${id}/`, data)
export const deleteJob = (id)         => client.delete(`/jobs/${id}/`)
export const closeJob  = (id)         => client.post(`/jobs/${id}/close/`)
export const setJobSkills    = (id, skills)     => client.post(`/jobs/${id}/set_skills/`, { skills })
export const removeJobSkill  = (id, skillName)  => client.post(`/jobs/${id}/remove_skill/`, { skill_name: skillName })

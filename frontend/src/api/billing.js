import client from './client'

export const getPlans             = ()                => client.get('/billing/plans/')
export const getProviders         = ()                => client.get('/billing/providers/')
export const getSubscription      = ()                => client.get('/billing/subscription/')
export const subscribe            = (planId, providerCode) => client.post('/billing/subscribe/', { plan_id: planId, provider_code: providerCode })
export const submitPaymentProof   = (paymentId, data) => client.post(`/billing/payments/${paymentId}/submit-proof/`, data)
export const getPendingPayments   = ()                => client.get('/billing/payments/pending-review/')
export const reviewPayment        = (paymentId, action) => client.post(`/billing/payments/${paymentId}/review/`, { action })

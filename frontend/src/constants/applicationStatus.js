export const STATUS_OPTIONS = [
  { value: '',            label: 'All Statuses' },
  { value: 'applied',     label: 'Applied' },
  { value: 'screening',   label: 'Screening' },
  { value: 'shortlisted', label: 'Shortlisted' },
  { value: 'interview',   label: 'Interview' },
  { value: 'offer',       label: 'Offer Extended' },
  { value: 'hired',       label: 'Hired' },
  { value: 'rejected',    label: 'Rejected' },
  { value: 'withdrawn',   label: 'Withdrawn' },
]

export const STATUS_STYLES = {
  applied:     'bg-surface-500 text-gray-300',
  screening:   'bg-blue-500/15 text-blue-400',
  shortlisted: 'bg-gold-500/15 text-gold-400',
  interview:   'bg-purple-500/15 text-purple-400',
  offer:       'bg-scarlet-500/15 text-scarlet-400',
  hired:       'bg-emerald-500/15 text-emerald-400',
  rejected:    'bg-red-500/15 text-red-400',
  withdrawn:   'bg-surface-500 text-gray-500',
}

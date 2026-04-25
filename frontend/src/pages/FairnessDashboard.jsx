import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { AlertTriangle, CheckCircle2, RefreshCw } from 'lucide-react'
import LoadingSpinner from '../components/LoadingSpinner'
import { getJobs } from '../api/jobs'
import { getFairnessReport, generateFairnessReport } from '../api/fairness'
import toast from 'react-hot-toast'

const ATTRIBUTES = ['gender', 'age_range', 'ethnicity', 'disability_status']

export default function FairnessDashboard() {
  const [jobs, setJobs] = useState([])
  const [selectedJob, setSelectedJob] = useState('')
  const [attribute, setAttribute] = useState('gender')
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    // Load manual jobs first so they appear at the top, then fill with other active jobs
    Promise.all([
      getJobs({ source: 'manual', ordering: '-created_at', page_size: 100 }),
      getJobs({ status: 'active', ordering: '-posted_at', page_size: 100 }),
    ]).then(([manual, active]) => {
      const manualList = manual.data.results ?? manual.data
      const activeList = active.data.results ?? active.data
      // Merge: manual jobs first, then others not already in manual
      const manualIds = new Set(manualList.map(j => j.id))
      const merged = [...manualList, ...activeList.filter(j => !manualIds.has(j.id))]
      setJobs(merged)
      if (merged.length > 0) setSelectedJob(String(merged[0].id))
    })
  }, [])

  useEffect(() => {
    if (!selectedJob) return
    setLoading(true)
    getFairnessReport(selectedJob)
      .then(({ data }) => setReports(Array.isArray(data) ? data : [data]))
      .catch(() => setReports([]))
      .finally(() => setLoading(false))
  }, [selectedJob])

  const generate = async () => {
    if (!selectedJob) return
    setGenerating(true)
    try {
      const { data } = await generateFairnessReport(selectedJob, attribute)
      setReports(r => [...r.filter(x => x.protected_attribute !== attribute), data])
      toast.success('Fairness report generated')
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Failed to generate report'
      toast.error(msg)
    } finally {
      setGenerating(false)
    }
  }

  const activeReport = reports.find(r => r.protected_attribute === attribute)

  // subgroups must be an array — guard against API returning a dict (old shape)
  const subgroups = Array.isArray(activeReport?.subgroups) ? activeReport.subgroups : []

  const chartData = subgroups.map(sg => ({
    name: sg.group_value,
    rate: parseFloat((sg.selection_rate * 100).toFixed(1)),
    di: parseFloat((sg.disparate_impact ?? 0).toFixed(2)),
  }))

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-title">Fairness & Bias Analysis</h1>
        <p className="text-gray-500 text-sm mt-1">Monitor hiring equity across demographic groups</p>
      </div>

      {/* Controls */}
      <div className="card p-5">
        <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-end gap-3">
          <div className="flex-1 min-w-0 sm:min-w-48">
            <label className="label">Job Position</label>
            <select className="input" value={selectedJob} onChange={e => setSelectedJob(e.target.value)}>
              {jobs.map(j => <option key={j.id} value={j.id}>{j.title} — {j.company}</option>)}
            </select>
          </div>
          <div className="sm:w-44">
            <label className="label">Protected Attribute</label>
            <select className="input" value={attribute} onChange={e => setAttribute(e.target.value)}>
              {ATTRIBUTES.map(a => <option key={a} value={a}>{a.replace('_', ' ')}</option>)}
            </select>
          </div>
          <button onClick={generate} disabled={generating || !selectedJob} className="btn-primary w-full sm:w-auto">
            <RefreshCw className="w-4 h-4" /> {generating ? 'Analyzing…' : 'Run Analysis'}
          </button>
        </div>
      </div>

      {loading || generating ? (
        <LoadingSpinner className="py-16" />
      ) : !activeReport ? (
        <div className="card text-center py-16">
          <AlertTriangle className="w-10 h-10 text-gray-600 mx-auto mb-3" />
          <p className="text-gray-400">No fairness report yet for this attribute.</p>
          <p className="text-gray-600 text-sm mt-1">Select a job and attribute, then click "Run Analysis".</p>
        </div>
      ) : (
        <>
          {/* Summary metric */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="card p-5 text-center">
              <p className="text-xs text-gray-500 mb-1">Disparate Impact Ratio</p>
              <p className={`text-3xl font-bold ${(activeReport.disparate_impact ?? 1) >= 0.8 ? 'text-emerald-400' : 'text-scarlet-500'}`}>
                {(activeReport.disparate_impact ?? 0).toFixed(3)}
              </p>
              <div className="flex items-center justify-center gap-1 mt-2">
                {(activeReport.disparate_impact ?? 1) >= 0.8
                  ? <><CheckCircle2 className="w-4 h-4 text-emerald-400" /><span className="text-xs text-emerald-400">Passes 4/5 rule</span></>
                  : <><AlertTriangle className="w-4 h-4 text-scarlet-400" /><span className="text-xs text-scarlet-400">Fails 4/5 rule (&lt; 0.8)</span></>
                }
              </div>
            </div>
            <div className="card p-5 text-center">
              <p className="text-xs text-gray-500 mb-1">Demographic Parity Diff</p>
              <p className="text-3xl font-bold text-white">{(activeReport.demographic_parity_difference ?? 0).toFixed(3)}</p>
              <p className="text-xs text-gray-600 mt-2">Ideal: 0.00</p>
            </div>
            <div className="card p-5 text-center">
              <p className="text-xs text-gray-500 mb-1">Bias Flag</p>
              <p className={`text-3xl font-bold ${activeReport.bias_detected ? 'text-scarlet-400' : 'text-emerald-400'}`}>
                {activeReport.bias_detected ? 'DETECTED' : 'NONE'}
              </p>
              <p className="text-xs text-gray-600 mt-2">Attribute: {activeReport.protected_attribute}</p>
            </div>
          </div>

          {/* Bar chart */}
          {chartData.length > 0 && (
            <div className="card p-5">
              <h2 className="section-title mb-4">Selection Rate by {attribute.replace('_', ' ')}</h2>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2E2E2E" />
                  <XAxis dataKey="name" tick={{ fill: '#888', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#888', fontSize: 12 }} tickFormatter={v => `${v}%`} />
                  <Tooltip
                    contentStyle={{ background: '#1E1E1E', border: '1px solid #2E2E2E', borderRadius: 8 }}
                    labelStyle={{ color: '#fff' }}
                    formatter={(v) => [`${v}%`, 'Selection Rate']}
                  />
                  <ReferenceLine y={80} stroke="#D3A625" strokeDasharray="4 4" label={{ value: '80% threshold', fill: '#D3A625', fontSize: 11 }} />
                  <Bar dataKey="rate" fill="#AE0001" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Subgroup table */}
          {subgroups.length > 0 && (
            <div className="card overflow-hidden">
              <div className="px-5 py-4 border-b border-surface-400">
                <h2 className="section-title">Subgroup Breakdown</h2>
              </div>
              <div className="overflow-x-auto -mx-px">
                <table className="w-full text-sm min-w-[520px]">
                  <thead>
                    <tr className="border-b border-surface-400">
                      {['Group', 'Total', 'Selected', 'Selection Rate', 'Disparate Impact', 'Status'].map(h => (
                        <th key={h} className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-400">
                    {subgroups.map(sg => (
                      <tr key={sg.group_value} className="hover:bg-surface-600 transition-colors">
                        <td className="px-5 py-3 font-medium text-white capitalize">{sg.group_value}</td>
                        <td className="px-5 py-3 text-gray-400">{sg.total_count}</td>
                        <td className="px-5 py-3 text-gray-400">{sg.selected_count}</td>
                        <td className="px-5 py-3 text-white">{(sg.selection_rate * 100).toFixed(1)}%</td>
                        <td className="px-5 py-3 text-white">{(sg.disparate_impact ?? 0).toFixed(3)}</td>
                        <td className="px-5 py-3">
                          {(sg.disparate_impact ?? 1) >= 0.8
                            ? <span className="badge bg-emerald-500/15 text-emerald-400">OK</span>
                            : <span className="badge bg-scarlet-500/15 text-scarlet-400">Bias Risk</span>
                          }
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

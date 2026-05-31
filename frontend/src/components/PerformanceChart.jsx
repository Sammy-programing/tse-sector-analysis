import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function PerformanceChart({ data }) {
  const chartData = data.slice(0, 10).map(sector => ({
    name: sector.sector_name,
    perf_1d: sector.perf_1d || 0,
    perf_5d: sector.perf_5d || 0,
    vs_topix: sector.vs_topix_1d || 0
  }))

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
        <YAxis />
        <Tooltip formatter={(value) => `${value?.toFixed(2)}%`} />
        <Legend />
        <Line type="monotone" dataKey="perf_1d" stroke="#3b82f6" name="1日 (%)" />
        <Line type="monotone" dataKey="perf_5d" stroke="#10b981" name="5日 (%)" />
        <Line type="monotone" dataKey="vs_topix" stroke="#f59e0b" name="TOPIX比 (%)" />
      </LineChart>
    </ResponsiveContainer>
  )
}

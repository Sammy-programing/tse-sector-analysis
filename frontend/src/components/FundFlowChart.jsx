import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function FundFlowChart({ data }) {
  const chartData = data.slice(0, 10).map(sector => ({
    name: sector.sector_name,
    trading_value: sector.trading_value_jpy / 1e9,
    change: sector.change_1d_pct
  }))

  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
        <YAxis />
        <Tooltip formatter={(value) => `¥${value.toFixed(1)}B`} />
        <Legend />
        <Bar dataKey="trading_value" fill="#3b82f6" name="売買代金 (十億円)" />
      </BarChart>
    </ResponsiveContainer>
  )
}

import { useQuery } from 'react-query'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'

const API_BASE_URL = '/api'

export default function SectorHeatmap({ analysisDate }) {
  const { data: performanceData, isLoading } = useQuery(
    ['heatmap', analysisDate],
    async () => {
      const response = await fetch(`${API_BASE_URL}/sectors/performance?date=${analysisDate}`)
      if (!response.ok) throw new Error('Failed to fetch performance data')
      return response.json()
    }
  )

  if (isLoading) {
    return <div className="text-center py-8">データ読み込み中...</div>
  }

  const sectors = performanceData?.sectors || []

  // パフォーマンスランキングデータを準備
  const heatmapData = sectors.slice(0, 15).map(sector => ({
    name: sector.sector_name,
    perf_1d: sector.perf_1d || 0,
    perf_5d: sector.perf_5d || 0,
    perf_20d: sector.perf_20d || 0,
    perf_60d: sector.perf_60d || 0
  }))

  // カラー取得関数
  const getColor = (value) => {
    if (value > 5) return '#059669' // 濃い緑
    if (value > 2) return '#10b981' // 緑
    if (value > 0) return '#a3e635' // 薄い緑
    if (value > -2) return '#fca5a5' // 薄い赤
    if (value > -5) return '#f87171' // 赤
    return '#dc2626' // 濃い赤
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">
          セクター別パフォーマンスランキング
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left font-semibold text-gray-900">セクター</th>
                <th className="px-4 py-2 text-center font-semibold text-gray-900">1日</th>
                <th className="px-4 py-2 text-center font-semibold text-gray-900">5日</th>
                <th className="px-4 py-2 text-center font-semibold text-gray-900">20日</th>
                <th className="px-4 py-2 text-center font-semibold text-gray-900">60日</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {heatmapData.map((sector, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{sector.name}</td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className="inline-block px-3 py-1 rounded font-semibold text-white"
                      style={{ backgroundColor: getColor(sector.perf_1d) }}
                    >
                      {sector.perf_1d >= 0 ? '+' : ''}{sector.perf_1d.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className="inline-block px-3 py-1 rounded font-semibold text-white"
                      style={{ backgroundColor: getColor(sector.perf_5d) }}
                    >
                      {sector.perf_5d >= 0 ? '+' : ''}{sector.perf_5d.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className="inline-block px-3 py-1 rounded font-semibold text-white"
                      style={{ backgroundColor: getColor(sector.perf_20d) }}
                    >
                      {sector.perf_20d >= 0 ? '+' : ''}{sector.perf_20d.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className="inline-block px-3 py-1 rounded font-semibold text-white"
                      style={{ backgroundColor: getColor(sector.perf_60d) }}
                    >
                      {sector.perf_60d >= 0 ? '+' : ''}{sector.perf_60d.toFixed(2)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

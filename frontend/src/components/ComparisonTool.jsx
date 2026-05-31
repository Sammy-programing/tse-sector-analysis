import { useState } from 'react'
import { useQuery } from 'react-query'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const API_BASE_URL = '/api'

export default function ComparisonTool({ analysisDate }) {
  const [selectedSectors, setSelectedSectors] = useState([])

  const { data: performanceData, isLoading } = useQuery(
    ['comparison', analysisDate],
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

  const toggleSector = (sectorId) => {
    setSelectedSectors(prev =>
      prev.includes(sectorId)
        ? prev.filter(id => id !== sectorId)
        : [...prev, sectorId].slice(-5) // Max 5 sectors
    )
  }

  const comparisonData = selectedSectors.length > 0
    ? [{
        name: '1日',
        ...selectedSectors.reduce((acc, id) => {
          const sector = sectors.find(s => s.sector_id === id)
          if (sector) acc[sector.sector_name] = sector.perf_1d || 0
          return acc
        }, {})
      }, {
        name: '5日',
        ...selectedSectors.reduce((acc, id) => {
          const sector = sectors.find(s => s.sector_id === id)
          if (sector) acc[sector.sector_name] = sector.perf_5d || 0
          return acc
        }, {})
      }]
    : []

  const selectedSectorNames = selectedSectors
    .map(id => sectors.find(s => s.sector_id === id)?.sector_name)
    .filter(Boolean)

  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-4">
          セクター間パフォーマンス比較
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          最大 5 つのセクターを選択して比較できます
        </p>
      </div>

      {/* セクター選択 */}
      <div className="border rounded-lg p-4 bg-gray-50">
        <p className="text-sm font-semibold text-gray-900 mb-3">
          セクターを選択 ({selectedSectors.length}/5)
        </p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-48 overflow-y-auto">
          {sectors.map(sector => (
            <label
              key={sector.sector_id}
              className="flex items-center gap-2 p-2 hover:bg-white rounded cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selectedSectors.includes(sector.sector_id)}
                onChange={() => toggleSector(sector.sector_id)}
                disabled={!selectedSectors.includes(sector.sector_id) && selectedSectors.length >= 5}
                className="w-4 h-4 rounded cursor-pointer"
              />
              <span className="text-sm text-gray-900">{sector.sector_name}</span>
            </label>
          ))}
        </div>
      </div>

      {/* 比較チャート */}
      {selectedSectors.length > 0 && (
        <div className="space-y-4">
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={comparisonData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
              <Legend />
              {selectedSectorNames.map((sectorName, idx) => {
                const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
                return (
                  <Bar
                    key={sectorName}
                    dataKey={sectorName}
                    fill={colors[idx % colors.length]}
                  />
                )
              })}
            </BarChart>
          </ResponsiveContainer>

          {/* 比較統計テーブル */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left font-semibold text-gray-900">セクター</th>
                  <th className="px-4 py-2 text-center font-semibold text-gray-900">1日</th>
                  <th className="px-4 py-2 text-center font-semibold text-gray-900">5日</th>
                  <th className="px-4 py-2 text-center font-semibold text-gray-900">20日</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {selectedSectors.map(sectorId => {
                  const sector = sectors.find(s => s.sector_id === sectorId)
                  return (
                    <tr key={sectorId} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">
                        {sector?.sector_name}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={sector?.perf_1d >= 0 ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
                          {sector?.perf_1d >= 0 ? '+' : ''}{sector?.perf_1d?.toFixed(2)}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={sector?.perf_5d >= 0 ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
                          {sector?.perf_5d >= 0 ? '+' : ''}{sector?.perf_5d?.toFixed(2)}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={sector?.perf_20d >= 0 ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
                          {sector?.perf_20d >= 0 ? '+' : ''}{sector?.perf_20d?.toFixed(2)}%
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {selectedSectors.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          比較するセクターを選択してください
        </div>
      )}
    </div>
  )
}

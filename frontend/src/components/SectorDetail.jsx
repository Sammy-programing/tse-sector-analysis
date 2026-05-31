import { useQuery } from 'react-query'
import { ArrowLeft } from 'lucide-react'

const API_BASE_URL = '/api'

export default function SectorDetail({ sectorId, analysisDate, onBack }) {
  const { data: sectorData, isLoading } = useQuery(
    ['sectorDetail', sectorId, analysisDate],
    async () => {
      const response = await fetch(
        `${API_BASE_URL}/sectors/${sectorId}/history?start_date=2026-05-01&end_date=${analysisDate}`
      )
      if (!response.ok) throw new Error('Failed to fetch sector detail')
      return response.json()
    }
  )

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="text-lg text-gray-600">データ読み込み中...</div>
      </div>
    )
  }

  const sector = sectorData || {}

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-4">
          <button
            onClick={onBack}
            className="p-2 hover:bg-gray-100 rounded-lg transition"
          >
            <ArrowLeft className="w-6 h-6 text-gray-600" />
          </button>
          <h1 className="text-3xl font-bold text-gray-900 ml-4">
            {sector.sector_name || `Sector ${sectorId}`}
          </h1>
        </div>
      </div>

      {/* 詳細情報 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          セクター詳細
        </h2>

        {sector.data && sector.data.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    日付
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    売買代金 (十億円)
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    1日 (%)
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    5日 (%)
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {sector.data.map((item, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {item.date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ¥{(item.fund_flow_jpy / 1e9).toFixed(1)}B
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={item.perf_1d >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {item.perf_1d >= 0 ? '+' : ''}{item.perf_1d?.toFixed(2)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={item.perf_5d >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {item.perf_5d >= 0 ? '+' : ''}{item.perf_5d?.toFixed(2)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-600 text-center py-8">データがありません</p>
        )}
      </div>
    </div>
  )
}

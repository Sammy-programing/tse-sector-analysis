import { useQuery } from 'react-query'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const API_BASE_URL = '/api'

export default function VolumeAnalysis({ analysisDate }) {
  const { data: performanceData, isLoading } = useQuery(
    ['volumeAnalysis', analysisDate],
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

  // 出来高データを準備（降順でソート）
  const volumeData = sectors
    .slice(0, 10)
    .sort((a, b) => (b.trading_value_jpy || 0) - (a.trading_value_jpy || 0))
    .map(sector => ({
      name: sector.sector_name,
      volume: (sector.trading_value_jpy || 0) / 1e9
    }))

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-6">
        セクター別出来高分析
      </h3>

      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={volumeData}>
          <defs>
            <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
          <YAxis label={{ value: '売買代金 (十億円)', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            formatter={(value) => `¥${value.toFixed(1)}B`}
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc' }}
          />
          <Area
            type="monotone"
            dataKey="volume"
            stroke="#3b82f6"
            fillOpacity={1}
            fill="url(#colorVolume)"
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* 出来高統計 */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-lg p-4">
          <p className="text-sm text-gray-600">平均売買代金</p>
          <p className="text-2xl font-bold text-blue-600">
            ¥{(volumeData.reduce((sum, d) => sum + d.volume, 0) / volumeData.length).toFixed(1)}B
          </p>
        </div>
        <div className="bg-green-50 rounded-lg p-4">
          <p className="text-sm text-gray-600">最大売買代金</p>
          <p className="text-2xl font-bold text-green-600">
            ¥{Math.max(...volumeData.map(d => d.volume)).toFixed(1)}B
          </p>
        </div>
        <div className="bg-purple-50 rounded-lg p-4">
          <p className="text-sm text-gray-600">合計売買代金</p>
          <p className="text-2xl font-bold text-purple-600">
            ¥{volumeData.reduce((sum, d) => sum + d.volume, 0).toFixed(1)}B
          </p>
        </div>
      </div>
    </div>
  )
}

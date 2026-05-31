import { useQuery } from 'react-query'
import { TrendingUp, TrendingDown } from 'lucide-react'
import FundFlowChart from './FundFlowChart'
import PerformanceChart from './PerformanceChart'

const API_BASE_URL = '/api'

export default function Dashboard({ analysisDate, onSelectSector }) {
  // 資金流入データを取得
  const { data: fundFlowData, isLoading: fundFlowLoading } = useQuery(
    ['fundFlow', analysisDate],
    async () => {
      const response = await fetch(`${API_BASE_URL}/sectors/fund-flow?date=${analysisDate}`)
      if (!response.ok) throw new Error('Failed to fetch fund flow data')
      return response.json()
    }
  )

  // パフォーマンスデータを取得
  const { data: performanceData, isLoading: performanceLoading } = useQuery(
    ['performance', analysisDate],
    async () => {
      const response = await fetch(`${API_BASE_URL}/sectors/performance?date=${analysisDate}`)
      if (!response.ok) throw new Error('Failed to fetch performance data')
      return response.json()
    }
  )

  if (fundFlowLoading || performanceLoading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="text-lg text-gray-600">データ読み込み中...</div>
      </div>
    )
  }

  const fundFlowSectors = fundFlowData?.sectors || []
  const inflow = fundFlowSectors.filter(s => s.change_1d_pct > 0)
  const outflow = fundFlowSectors.filter(s => s.change_1d_pct < 0)

  return (
    <div className="space-y-8">
      {/* 資金流入セクション */}
      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
          <TrendingUp className="text-green-500 mr-2" />
          資金流入ランキング
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <h3 className="text-lg font-semibold text-green-600 mb-4">
              流入上位 5 セクター
            </h3>
            <div className="space-y-3">
              {inflow.slice(0, 5).map((sector) => (
                <div
                  key={sector.sector_id}
                  className="p-4 bg-green-50 rounded-lg cursor-pointer hover:bg-green-100 transition"
                  onClick={() => onSelectSector(sector.sector_id)}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-semibold text-gray-900">
                        {sector.rank}. {sector.sector_name}
                      </p>
                      <p className="text-sm text-gray-600">
                        売買代金: ¥{(sector.trading_value_jpy / 1e9).toFixed(1)}B
                      </p>
                    </div>
                    <span className="text-green-600 font-bold">
                      {sector.change_1d_pct > 0 ? '+' : ''}{sector.change_1d_pct.toFixed(2)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-red-600 mb-4">
              流出上位 5 セクター
            </h3>
            <div className="space-y-3">
              {outflow.slice(0, 5).map((sector) => (
                <div
                  key={sector.sector_id}
                  className="p-4 bg-red-50 rounded-lg cursor-pointer hover:bg-red-100 transition"
                  onClick={() => onSelectSector(sector.sector_id)}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-semibold text-gray-900">
                        {sector.rank}. {sector.sector_name}
                      </p>
                      <p className="text-sm text-gray-600">
                        売買代金: ¥{(sector.trading_value_jpy / 1e9).toFixed(1)}B
                      </p>
                    </div>
                    <span className="text-red-600 font-bold">
                      {sector.change_1d_pct.toFixed(2)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* パフォーマンスセクション */}
      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          セクター別パフォーマンス
        </h2>

        <PerformanceChart data={performanceData?.sectors || []} />
      </section>

      {/* チャートセクション */}
      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          資金流入推移
        </h2>

        <FundFlowChart data={fundFlowSectors} />
      </section>
    </div>
  )
}

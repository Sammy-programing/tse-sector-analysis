import { useQuery } from 'react-query'
import { Download } from 'lucide-react'

const API_BASE_URL = '/api'

export default function ExportButton({ analysisDate }) {
  const { data: fundFlowData } = useQuery(
    ['fundFlow', analysisDate],
    async () => {
      const response = await fetch(`${API_BASE_URL}/sectors/fund-flow?date=${analysisDate}`)
      if (!response.ok) throw new Error('Failed to fetch fund flow data')
      return response.json()
    }
  )

  const { data: performanceData } = useQuery(
    ['performance', analysisDate],
    async () => {
      const response = await fetch(`${API_BASE_URL}/sectors/performance?date=${analysisDate}`)
      if (!response.ok) throw new Error('Failed to fetch performance data')
      return response.json()
    }
  )

  const handleExport = () => {
    const fundFlowSectors = fundFlowData?.sectors || []
    const performanceSectors = performanceData?.sectors || []

    // データを結合して CSV 形式に変換
    const csvContent = [
      ['日付', analysisDate],
      [],
      ['セクター分析データ'],
      ['セクター', '売買代金(十億円)', '1日変化率(%)', '5日変化率(%)', '20日変化率(%)', '60日変化率(%)'],
      ...fundFlowSectors.map(sector => {
        const perfSector = performanceSectors.find(p => p.sector_id === sector.sector_id) || {}
        return [
          sector.sector_name,
          (sector.trading_value_jpy / 1e9).toFixed(1),
          sector.change_1d_pct.toFixed(2),
          perfSector.perf_5d?.toFixed(2) || 'N/A',
          perfSector.perf_20d?.toFixed(2) || 'N/A',
          perfSector.perf_60d?.toFixed(2) || 'N/A'
        ]
      })
    ]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n')

    // CSV ファイルをダウンロード
    const element = document.createElement('a')
    element.setAttribute('href', `data:text/csv;charset=utf-8,${encodeURIComponent(csvContent)}`)
    element.setAttribute('download', `sector-analysis-${analysisDate}.csv`)
    element.style.display = 'none'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  return (
    <button
      onClick={handleExport}
      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold"
    >
      <Download className="w-4 h-4" />
      CSV エクスポート
    </button>
  )
}

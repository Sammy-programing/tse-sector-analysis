import { useState } from 'react'
import Dashboard from './components/Dashboard'
import SectorDetail from './components/SectorDetail'
import './App.css'

export default function App() {
  const [selectedSectorId, setSelectedSectorId] = useState(null)
  const [analysisDate, setAnalysisDate] = useState(new Date().toISOString().split('T')[0])

  const handleSelectSector = (sectorId) => {
    setSelectedSectorId(sectorId)
  }

  const handleBackToDashboard = () => {
    setSelectedSectorId(null)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">
              東証セクター資金流入分析
            </h1>
            <div className="text-right">
              <p className="text-sm text-gray-600">分析日付</p>
              <input
                type="date"
                value={analysisDate}
                onChange={(e) => setAnalysisDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {selectedSectorId ? (
          <SectorDetail
            sectorId={selectedSectorId}
            analysisDate={analysisDate}
            onBack={handleBackToDashboard}
          />
        ) : (
          <Dashboard
            analysisDate={analysisDate}
            onSelectSector={handleSelectSector}
          />
        )}
      </main>

      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-gray-600 text-sm">
            © 2026 東証セクター資金流入分析 - Powered by J-Quants API
          </p>
        </div>
      </footer>
    </div>
  )
}

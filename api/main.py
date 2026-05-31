"""
FastAPI メインアプリケーション
セクター資金流入分析 API サーバー
"""
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from data_ingestion.database import Database

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI アプリケーション
app = FastAPI(
    title="東証セクター資金流入分析 API",
    description="セクター別資金流入・パフォーマンス分析 API",
    version="1.0.0"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# リクエスト/レスポンス モデル
class SectorFundFlow(BaseModel):
    """セクター資金流入"""
    sector_id: int
    sector_name: str
    trading_value_jpy: int
    rank: int
    change_1d_pct: float


class SectorPerformance(BaseModel):
    """セクター別パフォーマンス"""
    sector_id: int
    sector_name: str
    perf_1d: Optional[float]
    perf_5d: Optional[float]
    perf_20d: Optional[float]
    perf_60d: Optional[float]
    vs_topix_1d: Optional[float]


class FundFlowResponse(BaseModel):
    """資金流入レスポンス"""
    date: date
    sectors: List[SectorFundFlow]


class PerformanceResponse(BaseModel):
    """パフォーマンスレスポンス"""
    date: date
    topix_perf_1d: Optional[float]
    sectors: List[SectorPerformance]


# API エンドポイント

@app.get("/", tags=["Root"])
def root():
    """ルートエンドポイント"""
    return {
        "message": "東証セクター資金流入分析 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health", tags=["Health"])
def health_check():
    """ヘルスチェック"""
    return {"status": "OK"}


@app.get("/api/sectors/fund-flow", response_model=FundFlowResponse, tags=["Sectors"])
def get_fund_flow(
    date_param: Optional[date] = Query(None, alias="date", description="分析日付（YYYY-MM-DD）")
):
    """
    セクター資金流入データを取得

    クエリパラメータ：
    - date: 分析日付（省略時は前営業日）

    レスポンス：
    - sectors: セクター資金流入ランキング
    """
    try:
        db = Database()
        target_date = date_param or (date.today() - timedelta(days=1))
        sectors_data = db.get_sector_fund_flow(target_date)

        return {
            "date": target_date,
            "sectors": [
                SectorFundFlow(
                    sector_id=s['sector_id'],
                    sector_name=s['sector_name'],
                    trading_value_jpy=s['trading_value_jpy'],
                    rank=s['rank'],
                    change_1d_pct=s['change_1d_pct']
                )
                for s in sectors_data
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching fund flow data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/sectors/performance", response_model=PerformanceResponse, tags=["Sectors"])
def get_performance(
    date_param: Optional[date] = Query(None, alias="date", description="分析日付（YYYY-MM-DD）")
):
    """
    セクター別パフォーマンスを取得

    クエリパラメータ：
    - date: 分析日付（省略時は前営業日）

    レスポンス：
    - sectors: セクター別パフォーマンス（1d/5d/20d/60d）
    - topix_perf_1d: TOPIX 1日パフォーマンス
    """
    try:
        db = Database()
        target_date = date_param or (date.today() - timedelta(days=1))
        sectors_data = db.get_sector_performance(target_date)

        return {
            "date": target_date,
            "topix_perf_1d": None,
            "sectors": [
                SectorPerformance(
                    sector_id=s['sector_id'],
                    sector_name=s['sector_name'],
                    perf_1d=s['perf_1d'],
                    perf_5d=s['perf_5d'],
                    perf_20d=s['perf_20d'],
                    perf_60d=s['perf_60d'],
                    vs_topix_1d=s['vs_topix_1d']
                )
                for s in sectors_data
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching performance data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/sectors/{sector_id}/history", tags=["Sectors"])
def get_sector_history(
    sector_id: int,
    start_date: Optional[date] = Query(None, description="開始日付"),
    end_date: Optional[date] = Query(None, description="終了日付")
):
    """
    セクター詳細履歴を取得

    パスパラメータ：
    - sector_id: セクター ID

    クエリパラメータ：
    - start_date: 開始日付
    - end_date: 終了日付
    """
    try:
        db = Database()
        start = start_date or (date.today() - timedelta(days=30))
        end = end_date or date.today()
        history_data = db.get_sector_history(sector_id, start, end)

        sector_name = ""
        if history_data:
            sector_name = "Sector"  # TODO: セクター名を取得
        else:
            all_sectors = db.get_all_sectors()
            for s in all_sectors:
                if s['sector_id'] == sector_id:
                    sector_name = s['sector_name']
                    break

        return {
            "sector_id": sector_id,
            "sector_name": sector_name,
            "data": history_data
        }
    except Exception as e:
        logger.error(f"Error fetching sector history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/metadata/sectors", tags=["Metadata"])
def get_sectors_metadata():
    """
    セクターメタデータを取得（ID と名前のマッピング）
    """
    try:
        db = Database()
        sectors_data = db.get_all_sectors()

        return {
            "sectors": [
                {"sector_id": s['sector_id'], "sector_name": s['sector_name']}
                for s in sectors_data
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching sectors metadata: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

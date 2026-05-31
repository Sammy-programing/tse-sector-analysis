"""
FastAPI メインアプリケーション
セクター資金流入分析 API サーバー
"""
import logging
from datetime import date
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    - date: 分析日付（省略時は最新）

    レスポンス：
    - sectors: セクター資金流入ランキング
    """
    try:
        # TODO: データベースからデータを取得
        # 現在はダミーレスポンス
        return {
            "date": date_param or date.today(),
            "sectors": [
                {
                    "sector_id": 1,
                    "sector_name": "テクノロジー",
                    "trading_value_jpy": 5000000000,
                    "rank": 1,
                    "change_1d_pct": 15.5
                },
                {
                    "sector_id": 2,
                    "sector_name": "金融",
                    "trading_value_jpy": 3000000000,
                    "rank": 2,
                    "change_1d_pct": 8.2
                }
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
    - date: 分析日付（省略時は最新）

    レスポンス：
    - sectors: セクター別パフォーマンス（1d/5d/20d/60d）
    - topix_perf_1d: TOPIX 1日パフォーマンス
    """
    try:
        # TODO: データベースからデータを取得
        # 現在はダミーレスポンス
        return {
            "date": date_param or date.today(),
            "topix_perf_1d": 1.2,
            "sectors": [
                {
                    "sector_id": 1,
                    "sector_name": "テクノロジー",
                    "perf_1d": 2.5,
                    "perf_5d": 1.8,
                    "perf_20d": -0.5,
                    "perf_60d": 8.3,
                    "vs_topix_1d": 1.3
                },
                {
                    "sector_id": 2,
                    "sector_name": "金融",
                    "perf_1d": 0.5,
                    "perf_5d": -0.2,
                    "perf_20d": -2.1,
                    "perf_60d": -5.0,
                    "vs_topix_1d": -0.7
                }
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
        # TODO: データベースからデータを取得
        return {
            "sector_id": sector_id,
            "sector_name": f"Sector {sector_id}",
            "data": [
                {
                    "date": "2026-05-30",
                    "fund_flow_jpy": 5000000000,
                    "perf_1d": 2.5,
                    "perf_5d": 1.8
                }
            ]
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
        # TODO: データベースからデータを取得
        return {
            "sectors": [
                {"id": 1, "name": "テクノロジー"},
                {"id": 2, "name": "金融"},
                {"id": 3, "name": "エネルギー"}
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching sectors metadata: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

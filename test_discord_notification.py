#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script: Analyze last Friday's data and send Discord notification
"""
import os
import sys
from datetime import datetime, timedelta, date
from dotenv import load_dotenv

load_dotenv()

from analysis.discord_notifier import DiscordNotifier

def main():
    # Calculate last Friday's date
    today = datetime(2026, 5, 31)
    last_friday = today - timedelta(days=(today.weekday() - 4) % 7 or 7)
    analysis_date = last_friday.strftime("%Y-%m-%d")
    analysis_date_obj = last_friday.date()

    print(f"Analysis Date: {analysis_date} (Friday)")
    print("=" * 60)

    # Create sample analysis data
    print("Preparing test data...")

    sample_sectors = [
        {
            "sector_id": 1,
            "sector_name": "Electric Appliances",
            "trading_value_jpy": 2500000000000,
            "change_1d_pct": 1.5,
            "perf_1d": 1.5,
            "perf_5d": 3.2,
            "perf_20d": 5.8,
            "vs_topix_1d": 0.8,
            "score": 2500000000000
        },
        {
            "sector_id": 2,
            "sector_name": "Chemicals",
            "trading_value_jpy": 1800000000000,
            "change_1d_pct": 0.8,
            "perf_1d": 0.8,
            "perf_5d": 2.1,
            "perf_20d": 3.5,
            "vs_topix_1d": -0.1,
            "score": 1800000000000
        },
        {
            "sector_id": 3,
            "sector_name": "Banks",
            "trading_value_jpy": 1200000000000,
            "change_1d_pct": -1.2,
            "perf_1d": -1.2,
            "perf_5d": -2.3,
            "perf_20d": -1.8,
            "vs_topix_1d": -2.0,
            "score": -1200000000000
        },
        {
            "sector_id": 4,
            "sector_name": "Transportation Equipment",
            "trading_value_jpy": 950000000000,
            "change_1d_pct": -0.5,
            "perf_1d": -0.5,
            "perf_5d": -1.2,
            "perf_20d": 2.1,
            "vs_topix_1d": -1.3,
            "score": -950000000000
        },
        {
            "sector_id": 5,
            "sector_name": "Machinery",
            "trading_value_jpy": 1500000000000,
            "change_1d_pct": 2.3,
            "perf_1d": 2.3,
            "perf_5d": 4.5,
            "perf_20d": 6.2,
            "vs_topix_1d": 1.2,
            "score": 1500000000000
        }
    ]

    print(f"✓ Prepared test data for {len(sample_sectors)} sectors\n")

    # Build analysis data
    print("Building analysis data...")

    inflow = sorted([s for s in sample_sectors if s["change_1d_pct"] > 0],
                    key=lambda x: x["score"], reverse=True)
    outflow = sorted([s for s in sample_sectors if s["change_1d_pct"] < 0],
                     key=lambda x: x["score"])

    top_inflow_sectors = [{"sector_id": s["sector_id"], "score": s["score"]} for s in inflow]
    top_outflow_sectors = [{"sector_id": s["sector_id"], "score": s["score"]} for s in outflow]

    sector_names = {s["sector_id"]: s["sector_name"] for s in sample_sectors}

    performance_changes = {
        "1d": {s["sector_id"]: s["perf_1d"] for s in sample_sectors},
        "5d": {s["sector_id"]: s["perf_5d"] for s in sample_sectors}
    }

    print("✓ Analysis data ready\n")
    print("=" * 60)

    # Send Discord notification
    print("\nSending Discord notification...")
    webhook_url = os.getenv("DISCORD_WEBHOOK")

    if not webhook_url:
        print("WARNING: DISCORD_WEBHOOK not set in .env")
        print("Preview of message that would be sent:\n")
        print("-" * 60)
        print_preview(analysis_date, sample_sectors, top_inflow_sectors, top_outflow_sectors)
        print("-" * 60)
        return

    try:
        notifier = DiscordNotifier(webhook_url)

        success = notifier.send_daily_summary(
            analysis_date=analysis_date_obj,
            top_inflow_sectors=top_inflow_sectors,
            top_outflow_sectors=top_outflow_sectors,
            performance_changes=performance_changes,
            sector_names=sector_names
        )

        if success:
            print("✓ Discord notification sent successfully!\n")
            print("Message sent:")
            print("-" * 60)
            print_preview(analysis_date, sample_sectors, top_inflow_sectors, top_outflow_sectors)
            print("-" * 60)
        else:
            print("✗ Failed to send Discord notification")
            sys.exit(1)

    except Exception as e:
        print(f"✗ Discord error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Test completed successfully!")

def print_preview(analysis_date, sectors, top_inflow, top_outflow):
    """Display notification content preview"""
    sector_dict = {s["sector_id"]: s["sector_name"] for s in sectors}

    print(f"\n[Discord Message Preview]\n")
    print(f"Sector Market Analysis - {analysis_date}\n")

    print("Top 5 Inflow Sectors:")
    for i, sector_data in enumerate(top_inflow[:5], 1):
        sector_id = sector_data.get('sector_id')
        sector_name = sector_dict.get(sector_id, f"Sector {sector_id}")
        score = sector_data.get('score', 0) / 1e9
        print(f"  {i}. {sector_name}: JPY {score:.1f}B")

    print("\nTop 5 Outflow Sectors:")
    for i, sector_data in enumerate(top_outflow[:5], 1):
        sector_id = sector_data.get('sector_id')
        sector_name = sector_dict.get(sector_id, f"Sector {sector_id}")
        score = abs(sector_data.get('score', 0)) / 1e9
        print(f"  {i}. {sector_name}: -JPY {score:.1f}B")

    print(f"\nPerformance Change (1 Day):")
    sorted_perf = sorted([(s["sector_id"], s["perf_1d"]) for s in sectors],
                         key=lambda x: x[1], reverse=True)
    for sector_id, perf in sorted_perf[:3]:
        sector_name = sector_dict[sector_id]
        print(f"  - {sector_name}: {perf:+.2f}%")

if __name__ == "__main__":
    main()

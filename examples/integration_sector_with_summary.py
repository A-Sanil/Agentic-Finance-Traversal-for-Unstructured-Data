"""
Integration Example: Using Execution Summaries in Sector Recommendations

This example demonstrates how to integrate the execution summary writer
into the sector recommendation workflow to produce audit-friendly reports.
"""

import asyncio
from quant_agent.execution_summary import ExecutionSummary, ExecutionSummaryItem, write_execution_summary_sync
from quant_agent.sector_recommendations import SectorRecommendationEngine
from quant_agent.sectors import DEFAULT_SECTOR_UNIVERSE


def generate_sector_recommendation_with_summary(
    sector: str,
    subsector: str,
) -> tuple:
    """
    Generate a sector recommendation and automatically produce an execution summary.
    
    Args:
        sector: e.g., "technology", "financials"
        subsector: e.g., "semiconductors", "banks"
    
    Returns:
        A tuple of (recommendation_markdown, execution_summary_path)
    """
    # Get the list of tickers for this sector/subsector
    tickers = DEFAULT_SECTOR_UNIVERSE.tickers_for(sector, subsector)
    
    if not tickers:
        print(f"No tickers found for {sector} > {subsector}")
        return None, None
    
    # Pick the first ticker as the focus (or iterate through all)
    primary_ticker = tickers[0]
    
    # Generate the sector recommendation
    engine = SectorRecommendationEngine()
    recommendation_result = engine.build_sector_report(
        sector=sector,
        subsector=subsector,
        live_sources=False,
    )
    
    # Create an execution summary
    summary = ExecutionSummary(
        target_company=primary_ticker,  # Use ticker as placeholder
        target_ticker=primary_ticker,
        sector=sector,
        subsector=subsector,
    )
    
    # Add sources that were traversed
    summary.add_source(f"SEC EDGAR - {sector} filings")
    summary.add_source(f"Web news sources - {subsector} news")
    summary.add_source("Twitter/X sentiment analysis")
    
    # Add simulated insights (in a real system, these come from the RAG engine)
    summary.add_insight(
        ExecutionSummaryItem(
            key="sector_growth_rate",
            value="8.5% YoY",
            source_document="SEC EDGAR - sector analysis",
            confidence=0.85,
        )
    )
    summary.add_insight(
        ExecutionSummaryItem(
            key="subsector_competitive_intensity",
            value="High - 5+ major players",
            source_document="Web news sources",
            confidence=0.75,
        )
    )
    
    # Set the prediction (comes from recommendation engine)
    if recommendation_result:
        prediction_text = f"Sector outlook: {recommendation_result.sector_thesis[:100]}..."
        summary.set_prediction(prediction_text)
        summary.set_conclusion(f"Recommend sector focus on {subsector} with selective stock picks.")
    
    # Write the summary to disk
    output_path = write_execution_summary_sync(summary, output_dir="./outputs")
    
    # Return both the recommendation and the execution summary path
    return (
        recommendation_result.to_markdown() if recommendation_result else None,
        output_path,
    )


# Example usage
if __name__ == "__main__":
    # Generate a recommendation for technology > semiconductors
    recommendation, summary_path = generate_sector_recommendation_with_summary(
        sector="technology",
        subsector="semiconductors",
    )
    
    if recommendation:
        print("\n" + "=" * 80)
        print("RECOMMENDATION MARKDOWN")
        print("=" * 80)
        print(recommendation)
    
    if summary_path:
        print("\n" + "=" * 80)
        print(f"EXECUTION SUMMARY SAVED TO: {summary_path}")
        print("=" * 80)
        
        # Print the summary contents
        with open(summary_path, "r") as f:
            print(f.read())

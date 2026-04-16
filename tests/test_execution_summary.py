"""
Tests for execution summary module.
"""
import tempfile
from pathlib import Path

from quant_agent.execution_summary import ExecutionSummary, ExecutionSummaryItem, write_execution_summary_sync


def test_execution_summary_creation():
    """Test basic execution summary creation and formatting."""
    summary = ExecutionSummary("NVIDIA Corporation", "NVDA", sector="technology", subsector="semiconductors")
    
    summary.add_source("NVDA_10K_2024.pdf")
    summary.add_source("NVDA_8K_2025_01.txt")
    
    insight1 = ExecutionSummaryItem("gross_margin", "64%", "NVDA_10K_2024.pdf", confidence=0.95)
    insight2 = ExecutionSummaryItem("supply_chain", "Secured through Q3 2026", "NVDA_8K_2025_01.txt", confidence=0.90)
    
    summary.add_insight(insight1)
    summary.add_insight(insight2)
    
    summary.set_prediction("BUY - Strong AI demand, margin expansion")
    summary.set_conclusion("NVIDIA shows structural growth in AI infrastructure.")
    
    # Verify summary attributes
    assert summary.target_company == "NVIDIA Corporation"
    assert summary.target_ticker == "NVDA"
    assert summary.sector == "technology"
    assert len(summary.sources_traversed) == 2
    assert len(summary.insights) == 2
    assert summary.market_prediction is not None
    assert summary.synthesized_conclusion is not None


def test_execution_summary_text_output():
    """Test that summary text output is properly formatted."""
    summary = ExecutionSummary("JPMorgan Chase", "JPM", sector="financials")
    
    summary.add_source("JPM_10K_2024.pdf")
    summary.add_insight(ExecutionSummaryItem("net_interest_margin", "2.15%", "JPM_10K_2024.pdf"))
    summary.set_prediction("HOLD - Stable profitability, rate risk elevated")
    summary.set_conclusion("JPMorgan remains well-positioned but rate sensitivity warrants caution.")
    
    text_output = summary.to_text()
    
    # Verify key sections are present
    assert "EXECUTION SUMMARY REPORT" in text_output
    assert "TIMESTAMP & TARGET" in text_output
    assert "SOURCES TRAVERSED" in text_output
    assert "INSIGHTS UNCOVERED" in text_output
    assert "MARKET PREDICTION" in text_output
    assert "SYNTHESIZED CONCLUSION" in text_output
    assert "JPMorgan Chase" in text_output
    assert "JPM" in text_output
    assert "2.15%" in text_output


def test_execution_summary_sync_write():
    """Test synchronous writing of execution summary to disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        summary = ExecutionSummary("Tesla Inc.", "TSLA", sector="consumer discretionary")
        
        summary.add_source("TSLA_10Q_2024_Q4.pdf")
        summary.add_insight(ExecutionSummaryItem("production_volume", "1.81M units/year", "TSLA_10Q_2024_Q4.pdf", confidence=0.98))
        summary.set_prediction("BUY - EV demand recovery, margin pressure mitigated")
        summary.set_conclusion("Tesla exhibits recovery trajectory with margin stabilization.")
        
        # Write summary
        output_path = write_execution_summary_sync(summary, output_dir=tmpdir)
        
        # Verify file was created
        assert Path(output_path).exists()
        assert output_path.endswith(".txt")
        assert "TSLA_" in Path(output_path).name
        
        # Verify file contents
        with open(output_path, "r") as f:
            content = f.read()
        assert "EXECUTION SUMMARY REPORT" in content
        assert "Tesla Inc." in content
        assert "1.81M units/year" in content


def test_execution_summary_empty_fields():
    """Test summary with missing/empty fields."""
    summary = ExecutionSummary("Unknown Corp", "UNKN")
    
    # Without setting sources, insights, prediction, or conclusion
    text_output = summary.to_text()
    
    assert "EXECUTION SUMMARY REPORT" in text_output
    assert "(No sources traversed in this run)" in text_output
    assert "(No insights extracted)" in text_output
    assert "(Prediction pending)" in text_output
    assert "(Conclusion pending)" in text_output

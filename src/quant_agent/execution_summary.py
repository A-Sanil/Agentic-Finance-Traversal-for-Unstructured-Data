"""
Execution Summary Writer for Financial AI Agent

Generates and persists final execution reports with traced evidence and predictions.
"""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import aiofiles
except ImportError:
    aiofiles = None


class ExecutionSummaryItem:
    """A single data point or insight extracted from traversed documents."""
    
    def __init__(
        self,
        key: str,
        value: Any,
        source_document: str,
        confidence: float = 0.8,
    ):
        self.key = key
        self.value = value
        self.source_document = source_document
        self.confidence = confidence
    
    def to_text(self) -> str:
        """Format insight as a single-line text entry."""
        return f"- {self.key}: {self.value} (source: {self.source_document}, confidence: {self.confidence:.0%})"


class ExecutionSummary:
    """
    Execution summary for an agent run.
    
    Contains timestamp, target asset, traversed sources, extracted insights,
    and final market prediction/synthesized conclusion.
    """
    
    def __init__(
        self,
        target_company: str,
        target_ticker: str,
        sector: Optional[str] = None,
        subsector: Optional[str] = None,
    ):
        self.target_company = target_company
        self.target_ticker = target_ticker
        self.sector = sector
        self.subsector = subsector
        self.run_timestamp = datetime.utcnow()
        self.sources_traversed: List[str] = []
        self.insights: List[ExecutionSummaryItem] = []
        self.market_prediction: Optional[str] = None
        self.synthesized_conclusion: Optional[str] = None
    
    def add_source(self, source_name: str) -> None:
        """Register a document/source that was traversed."""
        if source_name not in self.sources_traversed:
            self.sources_traversed.append(source_name)
    
    def add_insight(self, insight: ExecutionSummaryItem) -> None:
        """Add an extracted data point or insight."""
        self.insights.append(insight)
    
    def set_prediction(self, prediction: str) -> None:
        """Set the final market prediction (e.g., BUY, HOLD, SELL, or detailed outlook)."""
        self.market_prediction = prediction
    
    def set_conclusion(self, conclusion: str) -> None:
        """Set the synthesized conclusion based on all extracted insights."""
        self.synthesized_conclusion = conclusion
    
    def to_text(self) -> str:
        """
        Format the full execution summary as text for .txt output.
        
        Returns:
            str: A formatted text block ready for file writing.
        """
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("EXECUTION SUMMARY REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Timestamp and Target
        lines.append("TIMESTAMP & TARGET")
        lines.append("-" * 40)
        lines.append(f"Run Timestamp: {self.run_timestamp.isoformat()}")
        lines.append(f"Company: {self.target_company} ({self.target_ticker})")
        if self.sector:
            lines.append(f"Sector: {self.sector}")
        if self.subsector:
            lines.append(f"Subsector: {self.subsector}")
        lines.append("")
        
        # Sources Traversed
        lines.append("SOURCES TRAVERSED")
        lines.append("-" * 40)
        if self.sources_traversed:
            for i, source in enumerate(self.sources_traversed, 1):
                lines.append(f"{i}. {source}")
        else:
            lines.append("(No sources traversed in this run)")
        lines.append("")
        
        # Insights Uncovered
        lines.append("INSIGHTS UNCOVERED")
        lines.append("-" * 40)
        if self.insights:
            for insight in self.insights:
                lines.append(insight.to_text())
        else:
            lines.append("(No insights extracted)")
        lines.append("")
        
        # Market Prediction
        lines.append("MARKET PREDICTION")
        lines.append("-" * 40)
        if self.market_prediction:
            lines.append(self.market_prediction)
        else:
            lines.append("(Prediction pending)")
        lines.append("")
        
        # Synthesized Conclusion
        lines.append("SYNTHESIZED CONCLUSION")
        lines.append("-" * 40)
        if self.synthesized_conclusion:
            lines.append(self.synthesized_conclusion)
        else:
            lines.append("(Conclusion pending)")
        lines.append("")
        
        lines.append("=" * 80)
        return "\n".join(lines)


async def write_execution_summary(
    summary: ExecutionSummary,
    output_dir: str = "./outputs",
) -> str:
    """
    Asynchronously write an execution summary to disk.
    
    Args:
        summary: ExecutionSummary object with populated data.
        output_dir: Directory where the .txt file will be saved. Defaults to "./outputs".
    
    Returns:
        str: The absolute path to the written file.
    
    Raises:
        RuntimeError: If aiofiles is not installed.
    
    Example:
        summary = ExecutionSummary("NVIDIA", "NVDA", sector="technology")
        summary.add_source("NVDA_10K_2024.pdf")
        summary.add_insight(ExecutionSummaryItem("supply_chain", "resilient", "NVDA_10K_2024.pdf"))
        summary.set_prediction("BUY - Strong fundamentals, supply chain secured through Q3 2026")
        summary.set_conclusion("NVIDIA exhibits structural growth tailwinds in AI infrastructure.")
        
        output_path = await write_execution_summary(summary, output_dir="./outputs")
        print(f"Summary saved to: {output_path}")
    """
    if aiofiles is None:
        raise RuntimeError("aiofiles is required for async summary writing. Install with: pip install aiofiles")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Filename: {ticker}_{timestamp}.txt
    timestamp_str = summary.run_timestamp.strftime("%Y%m%d_%H%M%S")
    filename = f"{summary.target_ticker}_{timestamp_str}.txt"
    file_path = output_path / filename
    
    # Write the summary text
    text_content = summary.to_text()
    
    async with aiofiles.open(str(file_path), mode="w") as f:
        await f.write(text_content)
    
    return str(file_path.resolve())


def write_execution_summary_sync(
    summary: ExecutionSummary,
    output_dir: str = "./outputs",
) -> str:
    """
    Synchronously write an execution summary to disk.
    
    Provides a non-async alternative to write_execution_summary for contexts where
    async I/O is not available or desired.
    
    Args:
        summary: ExecutionSummary object with populated data.
        output_dir: Directory where the .txt file will be saved. Defaults to "./outputs".
    
    Returns:
        str: The absolute path to the written file.
    
    Example:
        summary = ExecutionSummary("JPMorgan", "JPM", sector="financials")
        summary.add_source("JPM_10K_2024.pdf")
        output_path = write_execution_summary_sync(summary)
        print(f"Summary saved to: {output_path}")
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Filename: {ticker}_{timestamp}.txt
    timestamp_str = summary.run_timestamp.strftime("%Y%m%d_%H%M%S")
    filename = f"{summary.target_ticker}_{timestamp_str}.txt"
    file_path = output_path / filename
    
    # Write the summary text
    text_content = summary.to_text()
    
    with open(file_path, "w") as f:
        f.write(text_content)
    
    return str(file_path.resolve())

"""
LLM Evaluation Framework: Measuring Agent Predictive Accuracy

This module demonstrates how to use the golden_dataset.csv to measure
the agent's recommendation accuracy against real market outcomes.
"""

import csv
from pathlib import Path
from typing import List, Dict, Tuple


class EvaluationMetrics:
    """Computes precision, recall, F1, and accuracy from golden dataset results."""
    
    def __init__(self):
        self.true_positives = 0
        self.false_positives = 0
        self.true_negatives = 0
        self.false_negatives = 0
    
    def precision(self) -> float:
        """Precision: of the positive predictions, how many were correct?"""
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)
    
    def recall(self) -> float:
        """Recall: of the actual positives, how many did we identify?"""
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)
    
    def f1_score(self) -> float:
        """F1 Score: harmonic mean of precision and recall."""
        p = self.precision()
        r = self.recall()
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)
    
    def accuracy(self) -> float:
        """Accuracy: fraction of all predictions that were correct."""
        total = self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
        if total == 0:
            return 0.0
        return (self.true_positives + self.true_negatives) / total


def load_golden_dataset(csv_path: str) -> List[Dict]:
    """
    Load the golden dataset CSV file.
    
    Args:
        csv_path: Path to golden_dataset.csv
    
    Returns:
        List of dictionaries, one per ground-truth row.
    """
    rows = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def evaluate_agent_predictions(
    golden_data: List[Dict],
    agent_predictions: Dict[str, str],
) -> Tuple[EvaluationMetrics, List[Dict]]:
    """
    Compare agent predictions against ground-truth outcomes.
    
    Args:
        golden_data: List of rows from golden_dataset.csv
        agent_predictions: Dict mapping {ticker -> "BUY"|"HOLD"|"SELL"}
    
    Returns:
        Tuple of (metrics, detailed_results)
    """
    metrics = EvaluationMetrics()
    results = []
    
    for row in golden_data:
        ticker = row["company_ticker"]
        actual_outcome = row["outcome_match"].lower() in ["true", "1", "yes"]
        agent_signal = agent_predictions.get(ticker, "UNKNOWN")
        prediction_signal = row["prediction_signal"]
        
        # Simplified: map BUY/HOLD/SELL to boolean outcomes for metrics
        agent_predicted_positive = agent_signal == "BUY"
        actual_positive = actual_outcome
        
        if agent_predicted_positive and actual_positive:
            metrics.true_positives += 1
            match = True
        elif not agent_predicted_positive and not actual_positive:
            metrics.true_negatives += 1
            match = True
        elif agent_predicted_positive and not actual_positive:
            metrics.false_positives += 1
            match = False
        else:
            metrics.false_negatives += 1
            match = False
        
        results.append({
            "ticker": ticker,
            "source_document": row["source_document_name"],
            "agent_signal": agent_signal,
            "ground_truth_signal": prediction_signal,
            "ground_truth_outcome": row["outcome_match"],
            "prediction_match": match,
            "return_30d": float(row.get("actual_return_30d", 0)),
            "return_90d": float(row.get("actual_return_90d", 0)),
        })
    
    return metrics, results


def print_evaluation_report(metrics: EvaluationMetrics, results: List[Dict]) -> None:
    """
    Pretty-print the evaluation report.
    
    Args:
        metrics: EvaluationMetrics object with computed scores
        results: List of detailed prediction results
    """
    print("\n" + "=" * 80)
    print("AGENT EVALUATION REPORT (Golden Dataset)")
    print("=" * 80)
    
    # Metrics summary
    print("\nOVERALL METRICS")
    print("-" * 40)
    print(f"Precision:  {metrics.precision():.2%}")
    print(f"Recall:     {metrics.recall():.2%}")
    print(f"F1 Score:   {metrics.f1_score():.3f}")
    print(f"Accuracy:   {metrics.accuracy():.2%}")
    
    # Confusion matrix
    print("\nCONFUSION MATRIX")
    print("-" * 40)
    print(f"True Positives:  {metrics.true_positives}")
    print(f"True Negatives:  {metrics.true_negatives}")
    print(f"False Positives: {metrics.false_positives}")
    print(f"False Negatives: {metrics.false_negatives}")
    
    # Per-stock results
    print("\nPER-STOCK RESULTS")
    print("-" * 40)
    for result in results:
        match_str = "✓" if result["prediction_match"] else "✗"
        print(
            f"{match_str} {result['ticker']:8} | Agent: {result['agent_signal']:6} | "
            f"Actual: {result['ground_truth_outcome']:6} | 30d Return: {result['return_30d']:+6.1f}% | "
            f"90d Return: {result['return_90d']:+6.1f}%"
        )
    
    print("\n" + "=" * 80)


# Example usage
if __name__ == "__main__":
    # Load the golden dataset
    golden_data = load_golden_dataset("evals/golden_dataset.csv")
    
    # Simulate agent predictions (in a real system, these come from the agent)
    agent_predictions = {
        "NVDA": "BUY",      # Matches ground truth
        "JPM": "HOLD",      # Matches ground truth
        "TSLA": "SELL",     # Matches ground truth
    }
    
    # Evaluate
    metrics, results = evaluate_agent_predictions(golden_data, agent_predictions)
    
    # Print report
    print_evaluation_report(metrics, results)
    
    print("\nIMPLEMENTATION NOTE:")
    print("In production, agent predictions come from SectorRecommendationEngine.build_sector_report().")
    print("Extract the prediction_signal field and compare against outcome_match from golden_dataset.csv.")

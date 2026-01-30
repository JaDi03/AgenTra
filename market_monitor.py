import pandas as pd
import numpy as np
import logging
from scipy.stats import ks_2samp

logger = logging.getLogger("market_monitor")

def calculate_log_returns(prices: pd.Series) -> pd.Series:
    """Calculates logarithmic returns for a price series."""
    return np.log(prices / prices.shift(1)).dropna()

def detect_drift(current_prices: pd.Series, baseline_prices: pd.Series, confidence_level: float = 0.05) -> dict:
    """
    Detects if the distribution of current returns has drifted from baseline returns.
    Uses Kolmogorov-Smirnov 2-sample test.
    
    Args:
        current_prices: Recent price series (e.g., last 50 candles).
        baseline_prices: Historical price series (e.g., prior 200 candles).
        confidence_level: P-value threshold (default 0.05).
        
    Returns:
        dict: {
            "drift_detected": bool,
            "p_value": float,
            "ks_stat": float,
            "reason": str
        }
    """
    try:
        current_returns = calculate_log_returns(current_prices)
        baseline_returns = calculate_log_returns(baseline_prices)
        
        if len(current_returns) < 20 or len(baseline_returns) < 50:
            return {
                "drift_detected": False, 
                "p_value": 1.0, 
                "ks_stat": 0.0, 
                "reason": "Insufficient samples for statistical test"
            }
            
        # KS Test: Null Hypothesis - Both samples drawn from the same distribution
        # If p-value < alpha, we reject the null hypothesis -> Drift Detected.
        ks_stat, p_value = ks_2samp(current_returns, baseline_returns)
        
        drift_detected = p_value < confidence_level
        
        reason = "Market behavior remains statistically consistent."
        if drift_detected:
            reason = f"CONCEPT DRIFT DETECTED: Return distribution has shifted (p-value: {p_value:.4e}). Market dynamics have changed."
            
        return {
            "drift_detected": bool(drift_detected),
            "p_value": float(p_value),
            "ks_stat": float(ks_stat),
            "reason": reason
        }

    except Exception as e:
        logger.error(f"Drift Detection Error: {e}")
        return {
            "drift_detected": False, 
            "p_value": 1.0, 
            "ks_stat": 0.0, 
            "reason": f"Calculation Error: {e}"
        }

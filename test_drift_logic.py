import pandas as pd
import numpy as np
import market_monitor as mm

def test_drift_identification():
    print("--- STARTING CONCEPT DRIFT VALIDATION ---")
    
    # 1. Baseline: Standard Normal Returns
    np.random.seed(42)
    baseline_returns = np.random.normal(0, 0.01, 200)
    baseline_prices = pd.Series(100 * (1 + baseline_returns).cumprod())
    
    # 2. Case A: Similar Distribution (No Drift)
    stable_returns = np.random.normal(0, 0.01, 50)
    stable_prices = pd.Series(baseline_prices.iloc[-1] * (1 + stable_returns).cumprod())
    
    result_stable = mm.detect_drift(stable_prices, baseline_prices)
    print(f"STABLE CASE: Drift={result_stable['drift_detected']}, p-value={result_stable['p_value']:.4f}")
    
    # 3. Case B: High Volatility Drift
    vol_returns = np.random.normal(0, 0.05, 50) # 5x Volatility
    vol_prices = pd.Series(baseline_prices.iloc[-1] * (1 + vol_returns).cumprod())
    
    result_vol = mm.detect_drift(vol_prices, baseline_prices)
    print(f"VOLATILITY DRIFT: Drift={result_vol['drift_detected']}, p-value={result_vol['p_value']:.4e}")
    
    # 4. Case C: Mean Shift Drift (Pump/Dump)
    pump_returns = np.random.normal(0.04, 0.01, 50) # Significant positive bias
    pump_prices = pd.Series(baseline_prices.iloc[-1] * (1 + pump_returns).cumprod())
    
    result_pump = mm.detect_drift(pump_prices, baseline_prices)
    print(f"MEAN SHIFT DRIFT: Drift={result_pump['drift_detected']}, p-value={result_pump['p_value']:.4e}")

    if not result_stable['drift_detected'] and result_vol['drift_detected'] and result_pump['drift_detected']:
        print("\n✅ VALIDATION SUCCESSFUL: Statistical test correctly identifies behavior shifts.")
    else:
        print("\n❌ VALIDATION FAILED: Test logic did not meet sensitivity requirements.")

if __name__ == "__main__":
    test_drift_identification()

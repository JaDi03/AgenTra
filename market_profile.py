import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("market_profile")

def calculate_volume_profile(df: pd.DataFrame, lookback: int = 24) -> dict:
    """
    Calculates Volume Profile (POC, VAH, VAL) for the given dataframe.
    
    Args:
        df: DataFrame with 'close', 'high', 'low', 'volume'.
        lookback: Number of recent candles to inspect (default 24 = 6 hours on 15m).
        
    Returns:
        dict: {
            "POC": float (Point of Control - Price with most volume),
            "VAH": float (Value Area High - 70% vol upper bound),
            "VAL": float (Value Area Low - 70% vol lower bound),
            "profile_str": str (Formatted string for AI)
        }
    """
    try:
        subset = df.iloc[-lookback:].copy()
        
        if subset.empty:
            return {"POC": 0, "VAH": 0, "VAL": 0, "profile_str": "Insufficient Data"}

        # Define Price Bins (e.g., 50 bins across the range)
        min_price = subset['low'].min()
        max_price = subset['high'].max()
        price_range = max_price - min_price
        
        if price_range == 0:
             return {"POC": min_price, "VAH": max_price, "VAL": min_price, "profile_str": "Flat Range"}

        bin_size = price_range / 50
        
        # Create bins
        bins = np.arange(min_price, max_price + bin_size, bin_size)
        
        # Using 'close' as proxy for volume allocation (simplified 15m profile)
        # Ideally we'd split volume across high-low, but close is sufficient for estimation.
        subset['bin_idx'] = np.digitize(subset['close'], bins)
        
        # Aggregate volume per bin
        volume_by_bin = subset.groupby('bin_idx')['volume'].sum()
        
        # Find POC (Bin with max volume)
        max_vol_idx = volume_by_bin.idxmax()
        poc_price = bins[max_vol_idx-1] # -1 because digitize is 1-indexed
        
        # Calculate Value Area (70% of total volume)
        total_volume = volume_by_bin.sum()
        target_volume = total_volume * 0.70
        
        # Sorting bins by volume to accumulate (Traditional VA calc starts at POC and expands, 
        # but simplified distribution ranking works for general levels)
        sorted_bins = volume_by_bin.sort_values(ascending=False)
        
        accumulated_vol = 0
        va_indices = []
        
        for idx, vol in sorted_bins.items():
            accumulated_vol += vol
            va_indices.append(idx)
            if accumulated_vol >= target_volume:
                break
                
        # Determine VAH and VAL from the indices in the Value Area
        va_prices = [bins[i-1] for i in va_indices if 0 <= i-1 < len(bins)]
        
        if not va_prices:
            vah = max_price
            val = min_price
        else:
            vah = max(va_prices)
            val = min(va_prices)
            
        return {
            "POC": round(poc_price, 4),
            "VAH": round(vah, 4),
            "VAL": round(val, 4),
            "profile_str": f"POC: {poc_price:.4f} | VA: [{val:.4f} - {vah:.4f}]"
        }

    except Exception as e:
        logger.error(f"Volume Profile Error: {e}")
        return {"POC": 0, "VAH": 0, "VAL": 0, "profile_str": "Error"}

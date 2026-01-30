import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("order_flow")

def calculate_vpin_pro(df: pd.DataFrame, n_buckets: int = 10, bucket_size_factor: float = 1.0) -> float:
    """
    Calculates the VPIN (Volume-Synchronized Probability of Informed Trading).
    This is a 'Pro' version that uses Volume Buckets for better toxicity detection.
    
    Logic:
    1. Determine the average volume per bucket.
    2. Approximate Buy/Sell volume within each candle using price relative position.
    3. Aggregate volume into buckets of size V.
    4. Calculate cumulative imbalance in the buckets.
    
    Args:
        df: DataFrame with OHLCV data.
        n_buckets: Number of buckets to look back for the VPIN average.
        bucket_size_factor: Multiplier for average volume to define bucket size.
        
    Returns:
        float: VPIN score (0.0 to 1.0). High (> 0.7) means toxic flow/informed trading.
    """
    try:
        # 1. Estimate Buy/Sell Volume using the 'Bulk Volume Classification' method:
        # Buy Volume = Total Volume * CDF((Close - Mean) / StdDev)
        # Simplified OHLC Proxy: (Close - Low) / (High - Low)
        
        subset = df.copy()
        price_range = subset['high'] - subset['low']
        price_range = price_range.replace(0, 0.000001) # Avoid div by zero
        
        # Buy volume proxy: Relative position of close in the candle
        buy_ratio = (subset['close'] - subset['low']) / price_range
        # Limit to 0-1 for crazy wicks
        buy_ratio = buy_ratio.clip(0, 1)
        
        subset['buy_vol'] = subset['volume'] * buy_ratio
        subset['sell_vol'] = subset['volume'] * (1 - buy_ratio)
        
        # 2. Define Bucket Size (Avg volume of the lookback period)
        avg_vol = subset['volume'].mean()
        V = avg_vol * bucket_size_factor
        
        # 3. Aggregate into Volume Buckets
        # We process candles one by one to fill 'buckets' of size V
        c_buy_vol = 0
        c_sell_vol = 0
        c_vol = 0
        imbalances = []
        
        # Iterate backwards through enough data to fill n_buckets
        # We need roughly n_buckets * bucket_size_factor candles
        for i in range(len(subset) - 1, -1, -1):
            row = subset.iloc[i]
            
            # Add to current bucket
            c_buy_vol += row['buy_vol']
            c_sell_vol += row['sell_vol']
            c_vol += row['volume']
            
            # If bucket is full (or we ran out of data)
            if c_vol >= V:
                # Calculate imbalance for this bucket: |Buy - Sell| / Total
                imbalances.append(abs(c_buy_vol - c_sell_vol) / c_vol)
                # Reset for next bucket
                c_buy_vol = 0
                c_sell_vol = 0
                c_vol = 0
                
            if len(imbalances) >= n_buckets:
                break
                
        if not imbalances:
            return 0.5
            
        # VPIN is the average of imbalances over history
        vpin = np.mean(imbalances)
        
        return round(float(vpin), 3)

    except Exception as e:
        logger.error(f"VPIN Pro Error: {e}")
        return 0.5

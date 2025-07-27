import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ConservativeIndicators:
    """Technical indicators optimized for conservative trading"""
    
    @staticmethod
    def calculate_atr(high, low, close, period=14):
        """
        Calculate Average True Range for volatility measurement
        
        Args:
            high: High prices series
            low: Low prices series  
            close: Close prices series
            period: Period for ATR calculation
            
        Returns:
            pandas.Series: ATR values
        """
        try:
            if len(high) < period or len(low) < period or len(close) < period:
                logger.warning("Insufficient data for ATR calculation")
                return pd.Series([0] * len(close))
                
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            
            logger.debug(f"ATR calculated for period {period}")
            return atr.fillna(0)
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return pd.Series([0] * len(close))
    
    @staticmethod
    def rsi(close, period=14):
        """
        Calculate RSI for overbought/oversold levels
        
        Args:
            close: Close prices series
            period: Period for RSI calculation
            
        Returns:
            pandas.Series: RSI values (0-100)
        """
        try:
            if len(close) < period + 1:
                logger.warning("Insufficient data for RSI calculation")
                return pd.Series([50] * len(close))
                
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            # Avoid division by zero
            loss = loss.replace(0, 0.000001)
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            logger.debug(f"RSI calculated for period {period}")
            return rsi.fillna(50)
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return pd.Series([50] * len(close))
    
    @staticmethod
    def bollinger_bands(close, period=20, std_dev=2):
        """
        Calculate Bollinger Bands for trend analysis
        
        Args:
            close: Close prices series
            period: Period for moving average
            std_dev: Standard deviation multiplier
            
        Returns:
            tuple: (upper_band, middle_band, lower_band)
        """
        try:
            if len(close) < period:
                logger.warning("Insufficient data for Bollinger Bands calculation")
                sma = pd.Series([close.iloc[-1] if len(close) > 0 else 0] * len(close))
                return sma, sma, sma
                
            sma = close.rolling(window=period).mean()
            std = close.rolling(window=period).std()
            
            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)
            
            logger.debug(f"Bollinger Bands calculated for period {period}")
            return upper.fillna(sma), sma.fillna(close), lower.fillna(sma)
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            sma = pd.Series([close.iloc[-1] if len(close) > 0 else 0] * len(close))
            return sma, sma, sma
    
    @staticmethod
    def moving_average(close, period=20):
        """
        Calculate Simple Moving Average
        
        Args:
            close: Close prices series
            period: Period for moving average
            
        Returns:
            pandas.Series: Moving average values
        """
        try:
            if len(close) < period:
                logger.warning("Insufficient data for Moving Average calculation")
                return pd.Series([close.iloc[-1] if len(close) > 0 else 0] * len(close))
                
            ma = close.rolling(window=period).mean()
            logger.debug(f"Moving Average calculated for period {period}")
            return ma.fillna(close)
            
        except Exception as e:
            logger.error(f"Error calculating Moving Average: {e}")
            return pd.Series([close.iloc[-1] if len(close) > 0 else 0] * len(close))
    
    @staticmethod
    def ema(close, period=20):
        """
        Calculate Exponential Moving Average
        
        Args:
            close: Close prices series
            period: Period for EMA
            
        Returns:
            pandas.Series: EMA values
        """
        try:
            if len(close) < period:
                logger.warning("Insufficient data for EMA calculation")
                return pd.Series([close.iloc[-1] if len(close) > 0 else 0] * len(close))
                
            ema = close.ewm(span=period).mean()
            logger.debug(f"EMA calculated for period {period}")
            return ema.fillna(close)
            
        except Exception as e:
            logger.error(f"Error calculating EMA: {e}")
            return pd.Series([close.iloc[-1] if len(close) > 0 else 0] * len(close))
    
    @staticmethod
    def macd(close, fast_period=12, slow_period=26, signal_period=9):
        """
        Calculate MACD indicator
        
        Args:
            close: Close prices series
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
            
        Returns:
            tuple: (macd_line, signal_line, histogram)
        """
        try:
            if len(close) < slow_period:
                logger.warning("Insufficient data for MACD calculation")
                zero_series = pd.Series([0] * len(close))
                return zero_series, zero_series, zero_series
                
            fast_ema = ConservativeIndicators.ema(close, fast_period)
            slow_ema = ConservativeIndicators.ema(close, slow_period)
            
            macd_line = fast_ema - slow_ema
            signal_line = ConservativeIndicators.ema(macd_line, signal_period)
            histogram = macd_line - signal_line
            
            logger.debug("MACD calculated")
            return macd_line, signal_line, histogram
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            zero_series = pd.Series([0] * len(close))
            return zero_series, zero_series, zero_series
    
    @classmethod
    def calculate_all_indicators(cls, data):
        """
        Calculate all indicators for given price data
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            dict: Dictionary containing all calculated indicators
        """
        try:
            if data.empty or len(data) < 26:  # Need at least 26 periods for MACD
                logger.warning("Insufficient data for indicator calculations")
                return {}
                
            indicators = {}
            
            # Basic indicators
            indicators['atr'] = cls.calculate_atr(data['high'], data['low'], data['close'])
            indicators['rsi'] = cls.rsi(data['close'])
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = cls.bollinger_bands(data['close'])
            indicators['bb_upper'] = bb_upper
            indicators['bb_middle'] = bb_middle
            indicators['bb_lower'] = bb_lower
            
            # Moving Averages
            indicators['ma_20'] = cls.moving_average(data['close'], 20)
            indicators['ma_50'] = cls.moving_average(data['close'], 50)
            indicators['ema_12'] = cls.ema(data['close'], 12)
            indicators['ema_26'] = cls.ema(data['close'], 26)
            
            # MACD
            macd_line, signal_line, histogram = cls.macd(data['close'])
            indicators['macd'] = macd_line
            indicators['macd_signal'] = signal_line
            indicators['macd_histogram'] = histogram
            
            logger.info("All indicators calculated successfully")
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating all indicators: {e}")
            return {}

import pandas as pd
import numpy as np
import logging
from indicators import ConservativeIndicators

logger = logging.getLogger(__name__)

class ConservativeSignals:
    """Generate conservative trading signals with high confidence requirements"""
    
    def __init__(self, risk_manager):
        self.risk_manager = risk_manager
        self.min_confidence = 75.0  # Minimum 75% confidence
        self.min_risk_reward = 2.0  # Minimum 2:1 risk-reward ratio
        
    def analyze_market_conditions(self, data):
        """
        Analyze market conditions for trade suitability
        
        Args:
            data: OHLCV price data
            
        Returns:
            dict: Market condition analysis
        """
        try:
            if data.empty or len(data) < 50:
                return {
                    'trend_clear': False,
                    'volatility_manageable': False,
                    'volume_adequate': False,
                    'risk_reward_favorable': False,
                    'overall_favorable': False
                }
            
            indicators = ConservativeIndicators.calculate_all_indicators(data)
            
            conditions = {
                'trend_clear': self.check_trend_clarity(data, indicators),
                'volatility_manageable': self.check_volatility(data, indicators),
                'volume_adequate': self.check_volume(data),
                'risk_reward_favorable': self.check_risk_reward_potential(data, indicators)
            }
            
            # Overall favorable if at least 3 of 4 conditions met
            conditions['overall_favorable'] = sum(conditions.values()) >= 3
            
            logger.debug(f"Market conditions analyzed: {conditions}")
            return conditions
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            return {
                'trend_clear': False,
                'volatility_manageable': False,
                'volume_adequate': False,
                'risk_reward_favorable': False,
                'overall_favorable': False
            }
    
    def check_trend_clarity(self, data, indicators):
        """Check if trend is clear and strong"""
        try:
            if not indicators or 'ma_20' not in indicators:
                return False
                
            current_price = data['close'].iloc[-1]
            ma_20 = indicators['ma_20'].iloc[-1]
            ma_50 = indicators['ma_50'].iloc[-1]
            
            # Trend is clear if:
            # 1. Price is clearly above/below both MAs
            # 2. MA20 is clearly above/below MA50
            price_ma20_diff = abs(current_price - ma_20) / current_price
            ma20_ma50_diff = abs(ma_20 - ma_50) / ma_20
            
            return price_ma20_diff > 0.02 and ma20_ma50_diff > 0.01  # 2% and 1% thresholds
            
        except Exception as e:
            logger.error(f"Error checking trend clarity: {e}")
            return False
    
    def check_volatility(self, data, indicators):
        """Check if volatility is manageable"""
        try:
            if not indicators or 'atr' not in indicators:
                return False
                
            current_price = data['close'].iloc[-1]
            current_atr = indicators['atr'].iloc[-1]
            avg_atr = indicators['atr'].tail(20).mean()
            
            # Volatility is manageable if current ATR is not excessive
            atr_percent = (current_atr / current_price) * 100
            volatility_increase = current_atr / avg_atr if avg_atr > 0 else 1
            
            return atr_percent < 5 and volatility_increase < 2  # Less than 5% ATR and not doubled
            
        except Exception as e:
            logger.error(f"Error checking volatility: {e}")
            return False
    
    def check_volume(self, data):
        """Check if volume is adequate"""
        try:
            if 'volume' not in data.columns or len(data) < 20:
                return True  # Assume adequate if no volume data
                
            current_volume = data['volume'].iloc[-1]
            avg_volume = data['volume'].tail(20).mean()
            
            # Volume is adequate if current volume is at least 50% of average
            return current_volume >= avg_volume * 0.5
            
        except Exception as e:
            logger.error(f"Error checking volume: {e}")
            return True
    
    def check_risk_reward_potential(self, data, indicators):
        """Check if risk-reward potential is favorable"""
        try:
            if not indicators or 'bb_upper' not in indicators:
                return False
                
            current_price = data['close'].iloc[-1]
            bb_upper = indicators['bb_upper'].iloc[-1]
            bb_lower = indicators['bb_lower'].iloc[-1]
            
            # Check if price is not at extremes of Bollinger Bands
            bb_width = bb_upper - bb_lower
            distance_to_upper = abs(current_price - bb_upper)
            distance_to_lower = abs(current_price - bb_lower)
            
            # Favorable if not too close to either band (within 20% of band width)
            return distance_to_upper > bb_width * 0.2 and distance_to_lower > bb_width * 0.2
            
        except Exception as e:
            logger.error(f"Error checking risk-reward potential: {e}")
            return False
    
    def generate_conservative_signal(self, symbol, data):
        """
        Generate conservative trading signal for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            data: OHLCV price data
            
        Returns:
            dict: Trading signal or None if no signal
        """
        try:
            if data.empty or len(data) < 50:
                logger.warning(f"Insufficient data for {symbol}")
                return None
                
            # Analyze market conditions first
            conditions = self.analyze_market_conditions(data)
            if not conditions['overall_favorable']:
                logger.debug(f"Market conditions not favorable for {symbol}")
                return None
                
            indicators = ConservativeIndicators.calculate_all_indicators(data)
            if not indicators:
                logger.warning(f"Could not calculate indicators for {symbol}")
                return None
                
            # Generate signal based on multiple confirmations
            signal = self._analyze_entry_signals(symbol, data, indicators)
            
            if signal and signal['confidence'] >= self.min_confidence:
                logger.info(f"Conservative signal generated for {symbol}: {signal['direction']} "
                           f"confidence: {signal['confidence']}%")
                return signal
                
            return None
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    def _analyze_entry_signals(self, symbol, data, indicators):
        """Analyze entry signals using multiple indicators"""
        try:
            current_price = data['close'].iloc[-1]
            rsi = indicators['rsi'].iloc[-1]
            macd = indicators['macd'].iloc[-1]
            macd_signal = indicators['macd_signal'].iloc[-1]
            ma_20 = indicators['ma_20'].iloc[-1]
            ma_50 = indicators['ma_50'].iloc[-1]
            bb_upper = indicators['bb_upper'].iloc[-1]
            bb_lower = indicators['bb_lower'].iloc[-1]
            atr = indicators['atr'].iloc[-1]
            
            signals = []
            
            # Long signal conditions
            long_conditions = [
                current_price > ma_20 > ma_50,  # Uptrend
                rsi > 40 and rsi < 70,  # Not oversold or overbought
                macd > macd_signal,  # MACD bullish
                current_price > bb_lower + (bb_upper - bb_lower) * 0.3  # Not near lower band
            ]
            
            # Short signal conditions  
            short_conditions = [
                current_price < ma_20 < ma_50,  # Downtrend
                rsi < 60 and rsi > 30,  # Not overbought or oversold
                macd < macd_signal,  # MACD bearish
                current_price < bb_upper - (bb_upper - bb_lower) * 0.3  # Not near upper band
            ]
            
            long_score = sum(long_conditions)
            short_score = sum(short_conditions)
            
            direction = None
            confidence = 0
            
            if long_score >= 3:  # At least 3 of 4 conditions
                direction = 'long'
                confidence = 70 + (long_score * 5)  # 75-90% based on conditions met
            elif short_score >= 3:
                direction = 'short'
                confidence = 70 + (short_score * 5)
                
            if direction:
                # Calculate stop loss and take profit
                stop_loss = self.risk_manager.calculate_stop_loss(current_price, direction, atr)
                risk_distance = abs(current_price - stop_loss)
                take_profit = current_price + (risk_distance * self.min_risk_reward) if direction == 'long' else current_price - (risk_distance * self.min_risk_reward)
                
                return {
                    'symbol': symbol,
                    'direction': direction,
                    'confidence': min(confidence, 95),  # Cap at 95%
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'suggested_leverage': min(3, max(1, int(confidence / 30))),  # 1-3x based on confidence
                    'risk_reward_ratio': self.min_risk_reward,
                    'market_conditions': 'favorable'
                }
                
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing entry signals: {e}")
            return None
    
    def get_conservative_signals(self, symbols=None):
        """
        Get conservative signals for multiple symbols
        
        Args:
            symbols: List of symbols to analyze
            
        Returns:
            list: List of conservative signals
        """
        try:
            if symbols is None:
                # Expanded Bitunix futures categories
                symbols = [
                    # Major Layer 1s
                    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT',
                    
                    # AI/ML Tokens
                    'FET/USDT', 'AGIX/USDT', 'OCEAN/USDT', 'RNDR/USDT',
                    
                    # Meme Coins
                    'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'FLOKI/USDT',
                    
                    # DeFi Blue Chips
                    'UNI/USDT', 'AAVE/USDT', 'COMP/USDT', 'MKR/USDT',
                    
                    # Layer 2s
                    'MATIC/USDT', 'ARB/USDT', 'OP/USDT',
                    
                    # Gaming/Metaverse
                    'AXS/USDT', 'SAND/USDT', 'MANA/USDT'
                ]
                
            signals = []
            
            for symbol in symbols:
                # In a real implementation, this would fetch actual market data
                # For demo purposes, we'll use simulated data
                data = self._generate_sample_data(symbol)
                signal = self.generate_conservative_signal(symbol, data)
                
                if signal:
                    signals.append(signal)
                    
                # Limit to maximum 2 signals to avoid overtrading
                if len(signals) >= 2:
                    break
                    
            logger.info(f"Generated {len(signals)} conservative signals")
            return signals
            
        except Exception as e:
            logger.error(f"Error getting conservative signals: {e}")
            return []
    
    def _generate_sample_data(self, symbol):
        """Generate sample OHLCV data for demo purposes"""
        try:
            import random
            
            # Base prices for different symbols across categories
            base_prices = {
                # Major Layer 1s
                'BTC/USDT': 45000, 'ETH/USDT': 2500, 'BNB/USDT': 300, 'SOL/USDT': 100, 'ADA/USDT': 0.5,
                
                # AI/ML Tokens
                'FET/USDT': 1.2, 'AGIX/USDT': 0.8, 'OCEAN/USDT': 0.6, 'RNDR/USDT': 8.0,
                
                # Meme Coins
                'DOGE/USDT': 0.08, 'SHIB/USDT': 0.000025, 'PEPE/USDT': 0.000012, 'FLOKI/USDT': 0.00015,
                
                # DeFi Blue Chips
                'UNI/USDT': 7.5, 'AAVE/USDT': 85, 'COMP/USDT': 60, 'MKR/USDT': 1500,
                
                # Layer 2s
                'MATIC/USDT': 0.9, 'ARB/USDT': 1.1, 'OP/USDT': 2.3,
                
                # Gaming/Metaverse
                'AXS/USDT': 6.5, 'SAND/USDT': 0.45, 'MANA/USDT': 0.38
            }
            
            base_price = base_prices.get(symbol, 1000)
            periods = 100
            
            # Generate realistic price data
            prices = []
            current_price = base_price
            
            for _ in range(periods):
                change_percent = random.uniform(-0.02, 0.02)  # ±2% change
                current_price *= (1 + change_percent)
                prices.append(current_price)
            
            # Create OHLCV data
            data = []
            for i, close in enumerate(prices):
                high = close * random.uniform(1.001, 1.015)
                low = close * random.uniform(0.985, 0.999)
                open_price = prices[i-1] if i > 0 else close
                volume = random.uniform(1000000, 10000000)
                
                data.append({
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': volume
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error generating sample data: {e}")
            return pd.DataFrame()

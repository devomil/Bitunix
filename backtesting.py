"""
Conservative Crypto Futures Backtesting Module

This module provides comprehensive backtesting capabilities for validating
conservative trading strategies with emphasis on risk management and 
capital preservation.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

# Import our existing modules
from indicators import ConservativeIndicators
from signals import ConservativeSignals
from risk_manager import RiskManager

logger = logging.getLogger(__name__)

class BacktestEngine:
    """
    Conservative backtesting engine that validates trading strategies
    with emphasis on risk management and capital preservation.
    """
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.risk_manager = RiskManager()
        self.signal_generator = ConservativeSignals(self.risk_manager)
        self.indicators = ConservativeIndicators()
        
        # Backtest metrics
        self.trades = []
        self.daily_balances = []
        self.drawdowns = []
        self.positions = {}
        
        # Conservative parameters
        self.max_positions = 3  # Limit concurrent positions
        self.position_size_pct = 0.02  # 2% of balance per trade
        self.stop_loss_pct = 0.015  # 1.5% stop loss
        self.take_profit_pct = 0.03  # 3% take profit (2:1 risk/reward)
        
        logger.info(f"Backtest engine initialized with ${initial_balance:,.2f}")
    
    def generate_historical_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """
        Generate realistic historical price data for backtesting.
        In production, this would connect to actual historical data APIs.
        """
        
        # Base prices for different crypto categories
        base_prices = {
            'BTC/USDT': 45000, 'ETH/USDT': 2800, 'SOL/USDT': 110, 'ADA/USDT': 0.45,
            'FET/USDT': 1.20, 'AGIX/USDT': 0.35, 'OCEAN/USDT': 0.55, 'RNDR/USDT': 7.50,
            'DOGE/USDT': 0.08, 'SHIB/USDT': 0.000025, 'PEPE/USDT': 0.000012, 'FLOKI/USDT': 0.00015,
            'UNI/USDT': 8.5, 'AAVE/USDT': 85, 'COMP/USDT': 45, 'MKR/USDT': 1200,
            'MATIC/USDT': 0.85, 'ARB/USDT': 1.15, 'OP/USDT': 2.20,
            'AXS/USDT': 6.5, 'SAND/USDT': 0.35, 'MANA/USDT': 0.32
        }
        
        base_price = base_prices.get(symbol, 1.0)
        
        # Generate timestamps
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        timestamps = pd.date_range(start=start_date, end=end_date, freq='1H')
        
        # Generate realistic price movements
        np.random.seed(42)  # For reproducible results
        
        # Different volatility for different crypto categories
        if symbol.startswith(('BTC', 'ETH')):
            volatility = 0.02  # Lower volatility for major cryptos
        elif symbol.startswith(('DOGE', 'SHIB', 'PEPE', 'FLOKI')):
            volatility = 0.05  # Higher volatility for meme coins
        else:
            volatility = 0.03  # Medium volatility for others
        
        # Generate price series with realistic patterns
        returns = np.random.normal(0, volatility, len(timestamps))
        
        # Add some trend and mean reversion
        trend = np.linspace(-0.1, 0.1, len(timestamps))
        mean_reversion = -0.1 * np.cumsum(returns)
        
        final_returns = returns + trend * 0.001 + mean_reversion * 0.001
        prices = base_price * np.exp(np.cumsum(final_returns))
        
        # Create OHLCV data
        data = []
        for i, (timestamp, price) in enumerate(zip(timestamps, prices)):
            # Generate realistic OHLC from price
            spread = price * 0.001  # 0.1% spread
            high = price + np.random.uniform(0, spread * 2)
            low = price - np.random.uniform(0, spread * 2)
            open_price = prices[i-1] if i > 0 else price
            close = price
            volume = np.random.uniform(100000, 1000000)
            
            data.append({
                'timestamp': timestamp,
                'open': open_price,
                'high': max(open_price, high, close),
                'low': min(open_price, low, close),
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def run_backtest(self, symbols: List[str], days: int = 30) -> Dict:
        """
        Run comprehensive backtest on multiple symbols with conservative strategy.
        """
        logger.info(f"Starting backtest on {len(symbols)} symbols for {days} days")
        
        # Reset state
        self.current_balance = self.initial_balance
        self.trades = []
        self.daily_balances = []
        self.positions = {}
        
        # Generate historical data for all symbols
        historical_data = {}
        for symbol in symbols:
            historical_data[symbol] = self.generate_historical_data(symbol, days)
        
        # Get all timestamps and sort
        all_timestamps = set()
        for df in historical_data.values():
            all_timestamps.update(df.index)
        timestamps = sorted(all_timestamps)
        
        # Run simulation
        for timestamp in timestamps:
            self._process_timestamp(timestamp, historical_data)
        
        # Calculate final metrics
        results = self._calculate_results()
        
        logger.info(f"Backtest completed. Final balance: ${self.current_balance:,.2f}")
        logger.info(f"Total return: {results['total_return_pct']:.2f}%")
        logger.info(f"Win rate: {results['win_rate']:.1f}%")
        logger.info(f"Max drawdown: {results['max_drawdown_pct']:.2f}%")
        
        return results
    
    def _process_timestamp(self, timestamp: datetime, historical_data: Dict[str, pd.DataFrame]):
        """Process a single timestamp in the backtest simulation."""
        
        current_prices = {}
        
        # Get current prices for all symbols
        for symbol, df in historical_data.items():
            if timestamp in df.index:
                current_prices[symbol] = df.loc[timestamp]
        
        # Update existing positions
        self._update_positions(current_prices)
        
        # Check for new signals (only every 4 hours to avoid overtrading)
        if timestamp.hour % 4 == 0:
            self._check_new_signals(timestamp, current_prices, historical_data)
        
        # Record daily balance
        if timestamp.hour == 0:
            total_value = self._calculate_total_value(current_prices)
            self.daily_balances.append({
                'timestamp': timestamp,
                'balance': total_value
            })
    
    def _update_positions(self, current_prices: Dict):
        """Update existing positions and check stop loss/take profit."""
        
        positions_to_close = []
        
        for position_id, position in self.positions.items():
            symbol = position['symbol']
            if symbol not in current_prices:
                continue
                
            current_price = current_prices[symbol]['close']
            entry_price = position['entry_price']
            direction = position['direction']
            
            # Calculate current P&L
            if direction == 'long':
                pnl_pct = (current_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - current_price) / entry_price
            
            # Check stop loss
            if pnl_pct <= -self.stop_loss_pct:
                self._close_position(position_id, current_price, 'stop_loss')
                positions_to_close.append(position_id)
            
            # Check take profit
            elif pnl_pct >= self.take_profit_pct:
                self._close_position(position_id, current_price, 'take_profit')
                positions_to_close.append(position_id)
        
        # Remove closed positions
        for position_id in positions_to_close:
            del self.positions[position_id]
    
    def _check_new_signals(self, timestamp: datetime, current_prices: Dict, historical_data: Dict):
        """Check for new trading signals."""
        
        # Don't open new positions if we're at max capacity
        if len(self.positions) >= self.max_positions:
            return
        
        for symbol, price_data in current_prices.items():
            # Skip if we already have a position in this symbol
            if any(pos['symbol'] == symbol for pos in self.positions.values()):
                continue
            
            # Get historical data for indicators
            df = historical_data[symbol]
            end_idx = df.index.get_loc(timestamp)
            
            # Need at least 20 periods for indicators
            if end_idx < 20:
                continue
            
            historical_slice = df.iloc[:end_idx+1]
            
            # Calculate indicators
            try:
                atr = self.indicators.calculate_atr(
                    historical_slice['high'], 
                    historical_slice['low'], 
                    historical_slice['close']
                )
                rsi = self.indicators.rsi(historical_slice['close'])
                bb_upper, bb_middle, bb_lower = self.indicators.bollinger_bands(historical_slice['close'])
                
                if len(atr) == 0 or len(rsi) == 0:
                    continue
                
                current_atr = atr.iloc[-1]
                current_rsi = rsi.iloc[-1]
                current_price = price_data['close']
                
                # Conservative signal generation
                signal = self._generate_conservative_signal(
                    symbol, current_price, current_rsi, current_atr, 
                    bb_upper.iloc[-1], bb_lower.iloc[-1]
                )
                
                if signal and signal['confidence'] >= 0.75:  # High confidence only
                    self._open_position(timestamp, signal)
                    
            except Exception as e:
                logger.warning(f"Error generating signal for {symbol}: {e}")
    
    def _generate_conservative_signal(self, symbol: str, price: float, rsi: float, 
                                    atr: float, bb_upper: float, bb_lower: float) -> Optional[Dict]:
        """Generate conservative trading signals."""
        
        # Conservative long signal: oversold + near lower BB
        if rsi < 35 and price <= bb_lower * 1.02:  # Within 2% of lower BB
            return {
                'symbol': symbol,
                'direction': 'long',
                'confidence': min(0.8, (35 - rsi) / 35 + 0.5),  # Higher confidence for more oversold
                'entry_price': price,
                'reason': 'oversold_near_support'
            }
        
        # Conservative short signal: overbought + near upper BB
        elif rsi > 65 and price >= bb_upper * 0.98:  # Within 2% of upper BB
            return {
                'symbol': symbol,
                'direction': 'short',
                'confidence': min(0.8, (rsi - 65) / 35 + 0.5),  # Higher confidence for more overbought
                'entry_price': price,
                'reason': 'overbought_near_resistance'
            }
        
        return None
    
    def _open_position(self, timestamp: datetime, signal: Dict):
        """Open a new position based on signal."""
        
        # Calculate position size (conservative 2% of balance)
        position_value = self.current_balance * self.position_size_pct
        
        # Validate with risk manager
        if not self.risk_manager.validate_trade(
            signal['symbol'], signal['direction'], position_value, 2.0  # 2x leverage
        ):
            return
        
        position_id = f"{signal['symbol']}_{timestamp.strftime('%Y%m%d_%H%M')}"
        
        position = {
            'id': position_id,
            'symbol': signal['symbol'],
            'direction': signal['direction'],
            'entry_price': signal['entry_price'],
            'entry_time': timestamp,
            'size': position_value / signal['entry_price'],
            'value': position_value,
            'confidence': signal['confidence'],
            'reason': signal['reason']
        }
        
        self.positions[position_id] = position
        
        logger.info(f"Opened {signal['direction']} position: {signal['symbol']} @ ${signal['entry_price']:.4f}")
    
    def _close_position(self, position_id: str, exit_price: float, reason: str):
        """Close an existing position."""
        
        position = self.positions[position_id]
        entry_price = position['entry_price']
        direction = position['direction']
        size = position['size']
        
        # Calculate P&L
        if direction == 'long':
            pnl = (exit_price - entry_price) * size
        else:
            pnl = (entry_price - exit_price) * size
        
        # Update balance
        self.current_balance += pnl
        
        # Record trade
        trade = {
            'symbol': position['symbol'],
            'direction': direction,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'size': size,
            'pnl': pnl,
            'pnl_pct': pnl / position['value'] * 100,
            'entry_time': position['entry_time'],
            'exit_time': datetime.now(),
            'reason': reason,
            'confidence': position['confidence']
        }
        
        self.trades.append(trade)
        
        logger.info(f"Closed {direction} position: {position['symbol']} @ ${exit_price:.4f}, P&L: ${pnl:.2f}")
    
    def _calculate_total_value(self, current_prices: Dict) -> float:
        """Calculate total portfolio value including open positions."""
        
        total_value = self.current_balance
        
        for position in self.positions.values():
            symbol = position['symbol']
            if symbol in current_prices:
                current_price = current_prices[symbol]['close']
                entry_price = position['entry_price']
                direction = position['direction']
                size = position['size']
                
                if direction == 'long':
                    unrealized_pnl = (current_price - entry_price) * size
                else:
                    unrealized_pnl = (entry_price - current_price) * size
                
                total_value += unrealized_pnl
        
        return total_value
    
    def _calculate_results(self) -> Dict:
        """Calculate comprehensive backtest results."""
        
        if not self.trades:
            return {
                'total_return_pct': 0,
                'win_rate': 0,
                'max_drawdown_pct': 0,
                'sharpe_ratio': 0,
                'total_trades': 0,
                'profitable_trades': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'largest_win': 0,
                'largest_loss': 0
            }
        
        # Basic metrics
        total_return = self.current_balance - self.initial_balance
        total_return_pct = (total_return / self.initial_balance) * 100
        
        # Trade statistics
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] <= 0]
        
        win_rate = len(winning_trades) / len(self.trades) * 100 if self.trades else 0
        
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        largest_win = max([t['pnl'] for t in winning_trades]) if winning_trades else 0
        largest_loss = min([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        # Drawdown calculation
        balances = [b['balance'] for b in self.daily_balances]
        if balances:
            peak = balances[0]
            max_drawdown = 0
            
            for balance in balances:
                if balance > peak:
                    peak = balance
                drawdown = (peak - balance) / peak * 100
                max_drawdown = max(max_drawdown, drawdown)
        else:
            max_drawdown = 0
        
        # Sharpe ratio (simplified)
        if len(self.daily_balances) > 1:
            daily_returns = []
            for i in range(1, len(self.daily_balances)):
                prev_balance = self.daily_balances[i-1]['balance']
                curr_balance = self.daily_balances[i]['balance']
                daily_return = (curr_balance - prev_balance) / prev_balance
                daily_returns.append(daily_return)
            
            if daily_returns and np.std(daily_returns) > 0:
                sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(365)
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_return_pct': round(total_return_pct, 2),
            'win_rate': round(win_rate, 1),
            'max_drawdown_pct': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'total_trades': len(self.trades),
            'profitable_trades': len(winning_trades),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'largest_win': round(largest_win, 2),
            'largest_loss': round(largest_loss, 2),
            'final_balance': round(self.current_balance, 2)
        }
    
    def get_trade_summary(self) -> List[Dict]:
        """Get detailed trade summary for analysis."""
        return self.trades
    
    def get_daily_balances(self) -> List[Dict]:
        """Get daily balance history for charting."""
        return self.daily_balances

# Quick test function
def run_sample_backtest():
    """Run a sample backtest for demonstration."""
    
    engine = BacktestEngine(initial_balance=1000.0)  # Start with $1000
    
    # Test on a few symbols from different categories
    symbols = ['BTC/USDT', 'ETH/USDT', 'DOGE/USDT', 'UNI/USDT', 'MANA/USDT']
    
    results = engine.run_backtest(symbols, days=14)  # 2 week backtest
    
    print("\n=== Conservative Strategy Backtest Results ===")
    print(f"Total Return: {results['total_return_pct']:.2f}%")
    print(f"Win Rate: {results['win_rate']:.1f}%")
    print(f"Max Drawdown: {results['max_drawdown_pct']:.2f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Final Balance: ${results['final_balance']:,.2f}")
    
    return results

if __name__ == "__main__":
    # Run sample backtest when module is executed directly
    run_sample_backtest()
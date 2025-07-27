import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PortfolioMonitor:
    """Monitor portfolio positions and risk metrics"""
    
    def __init__(self, api_client, risk_manager):
        self.api_client = api_client
        self.risk_manager = risk_manager
        self.positions = {}
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        
    def monitor_positions(self):
        """Continuously monitor open positions for risk management"""
        try:
            positions = self.get_open_positions()
            
            for position in positions:
                self.check_stop_loss(position)
                self.check_take_profit(position)
                self.monitor_drawdown(position)
                self.update_position_pnl(position)
                
            logger.debug(f"Monitored {len(positions)} positions")
            
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
    
    def get_open_positions(self):
        """Get list of open positions"""
        try:
            # In real implementation, this would fetch from exchange API
            # For demo, return stored positions
            return list(self.positions.values())
            
        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return []
    
    def check_stop_loss(self, position):
        """Check if position should be closed due to stop loss"""
        try:
            current_price = self.api_client.get_current_price(position['symbol'])
            if current_price is None:
                return
                
            should_close = False
            
            if position['direction'] == 'long':
                should_close = current_price <= position['stop_loss']
            else:
                should_close = current_price >= position['stop_loss']
                
            if should_close:
                logger.warning(f"Stop loss triggered for {position['symbol']} at {current_price}")
                self.close_position(position, 'stop_loss')
                
        except Exception as e:
            logger.error(f"Error checking stop loss for {position.get('symbol', 'unknown')}: {e}")
    
    def check_take_profit(self, position):
        """Check if position should be closed due to take profit"""
        try:
            current_price = self.api_client.get_current_price(position['symbol'])
            if current_price is None:
                return
                
            should_close = False
            
            if position['direction'] == 'long':
                should_close = current_price >= position['take_profit']
            else:
                should_close = current_price <= position['take_profit']
                
            if should_close:
                logger.info(f"Take profit reached for {position['symbol']} at {current_price}")
                self.close_position(position, 'take_profit')
                
        except Exception as e:
            logger.error(f"Error checking take profit for {position.get('symbol', 'unknown')}: {e}")
    
    def monitor_drawdown(self, position):
        """Monitor position drawdown and suggest adjustments"""
        try:
            current_price = self.api_client.get_current_price(position['symbol'])
            if current_price is None:
                return
                
            entry_price = position['entry_price']
            
            if position['direction'] == 'long':
                drawdown = (entry_price - current_price) / entry_price
            else:
                drawdown = (current_price - entry_price) / entry_price
                
            # Alert if drawdown exceeds 50% of stop loss distance
            stop_loss_distance = abs(entry_price - position['stop_loss']) / entry_price
            
            if drawdown > stop_loss_distance * 0.5:
                logger.warning(f"High drawdown detected for {position['symbol']}: {drawdown:.2%}")
                
        except Exception as e:
            logger.error(f"Error monitoring drawdown for {position.get('symbol', 'unknown')}: {e}")
    
    def update_position_pnl(self, position):
        """Update position P&L"""
        try:
            current_price = self.api_client.get_current_price(position['symbol'])
            if current_price is None:
                return
                
            entry_price = position['entry_price']
            position_size = position['size']
            
            if position['direction'] == 'long':
                pnl = (current_price - entry_price) * position_size
            else:
                pnl = (entry_price - current_price) * position_size
                
            position['unrealized_pnl'] = pnl
            position['current_price'] = current_price
            
        except Exception as e:
            logger.error(f"Error updating P&L for {position.get('symbol', 'unknown')}: {e}")
    
    def close_position(self, position, reason):
        """Close a position"""
        try:
            # In real implementation, this would place a market order to close
            position_id = position['id']
            
            logger.info(f"Closing position {position_id} for {position['symbol']} - Reason: {reason}")
            
            # Update daily P&L
            if 'unrealized_pnl' in position:
                self.daily_pnl += position['unrealized_pnl']
                
            # Remove from positions
            if position_id in self.positions:
                del self.positions[position_id]
                
        except Exception as e:
            logger.error(f"Error closing position: {e}")
    
    def calculate_portfolio_risk(self):
        """Calculate total portfolio risk percentage"""
        try:
            total_risk = 0
            balance = self.api_client.get_account_balance()
            
            if balance <= 0:
                return 0
                
            for position in self.positions.values():
                # Calculate risk amount for each position
                entry_price = position['entry_price']
                stop_loss = position['stop_loss']
                size = position['size']
                
                risk_per_unit = abs(entry_price - stop_loss)
                position_risk = risk_per_unit * size
                total_risk += position_risk
                
            risk_percentage = (total_risk / balance) * 100
            logger.debug(f"Total portfolio risk: {risk_percentage:.2f}%")
            
            return min(risk_percentage, 100)  # Cap at 100%
            
        except Exception as e:
            logger.error(f"Error calculating portfolio risk: {e}")
            return 0
    
    def get_balance(self):
        """Get account balance"""
        try:
            return self.api_client.get_account_balance()
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0
    
    def get_daily_pnl(self):
        """Get daily P&L"""
        try:
            # Reset daily counters if new day
            current_date = datetime.now().date()
            if current_date != self.last_reset_date:
                self.daily_pnl = 0
                self.daily_trades = 0
                self.last_reset_date = current_date
                
            # Add unrealized P&L from open positions
            total_pnl = self.daily_pnl
            for position in self.positions.values():
                if 'unrealized_pnl' in position:
                    total_pnl += position['unrealized_pnl']
                    
            return total_pnl
            
        except Exception as e:
            logger.error(f"Error getting daily P&L: {e}")
            return 0
    
    def suggest_position_adjustments(self):
        """Suggest position adjustments based on risk analysis"""
        try:
            risk_percent = self.calculate_portfolio_risk()
            max_risk = 5.0  # 5% maximum total portfolio risk
            
            suggestions = []
            
            if risk_percent > max_risk:
                suggestions.append(f"Portfolio risk ({risk_percent:.1f}%) exceeds maximum ({max_risk}%). Consider reducing position sizes.")
                
            if len(self.positions) > self.risk_manager.get_max_simultaneous_positions():
                suggestions.append(f"Too many open positions ({len(self.positions)}). Consider closing some positions.")
                
            if self.daily_trades >= self.risk_manager.get_max_daily_trades():
                suggestions.append("Daily trading limit reached. No new trades recommended today.")
                
            daily_pnl_percent = (self.get_daily_pnl() / self.get_balance()) * 100
            if self.risk_manager.check_daily_loss_limit(daily_pnl_percent):
                suggestions.append("Daily loss limit exceeded. Consider stopping trading for today.")
                
            if not suggestions:
                suggestions.append("Portfolio risk is within acceptable limits.")
                
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting position adjustments: {e}")
            return ["Error analyzing portfolio. Manual review recommended."]
    
    def add_position(self, position_data):
        """Add new position to monitoring"""
        try:
            position_id = f"{position_data['symbol']}_{datetime.now().timestamp()}"
            position = {
                'id': position_id,
                'symbol': position_data['symbol'],
                'direction': position_data['direction'],
                'entry_price': position_data['entry_price'],
                'size': position_data['size'],
                'stop_loss': position_data['stop_loss'],
                'take_profit': position_data['take_profit'],
                'leverage': position_data.get('leverage', 1),
                'timestamp': datetime.now(),
                'unrealized_pnl': 0
            }
            
            self.positions[position_id] = position
            self.daily_trades += 1
            
            logger.info(f"Added position {position_id} for monitoring")
            return position_id
            
        except Exception as e:
            logger.error(f"Error adding position: {e}")
            return None
    
    def get_portfolio_summary(self):
        """Get comprehensive portfolio summary"""
        try:
            balance = self.get_balance()
            daily_pnl = self.get_daily_pnl()
            risk_percent = self.calculate_portfolio_risk()
            
            return {
                'total_balance': balance,
                'daily_pnl': daily_pnl,
                'daily_pnl_percent': (daily_pnl / balance * 100) if balance > 0 else 0,
                'total_risk_percent': risk_percent,
                'active_positions': len(self.positions),
                'daily_trades': self.daily_trades,
                'positions': list(self.positions.values()),
                'suggestions': self.suggest_position_adjustments()
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {
                'total_balance': 0,
                'daily_pnl': 0,
                'daily_pnl_percent': 0,
                'total_risk_percent': 0,
                'active_positions': 0,
                'daily_trades': 0,
                'positions': [],
                'suggestions': ["Error retrieving portfolio data"]
            }

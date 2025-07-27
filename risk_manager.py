import logging

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, max_risk_percent=1.5, max_leverage=5, max_daily_loss=3.0):
        """
        Initialize risk manager with conservative defaults
        
        Args:
            max_risk_percent: Maximum risk per trade as percentage of balance
            max_leverage: Maximum allowed leverage
            max_daily_loss: Maximum daily loss percentage before emergency stop
        """
        self.max_risk_percent = max_risk_percent
        self.max_leverage = max_leverage
        self.max_daily_loss = max_daily_loss
        
        logger.info(f"RiskManager initialized with max_risk: {max_risk_percent}%, "
                   f"max_leverage: {max_leverage}x, max_daily_loss: {max_daily_loss}%")
        
    def validate_trade(self, trade_params):
        """
        Validate trade meets conservative criteria
        
        Args:
            trade_params: Dictionary containing trade parameters
            
        Returns:
            tuple: (is_valid: bool, validation_results: dict)
        """
        try:
            checks = {
                'leverage_safe': trade_params.get('leverage', 1) <= self.max_leverage,
                'risk_acceptable': trade_params.get('risk_percent', 0) <= self.max_risk_percent,
                'stop_loss_set': 'stop_loss' in trade_params and trade_params['stop_loss'] is not None,
                'position_size_safe': self.check_position_size(trade_params),
                'risk_reward_adequate': trade_params.get('risk_reward_ratio', 0) >= 2.0
            }
            
            is_valid = all(checks.values())
            
            if not is_valid:
                failed_checks = [check for check, passed in checks.items() if not passed]
                logger.warning(f"Trade validation failed. Failed checks: {failed_checks}")
            
            return is_valid, checks
            
        except Exception as e:
            logger.error(f"Error validating trade: {e}")
            return False, {'error': str(e)}
    
    def check_position_size(self, trade_params):
        """
        Check if position size is within safe limits
        
        Args:
            trade_params: Dictionary containing trade parameters
            
        Returns:
            bool: True if position size is safe
        """
        try:
            position_size = trade_params.get('position_size', 0)
            account_balance = trade_params.get('account_balance', 0)
            
            if account_balance <= 0:
                return False
                
            position_percent = (position_size / account_balance) * 100
            return position_percent <= 20  # Maximum 20% of balance in single position
            
        except Exception as e:
            logger.error(f"Error checking position size: {e}")
            return False
    
    def calculate_position_size(self, account_balance, risk_percent, entry_price, stop_loss_price):
        """
        Calculate safe position size based on risk parameters
        
        Args:
            account_balance: Total account balance
            risk_percent: Risk percentage for this trade
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price
            
        Returns:
            float: Safe position size
        """
        try:
            if stop_loss_price <= 0 or entry_price <= 0:
                return 0
                
            risk_amount = account_balance * (min(risk_percent, self.max_risk_percent) / 100)
            price_difference = abs(entry_price - stop_loss_price)
            
            if price_difference == 0:
                return 0
                
            position_size = risk_amount / price_difference
            
            # Cap position size to maximum percentage of balance
            max_position_value = account_balance * 0.2  # 20% max
            if position_size * entry_price > max_position_value:
                position_size = max_position_value / entry_price
                
            logger.debug(f"Calculated position size: {position_size} for risk: {risk_percent}%")
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0
    
    def calculate_stop_loss(self, entry_price, direction, atr_value):
        """
        Calculate conservative stop loss using ATR
        
        Args:
            entry_price: Entry price for the trade
            direction: 'long' or 'short'
            atr_value: Average True Range value
            
        Returns:
            float: Stop loss price
        """
        try:
            if atr_value <= 0 or entry_price <= 0:
                # Fallback to 2% stop loss if ATR unavailable
                multiplier = 0.98 if direction == 'long' else 1.02
                return entry_price * multiplier
                
            # Use 2x ATR for conservative stop loss
            atr_multiplier = 2.0
            
            if direction == 'long':
                stop_loss = entry_price - (atr_multiplier * atr_value)
            else:
                stop_loss = entry_price + (atr_multiplier * atr_value)
                
            # Ensure stop loss is reasonable (not more than 5% from entry)
            max_stop_distance = entry_price * 0.05
            if direction == 'long':
                stop_loss = max(stop_loss, entry_price - max_stop_distance)
            else:
                stop_loss = min(stop_loss, entry_price + max_stop_distance)
                
            logger.debug(f"Calculated stop loss: {stop_loss} for {direction} position at {entry_price}")
            return stop_loss
            
        except Exception as e:
            logger.error(f"Error calculating stop loss: {e}")
            return entry_price * (0.98 if direction == 'long' else 1.02)
    
    def check_daily_loss_limit(self, daily_pnl_percent):
        """
        Check if daily loss limit has been exceeded
        
        Args:
            daily_pnl_percent: Daily P&L as percentage
            
        Returns:
            bool: True if emergency stop should be triggered
        """
        try:
            if daily_pnl_percent < -self.max_daily_loss:
                logger.warning(f"Daily loss limit exceeded: {daily_pnl_percent}% vs limit {self.max_daily_loss}%")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error checking daily loss limit: {e}")
            return False
    
    def get_max_simultaneous_positions(self):
        """Get maximum number of simultaneous positions allowed"""
        return 3
    
    def get_max_daily_trades(self):
        """Get maximum number of trades allowed per day"""
        return 3

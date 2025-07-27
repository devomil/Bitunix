import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EmergencyStop:
    """Emergency stop system for risk management"""
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.is_active = False
        self.activation_reason = None
        self.activation_time = None
        self.daily_loss_limit = 3.0  # 3% daily loss limit
        self.max_drawdown_limit = 10.0  # 10% maximum drawdown
        self.consecutive_losses_limit = 5  # Max consecutive losses
        
        # Tracking variables
        self.consecutive_losses = 0
        self.daily_start_balance = 0
        self.max_balance_today = 0
        self.last_reset_date = datetime.now().date()
        
        logger.info("Emergency stop system initialized")
    
    def check_all_triggers(self, portfolio_data):
        """Check all emergency stop triggers"""
        try:
            if self.is_active:
                return True
                
            # Reset daily counters if new day
            self._reset_daily_counters()
            
            # Check various trigger conditions
            triggers = [
                self.check_daily_loss_limit(portfolio_data),
                self.check_drawdown_limit(portfolio_data),
                self.check_consecutive_losses(),
                self.check_system_health(),
                self.check_balance_threshold(portfolio_data)
            ]
            
            # If any trigger is activated
            if any(triggers):
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking emergency triggers: {e}")
            # In case of error, activate emergency stop as safety measure
            self.activate_emergency_stop("System error during trigger check")
            return True
    
    def check_daily_loss_limit(self, portfolio_data):
        """Check if daily loss exceeds limit"""
        try:
            current_balance = portfolio_data.get('total_balance', 0)
            daily_pnl_percent = portfolio_data.get('daily_pnl_percent', 0)
            
            # Set daily start balance on first check of the day
            if self.daily_start_balance == 0:
                self.daily_start_balance = current_balance
                self.max_balance_today = current_balance
            
            # Update max balance for the day
            self.max_balance_today = max(self.max_balance_today, current_balance)
            
            # Check if daily loss exceeds limit
            if daily_pnl_percent < -self.daily_loss_limit:
                self.activate_emergency_stop(
                    f"Daily loss limit exceeded: {daily_pnl_percent:.2f}% (limit: {self.daily_loss_limit}%)"
                )
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking daily loss limit: {e}")
            return False
    
    def check_drawdown_limit(self, portfolio_data):
        """Check if maximum drawdown exceeds limit"""
        try:
            current_balance = portfolio_data.get('total_balance', 0)
            
            if self.max_balance_today == 0:
                return False
                
            drawdown_percent = ((self.max_balance_today - current_balance) / self.max_balance_today) * 100
            
            if drawdown_percent > self.max_drawdown_limit:
                self.activate_emergency_stop(
                    f"Maximum drawdown exceeded: {drawdown_percent:.2f}% (limit: {self.max_drawdown_limit}%)"
                )
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking drawdown limit: {e}")
            return False
    
    def check_consecutive_losses(self):
        """Check if consecutive losses exceed limit"""
        try:
            if self.consecutive_losses >= self.consecutive_losses_limit:
                self.activate_emergency_stop(
                    f"Consecutive losses limit exceeded: {self.consecutive_losses} (limit: {self.consecutive_losses_limit})"
                )
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking consecutive losses: {e}")
            return False
    
    def check_system_health(self):
        """Monitor system health and API connectivity"""
        try:
            # Check API connection
            if not self.api_client.test_connection():
                self.activate_emergency_stop("API connection lost")
                return True
                
            # Add other system health checks here
            # - Memory usage
            # - CPU usage
            # - Network connectivity
            # - Database connectivity (if applicable)
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            self.activate_emergency_stop("System health check failed")
            return True
    
    def check_balance_threshold(self, portfolio_data):
        """Check if balance falls below critical threshold"""
        try:
            current_balance = portfolio_data.get('total_balance', 0)
            
            # If balance falls below 50% of starting balance, trigger emergency stop
            if self.daily_start_balance > 0:
                balance_ratio = current_balance / self.daily_start_balance
                if balance_ratio < 0.5:  # 50% threshold
                    self.activate_emergency_stop(
                        f"Balance fell below critical threshold: {balance_ratio:.1%} of starting balance"
                    )
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error checking balance threshold: {e}")
            return False
    
    def activate_emergency_stop(self, reason):
        """Activate emergency stop system"""
        try:
            if self.is_active:
                return  # Already active
                
            self.is_active = True
            self.activation_reason = reason
            self.activation_time = datetime.now()
            
            logger.critical(f"EMERGENCY STOP ACTIVATED: {reason}")
            
            # Close all open positions
            self._close_all_positions()
            
            # Cancel all pending orders
            self._cancel_all_orders()
            
            # Send alerts
            self._send_emergency_alert(reason)
            
        except Exception as e:
            logger.error(f"Error activating emergency stop: {e}")
    
    def _close_all_positions(self):
        """Close all open positions immediately"""
        try:
            positions = self.api_client.get_positions()
            
            for position in positions:
                symbol = position.get('symbol', 'unknown')
                logger.warning(f"Emergency closing position: {symbol}")
                
                success = self.api_client.close_position(symbol, position.get('id'))
                if success:
                    logger.info(f"Successfully closed position: {symbol}")
                else:
                    logger.error(f"Failed to close position: {symbol}")
                    
        except Exception as e:
            logger.error(f"Error closing all positions: {e}")
    
    def _cancel_all_orders(self):
        """Cancel all pending orders"""
        try:
            # In real implementation, get and cancel all open orders
            logger.info("Cancelling all pending orders")
            
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
    
    def _send_emergency_alert(self, reason):
        """Send emergency alerts via various channels"""
        try:
            # In real implementation, send alerts via:
            # - Email
            # - SMS
            # - Slack/Discord webhook
            # - Push notifications
            
            alert_message = f"EMERGENCY STOP ACTIVATED\nReason: {reason}\nTime: {datetime.now()}"
            logger.critical(alert_message)
            
            # For demo, just log the alert
            print(f"\n{'='*50}")
            print("🚨 EMERGENCY STOP ALERT 🚨")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Reason: {reason}")
            print("All positions closed, trading halted")
            print(f"{'='*50}\n")
            
        except Exception as e:
            logger.error(f"Error sending emergency alert: {e}")
    
    def record_trade_result(self, is_profitable):
        """Record trade result for consecutive loss tracking"""
        try:
            if is_profitable:
                self.consecutive_losses = 0
            else:
                self.consecutive_losses += 1
                logger.debug(f"Consecutive losses: {self.consecutive_losses}")
                
        except Exception as e:
            logger.error(f"Error recording trade result: {e}")
    
    def can_trade(self):
        """Check if trading is allowed"""
        return not self.is_active
    
    def reset_emergency_stop(self, manual_override=False):
        """Reset emergency stop system"""
        try:
            if not self.is_active:
                return True
                
            # For safety, require manual override for certain conditions
            critical_reasons = ['API connection lost', 'System health check failed']
            
            if any(reason in self.activation_reason for reason in critical_reasons) and not manual_override:
                logger.warning("Manual override required to reset emergency stop for critical failures")
                return False
                
            self.is_active = False
            reset_reason = self.activation_reason
            self.activation_reason = None
            reset_time = datetime.now()
            
            logger.info(f"Emergency stop reset. Previous reason: {reset_reason}")
            
            # Send reset notification
            self._send_reset_notification(reset_reason, reset_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Error resetting emergency stop: {e}")
            return False
    
    def _send_reset_notification(self, previous_reason, reset_time):
        """Send notification when emergency stop is reset"""
        try:
            duration = reset_time - self.activation_time if self.activation_time else timedelta(0)
            
            message = f"Emergency stop reset after {duration}\nPrevious reason: {previous_reason}"
            logger.info(message)
            
            print(f"\n{'='*50}")
            print("✅ EMERGENCY STOP RESET")
            print(f"Time: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Duration: {duration}")
            print(f"Previous reason: {previous_reason}")
            print("Trading can resume")
            print(f"{'='*50}\n")
            
        except Exception as e:
            logger.error(f"Error sending reset notification: {e}")
    
    def _reset_daily_counters(self):
        """Reset daily counters if new day"""
        try:
            current_date = datetime.now().date()
            
            if current_date != self.last_reset_date:
                self.daily_start_balance = 0
                self.max_balance_today = 0
                self.last_reset_date = current_date
                
                logger.info("Daily counters reset for new trading day")
                
        except Exception as e:
            logger.error(f"Error resetting daily counters: {e}")
    
    def get_status(self):
        """Get emergency stop status"""
        try:
            return {
                'is_active': self.is_active,
                'activation_reason': self.activation_reason,
                'activation_time': self.activation_time.isoformat() if self.activation_time else None,
                'consecutive_losses': self.consecutive_losses,
                'daily_loss_limit': self.daily_loss_limit,
                'max_drawdown_limit': self.max_drawdown_limit,
                'can_trade': self.can_trade()
            }
            
        except Exception as e:
            logger.error(f"Error getting emergency stop status: {e}")
            return {
                'is_active': True,  # Fail safe
                'activation_reason': 'Error retrieving status',
                'can_trade': False
            }

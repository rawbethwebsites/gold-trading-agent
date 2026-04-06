# Gold Trading Guidelines

## Before You Start Trading

### ✅ Pre-Flight Checklist

- [ ] MT5 is running and connected to Exness demo
- [ ] Logged into Exness demo account in MT5
- [ ] XAUUSD visible in Market Watch
- [ ] Account balance showing in MT5
- [ ] Backend shows "MT5 Connected"
- [ ] Dashboard shows account type: "DEMO"
- [ ] Trading is enabled in .env
- [ ] You understand the risks

### ⚠️ Safety Rules (Non-Negotiable)

1. **Demo Only**: Never trade on real account with this system
2. **Start Small**: Maximum 1 position, 0.01 lots
3. **Daily Loss Limit**: Stop if you lose 2% in a day
4. **Check Signals**: Don't trade blindly - understand why
5. **Monitor**: Don't leave running unattended

## Understanding the Signals

### BUY Signal

**What it means**: System thinks gold will go up

**Required**: 2+ of these conditions:
- RSI < 30 (oversold)
- MACD bullish crossover
- Price at lower Bollinger Band
- EMA 9 > EMA 21 (uptrend)

**Action**: Consider buying

### SELL Signal

**What it means**: System thinks gold will go down

**Required**: 2+ of these conditions:
- RSI > 70 (overbought)
- MACD bearish crossover
- Price at upper Bollinger Band
- EMA 9 < EMA 21 (downtrend)

**Action**: Consider selling

### HOLD Signal

**What it means**: No clear direction, or mixed signals

**Action**: Wait for clearer signal

## Risk Management

### Position Sizing

| Account Balance | Lot Size | Risk per Trade |
|----------------|----------|----------------|
| $1,000 - $5,000 | 0.01 | ~$2-5 |
| $5,000 - $10,000 | 0.02 | ~$4-10 |
| $10,000+ | 0.05 | ~$10-25 |

### Stop Loss / Take Profit

- **Stop Loss (SL)**: 2 × ATR from entry
- **Take Profit (TP)**: 4 × ATR from entry
- **Risk/Reward**: 1:2 ratio

Example:
- Entry: $2,650.00
- ATR: $5.00
- SL: $2,640.00 (2 × $5 = $10 below)
- TP: $2,670.00 (4 × $5 = $20 above)

### Daily Limits

- **Max Loss**: 2% of account balance
- **Max Positions**: 1 at a time
- **Reset Time**: Daily at midnight

## Trading Best Practices

### Do's ✅

- ✅ Test in demo for at least a week
- ✅ Start with smallest lot size (0.01)
- ✅ Understand each signal before trading
- ✅ Check economic calendar (avoid news times)
- ✅ Keep MT5 open and connected
- ✅ Monitor your trades
- ✅ Close positions manually if needed
- ✅ Review trades at end of day

### Don'ts ❌

- ❌ Trade on real account
- ❌ Increase lot size after wins
- ❌ Trade during high-impact news
- ❌ Leave system running overnight initially
- ❌ Ignore multiple failed signals
- ❌ Chase losses
- ❌ Trade without stop loss

## Interpreting Indicators

### RSI (Relative Strength Index)

- **Below 30**: Oversold - potential buy
- **Above 70**: Overbought - potential sell
- **40-60**: Neutral - no signal

### MACD

- **MACD > Signal**: Bullish momentum
- **MACD < Signal**: Bearish momentum
- **Histogram growing**: Momentum increasing
- **Histogram shrinking**: Momentum decreasing

### Bollinger Bands

- **Price touches lower band**: Potential buy
- **Price touches upper band**: Potential sell
- **Price in middle**: Neutral
- **Bands widening**: High volatility
- **Bands squeezing**: Low volatility (breakout coming)

### EMA Alignment

- **EMA 9 > EMA 21 > SMA 50**: Strong uptrend
- **EMA 9 < EMA 21 < SMA 50**: Strong downtrend
- **Mixed**: Range-bound or transitioning

## Signal Strength

The system calculates signal strength from -1.0 (strong sell) to +1.0 (strong buy):

| Strength | Interpretation |
|----------|----------------|
| +0.6 to +1.0 | Strong buy |
| +0.3 to +0.6 | Moderate buy |
| -0.3 to +0.3 | Neutral/hold |
| -0.6 to -0.3 | Moderate sell |
| -1.0 to -0.6 | Strong sell |

## Common Mistakes

1. **Trading every signal**: Not all signals are equal
2. **Ignoring the trend**: Trade with the trend, not against it
3. **Overtrading**: Wait for high-confidence setups
4. **Moving stop loss**: Don't widen your stop
5. **Revenge trading**: Don't trade emotionally after losses

## When to Stop Trading

Stop for the day if:
- You've hit 2% daily loss limit
- You've had 3 consecutive losing trades
- You're feeling emotional/frustrated
- High-impact news is coming
- MT5 disconnects repeatedly

## Testing Your Setup

### Phase 1: Paper Trade (1 week)
- Enable mock mode
- Practice reading signals
- Don't risk real money

### Phase 2: Demo Trade (1-2 weeks)
- Use Exness demo with small lots
- Verify all systems working
- Build confidence

### Phase 3: Live Evaluation
- Only proceed if demo is profitable
- Consider very small real trades
- **Never** use this system for large real accounts

## Emergency Procedures

### If System Goes Wrong

1. **Close all positions** in MT5 immediately
2. **Stop the backend** (Ctrl+C)
3. **Check your account** in MT5
4. **Review logs** in backend terminal

### Contact & Support

- **Exness Support**: https://www.exness.com/help
- **MT5 Help**: Press F1 in MT5
- **System Issues**: Check backend logs

## Remember

> **This system is for educational purposes only.**
> 
> Past performance does not guarantee future results.
> Never trade with money you can't afford to lose.
> Always do your own research.

## Daily Trading Routine

1. **Start MT5** - Login to demo
2. **Start backend** - Check connection
3. **Open dashboard** - Verify data flowing
4. **Check economic calendar** - Note news times
5. **Wait for signals** - Be patient
6. **Evaluate signals** - Check confidence and reasons
7. **Place trades** - Small size, with SL/TP
8. **Monitor** - Watch positions
9. **Review** - End of day analysis
10. **Shutdown** - Close everything

---

**Last Updated**: 2024
**Version**: 1.0
**Risk Level**: High (Demo Only)

"""
SMC (Smart Money Concepts) Pattern Detection — Algorithmic

Detects key institutional trading patterns from OHLCV data:
1. Swing Highs/Lows — structural pivots
2. Liquidity Sweeps — stop hunts above/below swing points
3. CHoCH (Change of Character) — trend reversal confirmation
4. BOS (Break of Structure) — trend continuation
5. FVG (Fair Value Gap) — 3-candle imbalance zones
6. Order Blocks — institutional supply/demand zones
7. Breaker Blocks — failed order blocks that flip to opposite zone

Academic references:
- Market microstructure theory (O'Hara, 1995)
- Liquidity and price discovery (Hasbrouck, 2007)
- Order flow and institutional trading (Harris, 2003)
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Direction(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


class PatternType(Enum):
    SWING_HIGH = "swing_high"
    SWING_LOW = "swing_low"
    LIQUIDITY_SWEEP_HIGH = "liquidity_sweep_high"
    LIQUIDITY_SWEEP_LOW = "liquidity_sweep_low"
    CHOCH_BULLISH = "choch_bullish"
    CHOCH_BEARISH = "choch_bearish"
    BOS_BULLISH = "bos_bullish"
    BOS_BEARISH = "bos_bearish"
    FVG_BULLISH = "fvg_bullish"
    FVG_BEARISH = "fvg_bearish"
    ORDER_BLOCK_BULLISH = "order_block_bullish"
    ORDER_BLOCK_BEARISH = "order_block_bearish"
    BREAKER_BULLISH = "breaker_bullish"
    BREAKER_BEARISH = "breaker_bearish"


@dataclass
class Pattern:
    pattern_type: PatternType
    index: int                      # Bar index where detected
    price_level: float              # Key price level
    price_high: Optional[float] = None
    price_low: Optional[float] = None
    strength: float = 1.0           # 0-1 confidence
    zone_top: Optional[float] = None
    zone_bottom: Optional[float] = None
    active: bool = True             # Still valid / not mitigated


class SMCDetector:
    """
    Detects Smart Money Concepts patterns from OHLCV DataFrame.
    
    Supports both daily and intraday (1H/4H) timeframes — thresholds
    auto-scale based on the `timeframe` parameter.
    
    Usage:
        detector = SMCDetector(df, swing_lookback=5, timeframe="1h")
        patterns = detector.detect_all()
    """
    
    def __init__(self, df: pd.DataFrame, swing_lookback: int = 5, timeframe: str = "1d"):
        """
        Args:
            df: OHLCV DataFrame (must have Open, High, Low, Close columns)
            swing_lookback: Number of bars on each side to confirm a swing point
            timeframe: "1h", "4h", or "1d" — scales detection thresholds
        """
        self.df = df.copy().reset_index(drop=True)
        self.n = len(df)
        self.lb = swing_lookback
        self.open = df["Open"].values
        self.high = df["High"].values
        self.low = df["Low"].values
        self.close = df["Close"].values
        self.volume = df["Volume"].values if "Volume" in df.columns else np.ones(self.n)
        self.timeframe = timeframe
        
        # Scale thresholds by timeframe (1H moves are ~5-8x smaller than daily)
        self._tf_scale = {"1h": 0.15, "4h": 0.4, "1d": 1.0}.get(timeframe, 1.0)
        
        self.swing_highs = []
        self.swing_lows = []
        self.patterns = []
    
    def detect_all(self) -> list[Pattern]:
        """Run full SMC detection pipeline."""
        self._detect_swings()
        self._detect_bos_choch()
        self._detect_liquidity_sweeps()
        self._detect_fvg()
        self._detect_order_blocks()
        self._detect_breaker_blocks()
        return self.patterns
    
    # ------------------------------------------------------------------
    # 1. SWING HIGHS / LOWS
    # ------------------------------------------------------------------
    def _detect_swings(self):
        """
        A swing high is a bar whose High is higher than the highs
        of `lb` bars on both sides. Vice versa for swing low.
        """
        for i in range(self.lb, self.n - self.lb):
            # Swing High
            left_highs = self.high[i - self.lb : i]
            right_highs = self.high[i + 1 : i + self.lb + 1]
            if self.high[i] > left_highs.max() and self.high[i] > right_highs.max():
                self.swing_highs.append((i, self.high[i]))
                self.patterns.append(Pattern(
                    pattern_type=PatternType.SWING_HIGH,
                    index=i, price_level=self.high[i],
                ))
            
            # Swing Low
            left_lows = self.low[i - self.lb : i]
            right_lows = self.low[i + 1 : i + self.lb + 1]
            if self.low[i] < left_lows.min() and self.low[i] < right_lows.min():
                self.swing_lows.append((i, self.low[i]))
                self.patterns.append(Pattern(
                    pattern_type=PatternType.SWING_LOW,
                    index=i, price_level=self.low[i],
                ))
    
    # ------------------------------------------------------------------
    # 2. BOS (Break of Structure) / CHoCH (Change of Character)
    # ------------------------------------------------------------------
    def _detect_bos_choch(self):
        """
        BOS: Price breaks a swing point IN the direction of the trend.
             - Bullish BOS: breaks above a swing high while in uptrend
             - Bearish BOS: breaks below a swing low while in downtrend
        
        CHoCH: Price breaks a swing point AGAINST the trend direction.
               - Bullish CHoCH: was in downtrend, breaks above swing high → reversal
               - Bearish CHoCH: was in uptrend, breaks below swing low → reversal
        
        Trend determined by comparing consecutive swing highs/lows.
        """
        if len(self.swing_highs) < 2 or len(self.swing_lows) < 2:
            return
        
        # Track trend: higher highs + higher lows = uptrend
        current_trend = None  # 'up' or 'down'
        
        # Combine and sort swings by index
        all_swings = (
            [(i, p, 'high') for i, p in self.swing_highs] +
            [(i, p, 'low') for i, p in self.swing_lows]
        )
        all_swings.sort(key=lambda x: x[0])
        
        prev_sh = None  # previous swing high
        prev_sl = None  # previous swing low
        
        for idx, price, stype in all_swings:
            if stype == 'high':
                if prev_sh is not None:
                    if price > prev_sh[1]:
                        current_trend = 'up'
                    elif price < prev_sh[1]:
                        current_trend = 'down'
                prev_sh = (idx, price)
            else:
                if prev_sl is not None:
                    if price > prev_sl[1]:
                        current_trend = 'up'
                    elif price < prev_sl[1]:
                        current_trend = 'down'
                prev_sl = (idx, price)
        
        # Now scan for breaks
        for i in range(self.lb * 2, self.n):
            # Check if current close breaks any recent swing high
            recent_highs = [(si, sp) for si, sp in self.swing_highs if si < i and i - si < 60]
            for si, sp in recent_highs:
                if self.close[i] > sp and self.close[i-1] <= sp:
                    # Determine if BOS or CHoCH based on recent trend at that swing
                    trend_at_break = self._get_local_trend(si)
                    if trend_at_break == 'down':
                        # Was downtrend, broke high → CHoCH bullish
                        self.patterns.append(Pattern(
                            pattern_type=PatternType.CHOCH_BULLISH,
                            index=i, price_level=sp,
                            strength=min(1.0, (self.close[i] - sp) / sp * 100),
                        ))
                    elif trend_at_break == 'up':
                        # Was uptrend, broke high → BOS bullish
                        self.patterns.append(Pattern(
                            pattern_type=PatternType.BOS_BULLISH,
                            index=i, price_level=sp,
                        ))
                    break  # Only first break per bar
            
            # Check if current close breaks any recent swing low
            recent_lows = [(si, sp) for si, sp in self.swing_lows if si < i and i - si < 60]
            for si, sp in recent_lows:
                if self.close[i] < sp and self.close[i-1] >= sp:
                    trend_at_break = self._get_local_trend(si)
                    if trend_at_break == 'up':
                        self.patterns.append(Pattern(
                            pattern_type=PatternType.CHOCH_BEARISH,
                            index=i, price_level=sp,
                            strength=min(1.0, (sp - self.close[i]) / sp * 100),
                        ))
                    elif trend_at_break == 'down':
                        self.patterns.append(Pattern(
                            pattern_type=PatternType.BOS_BEARISH,
                            index=i, price_level=sp,
                        ))
                    break
    
    def _get_local_trend(self, at_index: int) -> Optional[str]:
        """Determine trend at a given bar index based on recent swing structure."""
        recent_highs = [(i, p) for i, p in self.swing_highs if i <= at_index][-3:]
        recent_lows = [(i, p) for i, p in self.swing_lows if i <= at_index][-3:]
        
        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            hh = recent_highs[-1][1] > recent_highs[-2][1]  # higher high
            hl = recent_lows[-1][1] > recent_lows[-2][1]    # higher low
            if hh and hl:
                return 'up'
            lh = recent_highs[-1][1] < recent_highs[-2][1]  # lower high
            ll = recent_lows[-1][1] < recent_lows[-2][1]    # lower low
            if lh and ll:
                return 'down'
        return None
    
    # ------------------------------------------------------------------
    # 3. LIQUIDITY SWEEPS
    # ------------------------------------------------------------------
    def _detect_liquidity_sweeps(self):
        """
        Liquidity sweep: price briefly exceeds a swing point (grabbing stops)
        then reverses back. The wick exceeds but body doesn't hold.
        
        Bullish sweep (of lows): Low goes below swing low, but close stays above
        Bearish sweep (of highs): High goes above swing high, but close stays below
        """
        for i in range(1, self.n):
            # Sweep of swing lows (bullish — price dips below then recovers)
            for si, sp in self.swing_lows:
                if si >= i or i - si > 40:
                    continue
                if (self.low[i] < sp and         # Wick goes below swing low
                    self.close[i] > sp and        # Close recovers above
                    self.close[i] > self.open[i]  # Bullish candle
                ):
                    self.patterns.append(Pattern(
                        pattern_type=PatternType.LIQUIDITY_SWEEP_LOW,
                        index=i, price_level=sp,
                        price_low=self.low[i],
                        strength=min(1.0, abs(sp - self.low[i]) / sp * 200),
                    ))
                    break
            
            # Sweep of swing highs (bearish — price spikes above then drops)
            for si, sp in self.swing_highs:
                if si >= i or i - si > 40:
                    continue
                if (self.high[i] > sp and          # Wick goes above swing high
                    self.close[i] < sp and          # Close drops below
                    self.close[i] < self.open[i]    # Bearish candle
                ):
                    self.patterns.append(Pattern(
                        pattern_type=PatternType.LIQUIDITY_SWEEP_HIGH,
                        index=i, price_level=sp,
                        price_high=self.high[i],
                        strength=min(1.0, abs(self.high[i] - sp) / sp * 200),
                    ))
                    break
    
    # ------------------------------------------------------------------
    # 4. FAIR VALUE GAPS (FVG)
    # ------------------------------------------------------------------
    def _detect_fvg(self):
        """
        FVG is a 3-candle pattern where there's a gap between candle 1 and candle 3.
        
        Bullish FVG: Candle 1 High < Candle 3 Low (gap up, unfilled)
        Bearish FVG: Candle 1 Low > Candle 3 High (gap down, unfilled)
        
        These represent institutional imbalance — price tends to return to fill them.
        """
        for i in range(2, self.n):
            # Bullish FVG: gap between candle[i-2].high and candle[i].low
            if self.low[i] > self.high[i-2]:
                gap_size = self.low[i] - self.high[i-2]
                mid_price = (self.low[i] + self.high[i-2]) / 2
                # Must be a meaningful gap (> 0.05% of price)
                if gap_size / mid_price > 0.0005:
                    self.patterns.append(Pattern(
                        pattern_type=PatternType.FVG_BULLISH,
                        index=i, price_level=mid_price,
                        zone_top=self.low[i],
                        zone_bottom=self.high[i-2],
                        strength=min(1.0, gap_size / mid_price * 100),
                    ))
            
            # Bearish FVG: gap between candle[i].high and candle[i-2].low
            if self.high[i] < self.low[i-2]:
                gap_size = self.low[i-2] - self.high[i]
                mid_price = (self.low[i-2] + self.high[i]) / 2
                if gap_size / mid_price > 0.0005:
                    self.patterns.append(Pattern(
                        pattern_type=PatternType.FVG_BEARISH,
                        index=i, price_level=mid_price,
                        zone_top=self.low[i-2],
                        zone_bottom=self.high[i],
                        strength=min(1.0, gap_size / mid_price * 100),
                    ))
    
    # ------------------------------------------------------------------
    # 5. ORDER BLOCKS
    # ------------------------------------------------------------------
    def _detect_order_blocks(self):
        """
        Order Block: The last opposite-color candle before a strong impulsive move.
        
        Bullish OB: Last bearish candle before a strong bullish move
        Bearish OB: Last bullish candle before a strong bearish move
        
        The zone is the body of the order block candle.
        Represents institutional accumulation/distribution.
        """
        min_impulse = 3  # bars for impulsive move
        
        for i in range(1, self.n - min_impulse):
            # Check for bullish impulse (strong up move over next few bars)
            future_close = self.close[min(i + min_impulse, self.n - 1)]
            move = (future_close - self.close[i]) / self.close[i]
            
            if move > 0.01 * self._tf_scale:  # Bullish impulse (scaled by timeframe)
                # Find last bearish candle at or before i
                for j in range(i, max(i - 5, 0) - 1, -1):
                    if self.close[j] < self.open[j]:  # Bearish candle
                        self.patterns.append(Pattern(
                            pattern_type=PatternType.ORDER_BLOCK_BULLISH,
                            index=j, price_level=(self.open[j] + self.close[j]) / 2,
                            zone_top=self.open[j],
                            zone_bottom=self.close[j],
                            strength=min(1.0, move * 50),
                        ))
                        break
            
            elif move < -0.01 * self._tf_scale:  # Bearish impulse (scaled by timeframe)
                for j in range(i, max(i - 5, 0) - 1, -1):
                    if self.close[j] > self.open[j]:  # Bullish candle
                        self.patterns.append(Pattern(
                            pattern_type=PatternType.ORDER_BLOCK_BEARISH,
                            index=j, price_level=(self.open[j] + self.close[j]) / 2,
                            zone_top=self.close[j],
                            zone_bottom=self.open[j],
                            strength=min(1.0, abs(move) * 50),
                        ))
                        break
    
    # ------------------------------------------------------------------
    # 6. BREAKER BLOCKS
    # ------------------------------------------------------------------
    def _detect_breaker_blocks(self):
        """
        Breaker Block: An order block that gets violated (broken through),
        then the zone flips from support to resistance (or vice versa).
        
        Bullish breaker: A bearish OB gets broken to the upside →
                         the OB zone becomes support on retest
        Bearish breaker: A bullish OB gets broken to the downside →
                         the OB zone becomes resistance on retest
        """
        ob_patterns = [p for p in self.patterns if 'order_block' in p.pattern_type.value]
        
        for ob in ob_patterns:
            if ob.zone_top is None or ob.zone_bottom is None:
                continue
            
            # Look for price breaking through the OB zone after it formed
            for i in range(ob.index + 1, min(ob.index + 50, self.n)):
                if ob.pattern_type == PatternType.ORDER_BLOCK_BEARISH:
                    # Bearish OB broken to downside → bearish breaker
                    if self.close[i] < ob.zone_bottom:
                        self.patterns.append(Pattern(
                            pattern_type=PatternType.BREAKER_BEARISH,
                            index=i, price_level=ob.price_level,
                            zone_top=ob.zone_top,
                            zone_bottom=ob.zone_bottom,
                            strength=ob.strength * 0.8,
                        ))
                        ob.active = False
                        break
                
                elif ob.pattern_type == PatternType.ORDER_BLOCK_BULLISH:
                    # Bullish OB broken to upside → bullish breaker
                    if self.close[i] > ob.zone_top:
                        self.patterns.append(Pattern(
                            pattern_type=PatternType.BREAKER_BULLISH,
                            index=i, price_level=ob.price_level,
                            zone_top=ob.zone_top,
                            zone_bottom=ob.zone_bottom,
                            strength=ob.strength * 0.8,
                        ))
                        ob.active = False
                        break
    
    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def get_patterns_by_type(self, ptype: PatternType) -> list[Pattern]:
        return [p for p in self.patterns if p.pattern_type == ptype]
    
    def get_setup_at(self, bar_index: int, lookback: int = 30) -> dict:
        """
        Check for the user's SMC setup sequence near a given bar:
        1. Liquidity sweep
        2. CHoCH
        3. FVG or breaker block for entry
        
        Returns setup info if found, None otherwise.
        """
        start = max(0, bar_index - lookback)
        recent = [p for p in self.patterns if start <= p.index <= bar_index]
        
        sweeps = [p for p in recent if 'liquidity_sweep' in p.pattern_type.value]
        chochs = [p for p in recent if 'choch' in p.pattern_type.value]
        fvgs = [p for p in recent if 'fvg' in p.pattern_type.value]
        breakers = [p for p in recent if 'breaker' in p.pattern_type.value]
        
        # Look for bullish setup: sweep low → bullish choch → bullish fvg/breaker
        bullish_sweeps = [p for p in sweeps if p.pattern_type == PatternType.LIQUIDITY_SWEEP_LOW]
        bullish_chochs = [p for p in chochs if p.pattern_type == PatternType.CHOCH_BULLISH]
        bullish_entries = ([p for p in fvgs if p.pattern_type == PatternType.FVG_BULLISH] +
                         [p for p in breakers if p.pattern_type == PatternType.BREAKER_BULLISH])
        
        if bullish_sweeps and bullish_chochs:
            # Check sequence: sweep before choch
            for sweep in bullish_sweeps:
                for choch in bullish_chochs:
                    if choch.index > sweep.index:
                        entries_after = [e for e in bullish_entries if e.index >= choch.index]
                        return {
                            "direction": "bullish",
                            "sweep": sweep,
                            "choch": choch,
                            "entry_zone": entries_after[0] if entries_after else None,
                            "confidence": min(1.0, (sweep.strength + choch.strength) / 2),
                        }
        
        # Look for bearish setup: sweep high → bearish choch → bearish fvg/breaker
        bearish_sweeps = [p for p in sweeps if p.pattern_type == PatternType.LIQUIDITY_SWEEP_HIGH]
        bearish_chochs = [p for p in chochs if p.pattern_type == PatternType.CHOCH_BEARISH]
        bearish_entries = ([p for p in fvgs if p.pattern_type == PatternType.FVG_BEARISH] +
                         [p for p in breakers if p.pattern_type == PatternType.BREAKER_BEARISH])
        
        if bearish_sweeps and bearish_chochs:
            for sweep in bearish_sweeps:
                for choch in bearish_chochs:
                    if choch.index > sweep.index:
                        entries_after = [e for e in bearish_entries if e.index >= choch.index]
                        return {
                            "direction": "bearish",
                            "sweep": sweep,
                            "choch": choch,
                            "entry_zone": entries_after[0] if entries_after else None,
                            "confidence": min(1.0, (sweep.strength + choch.strength) / 2),
                        }
        
        return None
    
    def get_label_for_bar(self, bar_index: int, forward_bars: int = 10) -> Optional[str]:
        """
        Generate a training label for a chart ending at bar_index.
        
        Uses a two-tier approach:
        1. Check for full SMC setup (sweep → CHoCH → entry) — high confidence
        2. Check for ANY bullish/bearish SMC pattern — moderate confidence
        3. No patterns → neutral
        
        Returns: 'bullish', 'bearish', or 'neutral'
        """
        if bar_index + forward_bars >= self.n:
            return None  # Not enough future data
        
        future_return = (self.close[bar_index + forward_bars] - self.close[bar_index]) / self.close[bar_index]
        # Balanced threshold: ~0.09% for 1H, 0.6% for daily
        outcome_threshold = 0.006 * self._tf_scale
        
        # Tier 1: Full setup (sweep + CHoCH) — only label if outcome confirms
        setup = self.get_setup_at(bar_index)
        if setup is not None:
            if setup["direction"] == "bullish" and future_return > outcome_threshold:
                return "bullish"
            elif setup["direction"] == "bearish" and future_return < -outcome_threshold:
                return "bearish"
            # Don't return neutral here — fall through to check other tiers
        
        # Tier 2: Any recent bullish/bearish pattern (CHoCH, sweep, FVG, OB)
        lookback = 15
        start = max(0, bar_index - lookback)
        recent = [p for p in self.patterns if start <= p.index <= bar_index]
        
        bullish_patterns = [p for p in recent if p.pattern_type in (
            PatternType.CHOCH_BULLISH, PatternType.LIQUIDITY_SWEEP_LOW,
            PatternType.FVG_BULLISH, PatternType.ORDER_BLOCK_BULLISH,
        )]
        bearish_patterns = [p for p in recent if p.pattern_type in (
            PatternType.CHOCH_BEARISH, PatternType.LIQUIDITY_SWEEP_HIGH,
            PatternType.FVG_BEARISH, PatternType.ORDER_BLOCK_BEARISH,
        )]
        
        # Need at least 1 confirming pattern + outcome confirmation
        strong_threshold = outcome_threshold * 1.5
        if len(bullish_patterns) >= 1 and future_return > strong_threshold:
            return "bullish"
        if len(bearish_patterns) >= 1 and future_return < -strong_threshold:
            return "bearish"
        
        # Tier 3: Pure price movement (no patterns, but strong move)
        mega_threshold = outcome_threshold * 3
        if future_return > mega_threshold:
            return "bullish"
        if future_return < -mega_threshold:
            return "bearish"
        
        return "neutral"
    
    def summary(self) -> dict:
        """Pattern count summary."""
        counts = {}
        for p in self.patterns:
            name = p.pattern_type.value
            counts[name] = counts.get(name, 0) + 1
        return counts

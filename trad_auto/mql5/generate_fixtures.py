"""Generate deterministic MQL assertions from the unchanged Python reference.
Synthetic fixtures only, never market data or a profitability backtest.
"""
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'src'))
from trad_auto.core import Candle, Config, setup, structure


def main():
    rng = random.Random(91821)
    cases = []
    # Search deterministic random fixtures until both directions occur;
    # includes every prefix around each found signal, and opposing H1 filters.
    found = {"BUY": 0, "SELL": 0}
    for trial in range(20000):
        bars, price = [], 100.0
        for i in range(50):
            close = price + rng.uniform(-2, 2)
            bars.append(Candle(i * 300, price, max(price, close) + rng.uniform(0, 2), min(price, close) - rng.uniform(0, 2), close))
            price = close
        trend = structure(bars[:-2], 2)['trend']
        plan = setup(bars, Config(), trend)
        if plan['action'] != 'WAIT' and found[plan['action']] < 4:
            found[plan['action']] += 1
            for end in range(44, 51):
                for direction in (-1, 0, 1):
                    cases.append((bars[:end], direction))
        if min(found.values()) >= 4:
            break
    assert min(found.values()) >= 4, found
    # Equal extrema must not be pivots.
    cases.append(([Candle(i*300,100,101,99,100) for i in range(50)], 1))
    text = ['// Generated synthetic reference fixtures. DO NOT treat as market results.', 'bool RunCoreSelfTests()', '{', '   int failures=0;', '   MqlRates b[]; Setup s; double hi,lo;']
    previous = []
    for ci, (bars, direction) in enumerate(cases):
        plan = setup(bars, Config(), {-1:'bearish',0:'range',1:'bullish'}[direction])
        expected = {'BUY':1,'SELL':-1,'WAIT':0}[plan['action']]
        text += [f'   // Fixture {ci}; Python reference side={expected}', f'   ArrayResize(b,{len(bars)});']
        for i, b in enumerate(bars):
            if i < len(previous) and b == previous[i]:
                continue
            text += [f'   b[{i}].time={b.time};b[{i}].open={b.open:.17g};b[{i}].high={b.high:.17g};b[{i}].low={b.low:.17g};b[{i}].close={b.close:.17g};']
        previous = bars
        expected_trend = {'bullish':1,'bearish':-1,'range':0}[structure(bars,2)['trend']]
        text += [f'   if(Structure(b,ArraySize(b),2,hi,lo)!={expected_trend}) failures++;', f'   FindSetup(b,{direction},s);', f'   if(s.side!={expected}) failures++;']
        if expected:
            text += [f'   if(s.bos_index!={plan["bos"]["index"]} || MathAbs(s.stop-{plan["stop"]:.17g})>1e-8 || MathAbs(s.level-{plan["bos"]["level"]:.17g})>1e-8) failures++;']
    text += ['   if(FloorVolume(1,200,0.01,0.01,100)!=0) failures++;', '   if(MathAbs(FloorVolume(1,40,0.01,0.01,100)-0.02)>1e-10) failures++;', '   if(!ValidBars(b,300,15000)) failures++;', '   if(ValidBars(b,300,14999)) failures++;', '   if(ValidBars(b,300,15301)) failures++;', '   b[1].time=b[0].time; if(ValidBars(b,300,15000)) failures++;', f'   Print("CORE_SELFTEST fixtures={len(cases)} failures=",failures);', '   return failures==0;', '}']
    output = ROOT / 'CoreSelfTest.mqh'
    output.write_text('\n'.join(text)+'\n', encoding='utf-8')
    print({'fixtures':len(cases), 'positive_source_fixtures':found, 'output':str(output)})

if __name__ == '__main__':
    main()

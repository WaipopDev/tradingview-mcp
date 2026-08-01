# ปรับใช้ “151 Trading Strategies” กับ trad

Source: `/Users/waipop/Downloads/151 Trading Strategies.pdf`
Extraction note: อ่านจาก PDF แล้วบันทึกเฉพาะสรุป/การ map ที่ใช้กับ trad ไม่เก็บ full text ของ PDF ใน repo

เป้าหมายของไฟล์นี้คือแปลงหนังสือ/บทความเชิงกลยุทธ์ให้เป็น playbook ที่ใช้ได้กับ `tradingview-mcp` ใน repo `trad` โดยเน้นสิ่งที่ MCP มีข้อมูลรองรับจริง: ราคา, indicators, multi-timeframe, backtest, options chain/unusual activity, futures snapshot, news/sentiment

## หลักการคัดกรอง

1. ใช้ก่อน: กลยุทธ์ที่อาศัย OHLCV/indicator และรองรับด้วยเครื่องมือปัจจุบัน
2. ใช้เป็น proxy: กลยุทธ์ options/volatility สำหรับอ่าน positioning เช่น GLD options V/OI แทน OI ของ spot XAUUSD
3. เก็บเป็น roadmap: fixed income, credit, real estate, tax, distressed ต้องมี data source เฉพาะก่อนจึงค่อย implement
4. ทุกกลยุทธ์ต้องผ่าน regime filter: trend / range / volatility / event ก่อนให้ BUY/SELL

## Strategy universe จาก PDF

### Options / volatility structures
- สถานะใน trad: ใช้กับ `stock_options_chain`, `stock_options_unusual_activity`, GLD/options proxy, และการอ่าน IV/V-OI; ยังไม่ควรใช้เป็น spot XAUUSD entry โดยตรง
  1. Covered call
  2. Covered put
  3. Protective put
  4. Protective call
  5. Bull call spread
  6. Bull put spread
  7. Bear call spread
  8. Bear put spread
  9. Long synthetic forward
  10. Short synthetic forward
  11. Long combo
  12. Short combo
  13. Bull call ladder
  14. Bull put ladder
  15. Bear call ladder
  16. Bear put ladder
  17. Calendar call spread
  18. Calendar put spread
  19. Diagonal call spread
  20. Diagonal put spread
  21. Long straddle
  22. Long strangle
  23. Long guts
  24. Short straddle
  25. Short strangle
  26. Short guts
  27. Long call synthetic straddle
  28. Long put synthetic straddle
  29. Short call synthetic straddle
  30. Short put synthetic straddle
  31. Covered short straddle
  32. Covered short strangle
  33. Strap
  34. Strip
  35. Call ratio backspread
  36. Put ratio backspread
  37. Ratio call spread
  38. Ratio put spread
  39. Long call butterfly
  40. Modified call butterfly
  41. Long put butterfly
  42. Modified put butterfly
  43. Short call butterfly
  44. Short put butterfly
  45. "Long" iron butterfly
  46. "Short" iron butterfly
  47. Long call condor
  48. Long put condor
  49. Short call condor
  50. Short put condor
  51. Long iron condor
  52. Short iron condor
  53. Long box
  54. Collar
  55. Bullish short seagull spread
  56. Bearish long seagull spread
  57. Bearish short seagull spread
  58. Bullish long seagull spread

### Equities / ETFs / cross-sectional alpha
- สถานะใน trad: ใช้กับ stock screener, combined_analysis, backtest/compare_strategies; เหมาะกับ momentum, value, low-vol, pairs, sector rotation
  59. Price-momentum
  60. Earnings-momentum
  61. Value
  62. Low-volatility anomaly
  63. Implied volatility
  64. Multifactor portfolio
  65. Residual momentum
  66. Pairs trading
  67. Mean-reversion – single cluster
  68. Mean-reversion – multiple clusters
  69. Single moving average
  70. Two moving averages
  71. Three moving averages
  72. Support and resistance
  73. Channel
  74. Event-driven – M&A
  75. Machine learning – single-stock KNN
  76. Statistical arbitrage – optimization
  77. Market-making
  78. Alpha combos
  79. Sector momentum rotation
  80. Sector momentum rotation with MA filter
  81. Dual-momentum sector rotation
  82. Alpha rotation
  83. R-squared
  84. Mean-reversion
  85. Leveraged ETFs (LETFs)
  86. Multi-asset trend following

### Fixed income / credit
- สถานะใน trad: ใช้เป็น macro context เท่านั้น เว้นแต่เพิ่มข้อมูล yield/CDS เพิ่มในอนาคต
  87. Bullets
  88. Barbells
  89. Ladders
  90. Bond immunization
  91. Dollar-duration-neutral butterfly
  92. Fifty-fifty butterfly
  93. Regression-weighted butterfly
  94. Maturity-weighted butterfly
  95. Low-risk factor
  96. Value factor
  97. Carry factor
  98. Rolling down the yield curve
  99. Yield curve spread (flatteners & steepeners)
  100. CDS basis arbitrage
  101. Swap-spread arbitrage
  102. Cash-and-carry arbitrage

### Futures / commodities / FX / volatility
- สถานะใน trad: ใช้กับ futures tools, XAUUSD/commodities, FX, carry, trend, calendar spread, hedging pressure
  103. Dispersion trading in equity indexes
  104. Dispersion trading – subset portfolio
  105. Intraday arbitrage between index ETFs
  106. Index volatility targeting with risk-free asset
  107. VIX futures basis trading
  108. Volatility carry with two ETNs
  109. Hedging short VXX with VIX futures
  110. Volatility risk premium
  111. Volatility risk premium with Gamma hedging
  112. Volatility skew – long risk reversal
  113. Volatility trading with variance swaps
  114. Moving averages with HP filter
  115. Carry trade
  116. High-minus-low carry
  117. Dollar carry trade
  118. Momentum & carry combo
  119. FX triangular arbitrage
  120. Roll yields
  121. Trading based on hedging pressure
  122. Portfolio diversification with commodities
  123. Skewness premium
  124. Trading with pricing models
  125. Hedging risk with futures
  126. Cross-hedging
  127. Interest rate risk hedging
  128. Calendar spread
  129. Contrarian trading (mean-reversion)
  130. Contrarian trading – market activity
  131. Trend following (momentum)

### Structured/distressed/real estate/cash/misc
- สถานะใน trad: ส่วนใหญ่เป็น long-horizon/special situation; เก็บเป็น reference ไม่ใช้กับ intraday trad ตอนนี้
  132. Carry, equity tranche – index hedging
  133. Carry, senior/mezzanine – index hedging
  134. Carry – tranche hedging
  135. Carry – CDS hedging
  136. CDOs – curve trades
  137. Mortgage-backed security (MBS) trading
  138. Convertible arbitrage
  139. Convertible option-adjusted spread
  140. Municipal bond tax arbitrage
  141. Cross-border tax arbitrage
  142. Cross-border tax arbitrage with options
  143. Inflation hedging – inflation swaps
  144. TIPS-Treasury arbitrage
  145. Weather risk – demand hedging
  146. Energy – spark spread
  147. Buying and holding distressed debt
  148. Active distressed investing
  149. Planning a reorganization
  150. Buying outstanding debt
  151. Loan-to-own
  152. Distress risk puzzle
  153. Distress risk puzzle – risk management
  154. Mixed-asset diversification with real estate
  155. Intra-asset diversification within real estate
  156. Property type diversification
  157. Economic diversification
  158. Property type and geographic diversification
  159. Real estate momentum – regional approach
  160. Inflation hedging with real estate
  161. Fix-and-flip
  162. Money laundering – the dark side of cash
  163. Liquidity management
  164. Repurchase agreement (REPO)
  165. Pawnbroking
  166. Loan sharking
  167. Artificial neural network (ANN)
  168. Sentiment analysis – naı̈ve Bayes Bernoulli

### Machine learning / macro
- สถานะใน trad: ใช้เป็น roadmap: feature engineering, sentiment, macro announcement filters, model validation
  169. Fundamental macro momentum
  170. Global macro inflation hedge
  171. Global fixed-income strategy
  172. Trading on economic announcements

## Mapping ที่นำมาใช้กับ trad ตอนนี้

| PDF concept | trad tool/function | การใช้จริง |
|---|---|---|
| Price momentum / trend following / multi-asset trend following | `coin_analysis`, `multi_timeframe_analysis`, `compare_strategies`, `backtest_strategy` | ใช้หา BUY เมื่อ MTF เรียงขึ้น, ราคาเหนือ MA/EMA, momentum ยืนยัน; SELL เมื่อโครงสร้างกลับลง |
| Mean reversion / contrarian / Bollinger | `bollinger_scan`, `coin_analysis`, `backtest_strategy(strategy="bollinger")` | ใช้ในตลาด range: รอแตะ band + RSI extreme + liquidity sweep แล้วกลับเข้า range |
| Moving average 1/2/3 เส้น | `backtest_strategy(strategy="ema_cross"|"triple_ema")`, indicators ใน `coin_analysis` | ใช้เป็น trend filter ไม่ใช้เป็น trigger เดี่ยว |
| Channel / support and resistance / Donchian | `backtest_strategy(strategy="donchian")`, `top_gainers`, `top_losers` | ใช้กับ breakout หลัง compression; SL หลัง channel opposite/ATR |
| Keltner / ATR-normalized breakout | `backtest_strategy(strategy="keltner_breakout")`, ATR ใน indicators | ใช้เมื่อ volatility expansion มากับ volume |
| Options spreads / straddle / strangle / skew / volatility risk premium | `stock_options_chain`, `stock_options_unusual_activity` | ใช้ตีความ GLD/SPY/NVDA options flow, IV, V/OI; สำหรับ XAUUSD ใช้ GLD เป็น proxy |
| Futures roll/calendar/carry/hedging pressure | `futures_category_snapshot`, `futures_market_overview`, `futures_top_movers` | ใช้เป็น backdrop ของ metals/energy/index futures; ยังไม่มี OI/CoT โดยตรง |
| Sentiment / Naive Bayes / news-event ideas | `combined_analysis`, `market_sentiment`, `financial_news` | ใช้เป็น event/regime filter ไม่ให้สวนข่าวแรง |
| Machine learning ANN/KNN | future module | ต้องเพิ่ม feature store + walk-forward validation ก่อนใช้จริง |

## Rule engine ที่ควรใช้ในการตอบ trade plan

### 1) เลือก regime ก่อนเลือก strategy

- Trend: ใช้ momentum, MA/EMA, Donchian, Keltner, Supertrend
- Range: ใช้ mean reversion, Bollinger, support/resistance, liquidity sweep
- High-vol/event: ลดขนาด position, ใช้ options/sentiment/futures backdrop ตรวจ confirmation
- Low-vol squeeze: ใช้ Bollinger Band Width + volume breakout รอทิศทาง

### 2) Score รวมสำหรับ BUY/SELL

ให้คิดคะแนนภายในก่อนตอบ:

- MTF alignment: 0-25
- Structure/SMC/liquidity: 0-25
- Strategy fit ตาม regime: 0-20
- Volume/ATR/volatility confirmation: 0-15
- Options/futures/sentiment proxy: 0-15

Decision:
- 70+ = BUY/SELL ได้ถ้า RR ผ่าน
- 55-69 = รอ confirmation
- <55 = งดเทรด

### 3) Template การอ้างอิง PDF ในคำตอบ

ใช้แบบสั้น: “แนวคิดจาก 151 Trading Strategies ที่ใช้กับ setup นี้คือ trend following + channel breakout + volatility confirmation” แล้วค่อยให้ Entry/SL/TP

## Candidate implementation backlog

1. `strategy_regime_score`: รวม MTF + volatility + volume + indicator state เป็นคะแนน
2. `strategy_recommendation`: เลือก strategy family จาก trend/range/squeeze/event
3. `pairs_trading_backtest`: ต้องเพิ่ม multi-symbol Yahoo fetch และ hedge ratio
4. `sector_rotation`: ใช้ stock screener ต่อกลุ่ม sector/ETF
5. `options_strategy_analyzer`: สรุป straddle/strangle/spread payoff จาก options chain
6. `macro_event_filter`: ผูก financial_news/market_sentiment กับ volatility guard

## Notes สำหรับ XAUUSD

- Spot XAUUSD ไม่มี centralized OI; ใช้ GLD options V/OI และ COMEX gold futures volume เป็น proxy
- กลยุทธ์ที่เหมาะกับ intraday XAUUSD จาก PDF: trend following, mean reversion, support/resistance, channel, moving averages, carry/macro context, volatility/event filter
- ไม่ใช้ options payoff เป็นจุดเข้า spot ตรง ๆ; ใช้เป็น sentiment/positioning backdrop เท่านั้น

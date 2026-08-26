#property copyright "WTN IT Group"
#property version   "1.00"
#property strict
#property description "Read-only broker market-data bridge for Hermes/MGT"
#property indicator_chart_window
#property indicator_plots 0

input string InpSymbol = "GOLD";              // Broker symbol to export
input int    InpPublishIntervalSeconds = 1;   // Snapshot interval
input int    InpHistoryBars = 60;              // Bars used for volume and S/R context
input string InpOutputFile = "MT5MarketDataBridge\\GOLD.json";

#define TF_COUNT 4

ENUM_TIMEFRAMES g_timeframes[TF_COUNT] = {PERIOD_M15, PERIOD_H1, PERIOD_H4, PERIOD_D1};
string g_names[TF_COUNT] = {"15m", "1h", "4h", "1D"};
int g_rsi[TF_COUNT], g_atr[TF_COUNT], g_ema20[TF_COUNT], g_ema50[TF_COUNT], g_ema200[TF_COUNT];
int g_macd[TF_COUNT], g_bands[TF_COUNT], g_adx[TF_COUNT];
int g_digits = 2;

string JsonEscape(string value)
{
   StringReplace(value, "\\", "\\\\");
   StringReplace(value, "\"", "\\\"");
   StringReplace(value, "\r", "\\r");
   StringReplace(value, "\n", "\\n");
   return value;
}

string Num(const double value)
{
   return DoubleToString(value, g_digits + 6);
}

bool BufferValue(const int handle, const int buffer, const int shift, double &value)
{
   if(handle == INVALID_HANDLE)
      return false;
   double data[1];
   if(CopyBuffer(handle, buffer, shift, 1, data) != 1)
      return false;
   value = data[0];
   return MathIsValidNumber(value);
}

string BarJson(const MqlRates &bar)
{
   return StringFormat(
      "{\"time\":%I64d,\"open\":%s,\"high\":%s,\"low\":%s,\"close\":%s,\"tick_volume\":%I64d}",
      (long)bar.time, Num(bar.open), Num(bar.high), Num(bar.low), Num(bar.close), (long)bar.tick_volume
   );
}

bool FrameJson(const int index, string &json)
{
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   int requested = MathMax(25, InpHistoryBars);
   int copied = CopyRates(InpSymbol, g_timeframes[index], 0, requested, rates);
   if(copied < 25)
   {
      PrintFormat("MT5BRIDGE: %s CopyRates incomplete: %d/%d", g_names[index], copied, requested);
      return false;
   }

   double rsi, rsi_previous, atr, ema20, ema50, ema200;
   double macd, macd_signal, bb_middle, bb_upper, bb_lower, adx;
   if(!BufferValue(g_rsi[index], 0, 0, rsi) ||
      !BufferValue(g_rsi[index], 0, 1, rsi_previous) ||
      !BufferValue(g_atr[index], 0, 0, atr) ||
      !BufferValue(g_ema20[index], 0, 0, ema20) ||
      !BufferValue(g_ema50[index], 0, 0, ema50) ||
      !BufferValue(g_ema200[index], 0, 0, ema200) ||
      !BufferValue(g_macd[index], 0, 0, macd) ||
      !BufferValue(g_macd[index], 1, 0, macd_signal) ||
      !BufferValue(g_bands[index], 0, 0, bb_middle) ||
      !BufferValue(g_bands[index], 1, 0, bb_upper) ||
      !BufferValue(g_bands[index], 2, 0, bb_lower) ||
      !BufferValue(g_adx[index], 0, 0, adx))
   {
      PrintFormat("MT5BRIDGE: %s indicator buffers are not ready", g_names[index]);
      return false;
   }

   double volume_sum = 0.0;
   int volume_count = 0;
   double local_low = rates[1].low;
   double local_high = rates[1].high;
   int limit = MathMin(copied - 1, 20);
   for(int i = 1; i <= limit; i++)
   {
      volume_sum += (double)rates[i].tick_volume;
      volume_count++;
      local_low = MathMin(local_low, rates[i].low);
      local_high = MathMax(local_high, rates[i].high);
   }
   double avg_volume = volume_count > 0 ? volume_sum / volume_count : 0.0;
   string trend = "Neutral/Ranging";
   if(rates[0].close > ema20 && ema20 > ema50)
      trend = "Bullish";
   else if(rates[0].close < ema20 && ema20 < ema50)
      trend = "Bearish";

   json = "\"" + g_names[index] + "\":{";
   json += "\"bar\":" + BarJson(rates[0]) + ",";
   json += "\"previous_bar\":" + BarJson(rates[1]) + ",";
   json += "\"rsi\":" + Num(rsi) + ",\"rsi_previous\":" + Num(rsi_previous) + ",";
   json += "\"atr\":" + Num(atr) + ",";
   json += "\"ema20\":" + Num(ema20) + ",\"ema50\":" + Num(ema50) + ",\"ema200\":" + Num(ema200) + ",";
   json += "\"macd\":" + Num(macd) + ",\"macd_signal\":" + Num(macd_signal) + ",\"macd_histogram\":" + Num(macd - macd_signal) + ",";
   json += "\"bb_upper\":" + Num(bb_upper) + ",\"bb_middle\":" + Num(bb_middle) + ",\"bb_lower\":" + Num(bb_lower) + ",";
   json += "\"adx\":" + Num(adx) + ",\"avg_tick_volume\":" + Num(avg_volume) + ",";
   json += "\"trend\":\"" + trend + "\",";
   json += "\"support\":[" + Num(local_low) + "," + Num(rates[1].low) + "],";
   json += "\"resistance\":[" + Num(local_high) + "," + Num(rates[1].high) + "]}";
   return true;
}

void ReleaseHandles()
{
   for(int i = 0; i < TF_COUNT; i++)
   {
      if(g_rsi[i] != INVALID_HANDLE) IndicatorRelease(g_rsi[i]);
      if(g_atr[i] != INVALID_HANDLE) IndicatorRelease(g_atr[i]);
      if(g_ema20[i] != INVALID_HANDLE) IndicatorRelease(g_ema20[i]);
      if(g_ema50[i] != INVALID_HANDLE) IndicatorRelease(g_ema50[i]);
      if(g_ema200[i] != INVALID_HANDLE) IndicatorRelease(g_ema200[i]);
      if(g_macd[i] != INVALID_HANDLE) IndicatorRelease(g_macd[i]);
      if(g_bands[i] != INVALID_HANDLE) IndicatorRelease(g_bands[i]);
      if(g_adx[i] != INVALID_HANDLE) IndicatorRelease(g_adx[i]);
   }
}

bool CreateHandles()
{
   for(int i = 0; i < TF_COUNT; i++)
   {
      g_rsi[i] = iRSI(InpSymbol, g_timeframes[i], 14, PRICE_CLOSE);
      g_atr[i] = iATR(InpSymbol, g_timeframes[i], 14);
      g_ema20[i] = iMA(InpSymbol, g_timeframes[i], 20, 0, MODE_EMA, PRICE_CLOSE);
      g_ema50[i] = iMA(InpSymbol, g_timeframes[i], 50, 0, MODE_EMA, PRICE_CLOSE);
      g_ema200[i] = iMA(InpSymbol, g_timeframes[i], 200, 0, MODE_EMA, PRICE_CLOSE);
      g_macd[i] = iMACD(InpSymbol, g_timeframes[i], 12, 26, 9, PRICE_CLOSE);
      g_bands[i] = iBands(InpSymbol, g_timeframes[i], 20, 0, 2.0, PRICE_CLOSE);
      g_adx[i] = iADX(InpSymbol, g_timeframes[i], 14);
      if(g_rsi[i] == INVALID_HANDLE || g_atr[i] == INVALID_HANDLE ||
         g_ema20[i] == INVALID_HANDLE || g_ema50[i] == INVALID_HANDLE ||
         g_ema200[i] == INVALID_HANDLE || g_macd[i] == INVALID_HANDLE ||
         g_bands[i] == INVALID_HANDLE || g_adx[i] == INVALID_HANDLE)
      {
         PrintFormat("MT5BRIDGE: failed to create handles for %s error=%d", g_names[i], GetLastError());
         return false;
      }
   }
   return true;
}

bool PublishSnapshot()
{
   MqlTick tick;
   if(!SymbolInfoTick(InpSymbol, tick) || tick.bid <= 0 || tick.ask <= 0)
   {
      PrintFormat("MT5BRIDGE: no valid tick for %s error=%d", InpSymbol, GetLastError());
      return false;
   }

   string frames = "";
   for(int i = 0; i < TF_COUNT; i++)
   {
      string frame;
      if(!FrameJson(i, frame))
         return false;
      if(i > 0)
         frames += ",";
      frames += frame;
   }

   double point = SymbolInfoDouble(InpSymbol, SYMBOL_POINT);
   long spread_points = point > 0 ? (long)MathRound((tick.ask - tick.bid) / point) : 0;
   string json = "{";
   json += "\"schema_version\":1,\"source\":\"MT5\",";
   json += "\"broker\":\"" + JsonEscape(AccountInfoString(ACCOUNT_SERVER)) + "\",";
   json += "\"symbol\":\"" + JsonEscape(InpSymbol) + "\",\"canonical_symbol\":\"XAUUSD\",";
   json += StringFormat("\"generated_at_msc\":%I64d,", (long)tick.time_msc);
   json += "\"tick\":{";
   json += StringFormat("\"time_msc\":%I64d,", (long)tick.time_msc);
   json += "\"bid\":" + Num(tick.bid) + ",\"ask\":" + Num(tick.ask) + ",\"last\":" + Num(tick.last) + ",";
   json += StringFormat("\"spread_points\":%I64d,\"digits\":%d,", spread_points, g_digits);
   json += "\"point\":" + DoubleToString(point, g_digits + 4) + "},";
   json += "\"timeframes\":{" + frames + "}}";

   string temp_file = InpOutputFile + ".tmp";
   int handle = FileOpen(temp_file, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_SHARE_READ, 0, CP_UTF8);
   if(handle == INVALID_HANDLE)
   {
      PrintFormat("MT5BRIDGE: FileOpen failed path=%s error=%d", temp_file, GetLastError());
      return false;
   }
   uint written = FileWriteString(handle, json);
   FileFlush(handle);
   FileClose(handle);
   if(written != StringLen(json))
   {
      PrintFormat("MT5BRIDGE: short write %u/%d", written, StringLen(json));
      FileDelete(temp_file);
      return false;
   }
   ResetLastError();
   if(!FileMove(temp_file, InpOutputFile, FILE_REWRITE))
   {
      PrintFormat("MT5BRIDGE: atomic rename failed temp=%s output=%s error=%d", temp_file, InpOutputFile, GetLastError());
      FileDelete(temp_file);
      return false;
   }
   return true;
}

int OnInit()
{
   if(InpPublishIntervalSeconds < 1 || InpHistoryBars < 25)
      return INIT_PARAMETERS_INCORRECT;
   if(!SymbolSelect(InpSymbol, true))
   {
      PrintFormat("MT5BRIDGE: SymbolSelect failed for %s error=%d", InpSymbol, GetLastError());
      return INIT_FAILED;
   }
   g_digits = (int)SymbolInfoInteger(InpSymbol, SYMBOL_DIGITS);
   if(!CreateHandles())
   {
      ReleaseHandles();
      return INIT_FAILED;
   }
   EventSetTimer(InpPublishIntervalSeconds);
   PrintFormat("MT5BRIDGE initialized v1.00 symbol=%s output=%s interval=%ds", InpSymbol, InpOutputFile, InpPublishIntervalSeconds);
   PublishSnapshot();
   return INIT_SUCCEEDED;
}

void OnTimer()
{
   PublishSnapshot();
}

int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   // Timer owns publication cadence; this indicator has no visual plot.
   return rates_total;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   ReleaseHandles();
   PrintFormat("MT5BRIDGE stopped reason=%d", reason);
}

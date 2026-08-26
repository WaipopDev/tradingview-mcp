#property strict
#property version   "1.003"
#property description "TradSignalOCOEA_V0.03 - autonomous EMA/RSI/ATR execution EA"
#include <Trade/Trade.mqh>

input ulong  Magic=26081701;
input double FixedLots=0.01;
input ENUM_TIMEFRAMES SignalTimeframe=PERIOD_M15;
input int    FastEMAPeriod=20;
input int    SlowEMAPeriod=50;
input int    RSIPeriod=14;
input double BuyRSIMin=55.0;
input double SellRSIMax=45.0;
input int    ATRPeriod=14;
input double ATRStopMultiplier=1.5;
input double RewardRisk=1.5;
input string AllowedSession="ALL"; // ALL or an exact signal session label such as Asia
input int    AsiaStartUtcHour=0;
input int    AsiaEndUtcHour=9;
input string AllowedSide="BOTH"; // BOTH, BUY, or SELL
input int    MaxSpreadPoints=80;
input int    MaxSlippagePoints=30;
input int    MaxSignalAgeMinutes=15;
input double DailyLossLimit=100.0;
input double MaxEquityDrawdownPercent=2.0;
input bool   EnableProtectiveOppositeStop=false; // V1 deliberately leaves OCO reversal disabled.


CTrade trade;
struct Signal
  {
   string id,side,session;
   datetime created,expiry;
   double entry,sl,tp1,tp2;
   int score;
  };

uint TextHash(const string value)
  {
   uint hash=2166136261;
   for(int i=0;i<StringLen(value);i++)
     {
      hash^=(uint)StringGetCharacter(value,i);
      hash*=16777619;
     }
   return hash;
  }
datetime BrokerNow()
  {
   datetime now=TimeTradeServer();
   return now>0 ? now : TimeCurrent();
  }
string Scope()
  {
   return StringFormat("TSO.%I64d.%08X.%08X.%I64d",
                       (long)AccountInfoInteger(ACCOUNT_LOGIN),
                       TextHash(AccountInfoString(ACCOUNT_SERVER)),
                       TextHash(_Symbol),(long)Magic);
  }
string Key(const string suffix) { return Scope()+"."+suffix; }
string DayKey() { return TimeToString(BrokerNow(),TIME_DATE); }
string LockKey() { return Key("lock."+DayKey()); }
string EquityKey() { return Key("equity."+DayKey()); }

bool PersistValue(const string key,const double value)
  {
   if(!GlobalVariableSet(key,value))
     {
      Print("GlobalVariableSet failed: ",key);
      return false;
     }
   GlobalVariablesFlush();
   return true;
  }

bool RetcodeOK(const string operation,const bool allow_placed=false)
  {
   uint code=trade.ResultRetcode();
   if(code==TRADE_RETCODE_DONE || (allow_placed && code==TRADE_RETCODE_PLACED))
      return true;
   Print(operation," rejected retcode=",code," comment=",trade.ResultRetcodeDescription());
   return false;
  }

bool FullCloseRetcodeOK()
  {
   uint code=trade.ResultRetcode();
   if(code==TRADE_RETCODE_DONE)
      return true;
   Print("PositionClose rejected retcode=",code," comment=",trade.ResultRetcodeDescription());
   return false;
  }

bool IsOwnedPosition(const ulong ticket)
  {
   if(!PositionSelectByTicket(ticket)) return false;
   return PositionGetString(POSITION_SYMBOL)==_Symbol && (ulong)PositionGetInteger(POSITION_MAGIC)==Magic;
  }
bool IsOwnedOrder(const ulong ticket)
  {
   if(!OrderSelect(ticket)) return false;
   return OrderGetString(ORDER_SYMBOL)==_Symbol && (ulong)OrderGetInteger(ORDER_MAGIC)==Magic;
  }
bool HasOwnedExposure()
  {
   for(int i=PositionsTotal()-1;i>=0;i--) if(IsOwnedPosition(PositionGetTicket(i))) return true;
   for(int i=OrdersTotal()-1;i>=0;i--) if(IsOwnedOrder(OrderGetTicket(i))) return true;
   return false;
  }
bool VerifyFlat()
  {
   bool flat=!HasOwnedExposure();
   if(!flat) Print("Full-close verification failed; lock stays active and cleanup retries.");
   return flat;
  }

void CleanupOwnedExposure()
  {
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      ulong ticket=OrderGetTicket(i);
      if(IsOwnedOrder(ticket) && (!trade.OrderDelete(ticket) || !RetcodeOK("OrderDelete")))
         Print("OrderDelete retry will occur on next timer/tick");
     }
   for(int i=PositionsTotal()-1;i>=0;i--)
     {
      ulong ticket=PositionGetTicket(i);
      if(IsOwnedPosition(ticket) &&
         (!trade.PositionClose(ticket) || !FullCloseRetcodeOK() || PositionSelectByTicket(ticket)))
         Print("PositionClose retry will occur on next timer/tick");
     }
   VerifyFlat();
  }


double RealizedToday()
  {
   MqlDateTime day; TimeToStruct(BrokerNow(),day);
   day.hour=0; day.min=0; day.sec=0;
   datetime start=StructToTime(day);
   if(!HistorySelect(start,BrokerNow())) return 0;
   double pnl=0;
   int total=HistoryDealsTotal();
   for(int i=0;i<total;i++)
     {
      ulong deal=HistoryDealGetTicket(i);
      if(HistoryDealGetString(deal,DEAL_SYMBOL)==_Symbol && (ulong)HistoryDealGetInteger(deal,DEAL_MAGIC)==Magic)
         pnl+=HistoryDealGetDouble(deal,DEAL_PROFIT)+HistoryDealGetDouble(deal,DEAL_SWAP)+HistoryDealGetDouble(deal,DEAL_COMMISSION);
     }
   return pnl;
  }

bool RiskLocked()
  {
   if(GlobalVariableCheck(LockKey()))
     {
      CleanupOwnedExposure();
      return true;
     }
   // A prior broker-day lock remains an emergency cleanup state only while
   // exposure survives rollover; it cannot be inherited by a new account/day.
   string prefix=Scope()+".lock.";
   for(int i=GlobalVariablesTotal()-1;i>=0;i--)
     {
      string old_key=GlobalVariableName(i);
      if(StringFind(old_key,prefix)!=0 || old_key==LockKey()) continue;
      if(HasOwnedExposure()) { CleanupOwnedExposure(); return true; }
      GlobalVariableDel(old_key);
      GlobalVariablesFlush();
     }
   if(!GlobalVariableCheck(EquityKey())) PersistValue(EquityKey(),AccountInfoDouble(ACCOUNT_EQUITY));
   double start_equity=GlobalVariableGet(EquityKey()), equity=AccountInfoDouble(ACCOUNT_EQUITY);
   bool breach=(DailyLossLimit>0 && RealizedToday()<=-DailyLossLimit) ||
               (MaxEquityDrawdownPercent>0 && equity<=start_equity*(1.0-MaxEquityDrawdownPercent/100.0));
   if(breach) PersistValue(LockKey(),1.0);
   if(GlobalVariableCheck(LockKey())) { CleanupOwnedExposure(); return true; }
   return false;
  }

bool SpreadOK()
  {
   MqlTick t; if(!SymbolInfoTick(_Symbol,t)) return false;
   return (t.ask-t.bid)/_Point<=MaxSpreadPoints;
  }

bool SessionGuard()
  {
   // ALL permits the full broker day; a named session uses the legacy Asia UTC window.
   if(AllowedSession=="ALL") return true;
   if(AllowedSession!="Asia") return false;
   MqlDateTime utc; TimeToStruct(BrokerNow(),utc);
   if(AsiaStartUtcHour<0 || AsiaStartUtcHour>23 || AsiaEndUtcHour<0 || AsiaEndUtcHour>23)
      return false;
   if(AsiaStartUtcHour==AsiaEndUtcHour) return false;
   if(AsiaStartUtcHour<AsiaEndUtcHour)
      return utc.hour>=AsiaStartUtcHour && utc.hour<AsiaEndUtcHour;
   return utc.hour>=AsiaStartUtcHour || utc.hour<AsiaEndUtcHour;
  }

bool ExecutionAccountAllowed()
  {
   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)==ACCOUNT_TRADE_MODE_REAL)
     {
      Print("Real account blocked: TradSignalOCOEA_V0.02 executes only in Strategy Tester or Demo.");
      return false;
     }
   return true;
  }

bool IsNewSignalBar()
  {
   static datetime last_bar=0;
   datetime bar=iTime(_Symbol,SignalTimeframe,0);
   if(bar<=0 || bar==last_bar) return false;
   last_bar=bar;
   return true;
  }
bool ReadBufferValue(const int handle,const int shift,double &value)
  {
   double values[]; return CopyBuffer(handle,0,shift,1,values)==1 && (value=values[0])>0;
  }
bool Submit(const string side,const double sl,const double tp)
  {
   trade.SetExpertMagicNumber(Magic); trade.SetDeviationInPoints(MaxSlippagePoints);
   bool sent=(side=="BUY") ? trade.Buy(FixedLots,_Symbol,0.0,sl,tp,"TSO_V003_BUY")
                            : trade.Sell(FixedLots,_Symbol,0.0,sl,tp,"TSO_V003_SELL");
   return sent && RetcodeOK("market entry");
  }
void Process()
  {
   if(!ExecutionAccountAllowed() || RiskLocked() || HasOwnedExposure() || !SpreadOK() || !SessionGuard() || !IsNewSignalBar()) return;
   int fast=iMA(_Symbol,SignalTimeframe,FastEMAPeriod,0,MODE_EMA,PRICE_CLOSE);
   int slow=iMA(_Symbol,SignalTimeframe,SlowEMAPeriod,0,MODE_EMA,PRICE_CLOSE);
   int rsi=iRSI(_Symbol,SignalTimeframe,RSIPeriod,PRICE_CLOSE);
   int atr=iATR(_Symbol,SignalTimeframe,ATRPeriod);
   double f,s,r,a; bool ok=ReadBufferValue(fast,1,f)&&ReadBufferValue(slow,1,s)&&ReadBufferValue(rsi,1,r)&&ReadBufferValue(atr,1,a);
   IndicatorRelease(fast); IndicatorRelease(slow); IndicatorRelease(rsi); IndicatorRelease(atr);
   if(!ok || a<=0 || RewardRisk<=0 || ATRStopMultiplier<=0) return;
   MqlTick t; if(!SymbolInfoTick(_Symbol,t)) return;
   double stop=a*ATRStopMultiplier;
   if((AllowedSide=="BOTH" || AllowedSide=="BUY") && f>s && r>=BuyRSIMin)
      Submit("BUY",NormalizeDouble(t.ask-stop,_Digits),NormalizeDouble(t.ask+stop*RewardRisk,_Digits));
   else if((AllowedSide=="BOTH" || AllowedSide=="SELL") && f<s && r<=SellRSIMax)
      Submit("SELL",NormalizeDouble(t.bid+stop,_Digits),NormalizeDouble(t.bid-stop*RewardRisk,_Digits));
  }
int OnInit() { trade.SetExpertMagicNumber(Magic); EventSetTimer(5); return INIT_SUCCEEDED; }
void OnDeinit(const int reason) { EventKillTimer(); }
void OnTick() { Process(); }
void OnTimer() { if(GlobalVariableCheck(LockKey())) CleanupOwnedExposure(); else Process(); }

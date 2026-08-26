#property strict
#property version   "1.002"
#property description "TradSignalOCOEA_V0.02 - fail-closed, single-signal MT5 execution EA"
#include <Trade/Trade.mqh>

input ulong  Magic=26081701;
input string SignalFile="trad_signal.csv";
input double FixedLots=0.01;
input int    MinScore=70;
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
string DuplicateKey(const string id) { return Key("Duplicate."+id); }
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

datetime ParseUtc(string iso)
  {
   StringReplace(iso,"T"," "); StringReplace(iso,"Z",""); StringReplace(iso,"-",".");
   datetime local=StringToTime(iso);
   if(local<=0) return 0;
   // StringToTime parses a terminal-local wall clock; normalize that wall clock to UTC.
   return local+(TimeLocal()-TimeGMT());
  }

bool ParseSignal(Signal &s)
  {
   int h=FileOpen(SignalFile,FILE_READ|FILE_TXT|FILE_ANSI);
   if(h==INVALID_HANDLE) { Print("Signal file unavailable: ",SignalFile); return false; }
   string header=FileReadString(h), row=FileReadString(h), extra=FileReadString(h); FileClose(h);
   StringTrimLeft(header); StringTrimRight(header); StringTrimLeft(row); StringTrimRight(row); StringTrimLeft(extra); StringTrimRight(extra);
   if(header!="signal_id,created_utc,side,entry,sl,tp1,tp2,score,session,expiry_utc" || row=="" || extra!="")
     { Print("Fail-closed CSV: require header plus exactly one row"); return false; }
   string f[]; if(StringSplit(row,',',f)!=10) { Print("Fail-closed CSV column count"); return false; }
   s.id=f[0]; s.created=ParseUtc(f[1]); s.side=f[2]; s.entry=StringToDouble(f[3]); s.sl=StringToDouble(f[4]);
   s.tp1=StringToDouble(f[5]); s.tp2=StringToDouble(f[6]); s.score=(int)StringToInteger(f[7]); s.session=f[8]; s.expiry=ParseUtc(f[9]);
   return s.id!="" && s.created>0 && s.expiry>0;
  }

bool ValidSignal(const Signal &s)
  {
   datetime now=TimeGMT();
   if((s.side!="BUY" && s.side!="SELL") ||
      (AllowedSide!="BOTH" && s.side!=AllowedSide)) return false;
   if((AllowedSession!="ALL" && s.session!=AllowedSession) || s.score<MinScore) return false;
   if(s.expiry<=s.created || s.expiry<=now || now-s.created>(MaxSignalAgeMinutes*60)) return false;
   if(GlobalVariableCheck(DuplicateKey(s.id))) { Print("Duplicate signal rejected: ",s.id); return false; }
   if(s.entry<=0 || s.sl<=0 || s.tp1<=0 || s.tp2<=0) return false;
   if(s.side=="SELL" && !(s.sl>s.entry && s.entry>s.tp1 && s.tp1>s.tp2)) return false;
   if(s.side=="BUY" && !(s.sl<s.entry && s.entry<s.tp1 && s.tp1<s.tp2)) return false;
   return true;
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

bool Submit(const Signal &s)
  {
   MqlTick t; if(!SymbolInfoTick(_Symbol,t)) return false;
   trade.SetExpertMagicNumber(Magic); trade.SetDeviationInPoints(MaxSlippagePoints);
   bool sent=false;
   if(s.side=="SELL") sent=(s.entry>=t.bid) ? trade.SellLimit(FixedLots,s.entry,_Symbol,s.sl,s.tp1,ORDER_TIME_SPECIFIED,s.expiry,s.id)
                                             : trade.SellStop(FixedLots,s.entry,_Symbol,s.sl,s.tp1,ORDER_TIME_SPECIFIED,s.expiry,s.id);
   else               sent=(s.entry<=t.ask) ? trade.BuyLimit(FixedLots,s.entry,_Symbol,s.sl,s.tp1,ORDER_TIME_SPECIFIED,s.expiry,s.id)
                                             : trade.BuyStop(FixedLots,s.entry,_Symbol,s.sl,s.tp1,ORDER_TIME_SPECIFIED,s.expiry,s.id);
   if(!sent || !RetcodeOK("primary pending order",true) || trade.ResultOrder()==0) return false;
   PersistValue(DuplicateKey(s.id),(double)s.expiry);
   return true;
  }

void Process()
  {
   if(!ExecutionAccountAllowed() || RiskLocked() || HasOwnedExposure() || !SpreadOK() || !SessionGuard()) return;
   Signal s; if(!ParseSignal(s) || !ValidSignal(s)) return;
   Submit(s);
  }
int OnInit() { trade.SetExpertMagicNumber(Magic); EventSetTimer(5); return INIT_SUCCEEDED; }
void OnDeinit(const int reason) { EventKillTimer(); }
void OnTick() { Process(); }
void OnTimer() { if(GlobalVariableCheck(LockKey())) CleanupOwnedExposure(); else Process(); }

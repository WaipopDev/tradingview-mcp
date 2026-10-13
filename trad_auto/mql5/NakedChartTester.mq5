#property strict
#property version "1.00"
// Fixed experiment; no safety bypass, live-chart support, or tuning parameters.
#include "NakedCore.mqh"
#include "CoreSelfTest.mqh"
// The risk budget is an input only because a fixed 1% cannot fund the minimum
// lot on a 100 USD account: 0.01 lots on GOLD risks about 1.00 USD per price
// unit of stop distance. Every other rule stays fixed and the MQL_TESTER guards
// remain non-configurable.
input double InpRiskPercent=1.0; // percent of current equity risked to the stop
datetime last_bar=0,seen_time[];
int seen_side[];
long evaluated=0,signals=0,risk_skipped=0,spread_skipped=0,margin_skipped=0;
long position_skipped=0,stop_skipped=0,data_skipped=0,orders=0,rejected=0;
int OnInit()
{
   if(!MQLInfoInteger(MQL_TESTER)) return INIT_FAILED;
   if(!RunCoreSelfTests()) return INIT_FAILED;
   if(_Symbol!="GOLD" || _Period!=PERIOD_M5) return INIT_PARAMETERS_INCORRECT;
   if(AccountInfoString(ACCOUNT_CURRENCY)!="USD" || AccountInfoInteger(ACCOUNT_LEVERAGE)!=1000) return INIT_PARAMETERS_INCORRECT;
   if(MathAbs(AccountInfoDouble(ACCOUNT_BALANCE)-100.0)>0.001) return INIT_PARAMETERS_INCORRECT;
   if(!MathIsValidNumber(InpRiskPercent)||InpRiskPercent<0.1||InpRiskPercent>10.0) return INIT_PARAMETERS_INCORRECT;
   PrintFormat("TESTER_ONLY fixed GOLD M5/H1 pivot=2 retest=4 RR=1 risk=%.2f%% max_spread=1.0 bars=260",InpRiskPercent);
   return INIT_SUCCEEDED;
}
bool SendTestOrder(MqlTradeRequest &request,MqlTradeResult &result)
{
   if(!MQLInfoInteger(MQL_TESTER)) return false;
   return OrderSend(request,result);
}
bool SeenBos(int side,datetime bos)
{
   int n=ArraySize(seen_time);
   for(int i=0;i<n;i++) if(seen_time[i]==bos&&seen_side[i]==side) return true;
   ArrayResize(seen_time,n+1);ArrayResize(seen_side,n+1);
   seen_time[n]=bos;seen_side[n]=side;
   return false;
}
void OnTick()
{
   if(!MQLInfoInteger(MQL_TESTER)) return;
   datetime current=iTime(_Symbol,PERIOD_M5,0);
   if(current<=0||current==last_bar) return;
   last_bar=current;
   MqlRates bars[],higher[];
   ArraySetAsSeries(bars,false);ArraySetAsSeries(higher,false);
   int n=CopyRates(_Symbol,PERIOD_M5,1,260,bars);
   int hn=CopyRates(_Symbol,PERIOD_H1,1,260,higher);
   if(n<10||hn<10) {data_skipped++;return;}
   datetime asof=bars[n-1].time+300;
   if(!ValidBars(bars,300,TimeCurrent()) || !ValidBars(higher,3600,asof)) {data_skipped++;return;}
   // Shift 1 excludes forming bars; H1 close must also precede M5 asof.
   double hi,lo;int htrend=Structure(higher,hn,2,hi,lo);
   Setup s;evaluated++;
   if(!FindSetup(bars,htrend,s)||SeenBos(s.side,s.bos_time)) return;
   signals++;
   if(PositionsTotal()>0) {position_skipped++;return;}
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick)||tick.bid<=0||tick.ask<tick.bid||TimeCurrent()<tick.time||TimeCurrent()-tick.time>120) {data_skipped++;return;}
   if(tick.ask-tick.bid>1.0) {spread_skipped++;return;}
   double tick_size=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
   double point=SymbolInfoDouble(_Symbol,SYMBOL_POINT);
   int digits=(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS);
   if(tick_size<=0||point<=0) {data_skipped++;return;}
   double quote=s.side==1?tick.ask:tick.bid;
   double entry=NormalizeDouble(MathRound(quote/tick_size)*tick_size,digits);
   if(MathAbs(entry-quote)>tick_size*1e-6) {stop_skipped++;return;}
   double stop=NormalizeDouble((s.side==1?MathFloor(s.stop/tick_size):MathCeil(s.stop/tick_size))*tick_size,digits);
   double distance=s.side*(entry-stop);
   double target=NormalizeDouble(2*entry-stop,digits);
   double minimum_stop=SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL)*point;
   bool valid=s.side==1?(tick.bid-stop>=minimum_stop&&target-tick.bid>=minimum_stop):(stop-tick.ask>=minimum_stop&&tick.ask-target>=minimum_stop);
   if(distance<=0||target<=0||!valid||MathAbs(MathAbs(target-entry)-distance)>tick_size*1e-6) {stop_skipped++;return;}
   ENUM_ORDER_TYPE type=s.side==1?ORDER_TYPE_BUY:ORDER_TYPE_SELL;
   double pnl=0;
   double minimum=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   double maximum=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   if(minimum<=0||!OrderCalcProfit(type,_Symbol,minimum,entry,stop,pnl)||pnl>=0) {risk_skipped++;return;}
   double budget=AccountInfoDouble(ACCOUNT_EQUITY)*InpRiskPercent/100.0;
   double volume=FloorVolume(budget,-pnl/minimum,step,minimum,maximum);
   if(volume<=0||!OrderCalcProfit(type,_Symbol,volume,entry,stop,pnl)||pnl>=0||-pnl>budget+1e-9) {risk_skipped++;PrintFormat("RISK_SKIP side=%d distance=%.2f min_lot_risk=%.2f budget=%.2f",s.side,distance,-pnl,budget);return;}
   double margin=0;
   if(!OrderCalcMargin(type,_Symbol,volume,entry,margin)||margin>AccountInfoDouble(ACCOUNT_MARGIN_FREE)) {margin_skipped++;return;}
   MqlTradeRequest request={};MqlTradeResult result={};MqlTradeCheckResult check={};
   request.action=TRADE_ACTION_DEAL;request.symbol=_Symbol;request.type=type;
   request.volume=volume;request.price=entry;request.sl=stop;request.tp=target;
   request.deviation=0;request.magic=20260911;request.comment="tester-only fixed 1pct RR1";
   long filling=SymbolInfoInteger(_Symbol,SYMBOL_FILLING_MODE);
   if((filling&SYMBOL_FILLING_FOK)!=0) request.type_filling=ORDER_FILLING_FOK;
   else if((filling&SYMBOL_FILLING_IOC)!=0) request.type_filling=ORDER_FILLING_IOC;
   else if(SymbolInfoInteger(_Symbol,SYMBOL_TRADE_EXEMODE)!=SYMBOL_TRADE_EXECUTION_MARKET) request.type_filling=ORDER_FILLING_RETURN;
   else {rejected++;return;}
   request.type_time=ORDER_TIME_GTC;
   if(!OrderCheck(request,check)) {rejected++;Print("CHECK_REJECT retcode=",check.retcode);return;}
   if(!SendTestOrder(request,result)||(result.retcode!=TRADE_RETCODE_DONE&&result.retcode!=TRADE_RETCODE_DONE_PARTIAL)) {rejected++;Print("SEND_REJECT retcode=",result.retcode);return;}
   orders++;
   PrintFormat("TEST_FILL side=%d requested=%.8f actual=%.8f sl=%.8f tp=%.8f volume=%.8f planned_stop_risk=%.8f",s.side,entry,result.price,stop,target,volume,-pnl);
}
double OnTester()
{
   if(!MQLInfoInteger(MQL_TESTER)) return 0;
   double commission=0,swap=0,fee=0;
   if(HistorySelect(0,TimeCurrent())) for(int i=0;i<HistoryDealsTotal();i++) {
      ulong deal=HistoryDealGetTicket(i);
      commission+=HistoryDealGetDouble(deal,DEAL_COMMISSION);
      swap+=HistoryDealGetDouble(deal,DEAL_SWAP);
      fee+=HistoryDealGetDouble(deal,DEAL_FEE);
   }
   double trades=TesterStatistics(STAT_TRADES),profit=TesterStatistics(STAT_PROFIT);
   string json=StringFormat("{\"evaluated\":%I64d,\"signals\":%I64d,\"risk_skipped\":%I64d,\"spread_skipped\":%I64d,\"margin_skipped\":%I64d,\"position_skipped\":%I64d,\"stop_skipped\":%I64d,\"data_skipped\":%I64d,\"orders\":%I64d,\"rejected\":%I64d,\"trades\":%.0f,\"net_profit\":%.8f,\"ending_balance\":%.8f,\"profit_factor\":%.8g,\"max_equity_dd\":%.8f,\"max_equity_dd_percent\":%.8f,\"winrate_percent\":%.8f,\"commission\":%.8f,\"swap\":%.8f,\"fee\":%.8f}",evaluated,signals,risk_skipped,spread_skipped,margin_skipped,position_skipped,stop_skipped,data_skipped,orders,rejected,trades,profit,TesterStatistics(STAT_INITIAL_DEPOSIT)+profit,TesterStatistics(STAT_PROFIT_FACTOR),TesterStatistics(STAT_EQUITY_DD),TesterStatistics(STAT_EQUITY_DDREL_PERCENT),trades>0?100*TesterStatistics(STAT_PROFIT_TRADES)/trades:0,commission,swap,fee);
   Print("TESTER_SUMMARY ",json);
   int file=FileOpen("NakedChartTester-summary.json",FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(file!=INVALID_HANDLE) {FileWriteString(file,json);FileClose(file);}
   return profit;
}

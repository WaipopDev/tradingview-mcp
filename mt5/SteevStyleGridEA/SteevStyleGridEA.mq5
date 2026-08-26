//+------------------------------------------------------------------+
//| SteevStyleGridEA.mq5                                             |
//| Symmetric BUY STOP / SELL STOP grid with OCO and risk controls   |
//| Shadow/demo validation first. No martingale.                     |
//+------------------------------------------------------------------+
#property copyright "WaipopDev"
#property version   "1.00"
#property strict
#property description "Pending-order breakout grid for MT5 with OCO, basket limits, BE, partial and trailing management."

#include <Trade/Trade.mqh>

enum ENUM_GRID_MODE
  {
   GRID_OCO = 0,       // First side triggered -> delete opposite pending side
   GRID_HEDGE = 1      // Keep both pending sides until another safety rule removes them
  };

input group "Grid"
input ENUM_GRID_MODE InpGridMode              = GRID_OCO;
input double         InpFixedLot              = 0.01;
input int            InpLevelsPerSide         = 5;
input int            InpInitialOffsetPoints   = 300;
input int            InpGridSpacingPoints     = 300;
input int            InpPendingExpiryHours    = 4;
input int            InpRecenterDistancePoints= 900;
input int            InpCooldownMinutes       = 15;

input group "Per-order protection"
input int            InpStopLossPoints        = 700;
input int            InpTakeProfitPoints      = 1200;
input int            InpBreakEvenTriggerPoints= 350;
input int            InpBreakEvenLockPoints   = 30;
input bool           InpEnablePartialClose    = true;
input int            InpPartialTriggerPoints  = 500;
input double         InpPartialClosePercent   = 50.0;
input int            InpTrailingStartPoints   = 700;
input int            InpTrailingDistancePoints= 350;

input group "Account and basket safety"
input int            InpMaxOpenPositions      = 10;
input double         InpMaxOpenLots           = 0.10;
input double         InpMaxPendingLots        = 0.10;
input double         InpBasketTakeProfitMoney = 20.0;
input double         InpBasketStopLossMoney   = 30.0;
input double         InpMaxDailyLossPercent   = 2.0;
input double         InpMaxEquityDrawdownPct  = 5.0;

input group "Execution filters"
input int            InpMaxSpreadPoints       = 80;
input int            InpMaxSlippagePoints     = 30;
input int            InpSessionStartHour      = 0;
input int            InpSessionEndHour        = 24;
input bool           InpCancelPendingsOutsideSession = true;
input bool           InpCancelPendingsOnRemove       = false;

input group "Identity"
input long           InpMagic                 = 26080601;
input string         InpOrderPrefix           = "SGRID";

CTrade   trade;
double   g_anchor_price       = 0.0;
double   g_start_equity       = 0.0;
double   g_day_start_balance  = 0.0;
int      g_day_key            = -1;
datetime g_last_flat_time     = 0;
bool     g_risk_lock          = false;
int      g_previous_positions = 0;
int      g_previous_pendings  = 0;
bool     g_cycle_active       = false;
bool     g_exit_seen          = false;

//+------------------------------------------------------------------+
int OnInit()
  {
   if(!ValidateInputs())
      return(INIT_PARAMETERS_INCORRECT);

   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(InpMaxSlippagePoints);
   trade.SetTypeFillingBySymbol(_Symbol);
   trade.SetAsyncMode(false);

   ResetDailyBaseline(true);
   g_previous_positions=CountOurPositions();
   g_previous_pendings=CountOurPendings();
   g_cycle_active=(g_previous_positions>0);
   if(g_previous_positions==0 && g_previous_pendings>0)
     {
      g_last_flat_time=TimeCurrent();
      CancelAllPendings("restart orphan-safety reset");
      g_previous_pendings=CountOurPendings();
     }
   EventSetTimer(5);

   PrintFormat("%s initialized on %s. Mode=%s, levels=%d, lot=%.2f",
               InpOrderPrefix,_Symbol,(InpGridMode==GRID_OCO ? "OCO" : "HEDGE"),
               InpLevelsPerSide,InpFixedLot);
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   EventKillTimer();
   if(InpCancelPendingsOnRemove)
      CancelAllPendings("EA removed");
  }

//+------------------------------------------------------------------+
void OnTick()
  {
   ResetDailyBaseline(false);
   ManageRiskAndPositions();
   MaintainGrid();
  }

//+------------------------------------------------------------------+
void OnTimer()
  {
   ResetDailyBaseline(false);
   ManageRiskAndPositions();
   MaintainGrid();
  }

//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
  {
   if(trans.type!=TRADE_TRANSACTION_DEAL_ADD || trans.deal==0)
      return;
   if(!HistoryDealSelect(trans.deal))
      return;
   if((long)HistoryDealGetInteger(trans.deal,DEAL_MAGIC)!=InpMagic)
      return;
   if(HistoryDealGetString(trans.deal,DEAL_SYMBOL)!=_Symbol)
      return;
   ENUM_DEAL_ENTRY deal_entry=(ENUM_DEAL_ENTRY)HistoryDealGetInteger(trans.deal,DEAL_ENTRY);
   ENUM_DEAL_TYPE deal_type=(ENUM_DEAL_TYPE)HistoryDealGetInteger(trans.deal,DEAL_TYPE);
   bool is_entry=(deal_entry==DEAL_ENTRY_IN || deal_entry==DEAL_ENTRY_INOUT);
   bool is_exit=(deal_entry==DEAL_ENTRY_OUT || deal_entry==DEAL_ENTRY_OUT_BY ||
                 deal_entry==DEAL_ENTRY_INOUT);
   if(is_entry)
      g_cycle_active=true;
   if(is_exit)
      g_exit_seen=true;

   if(is_entry && InpGridMode==GRID_OCO)
     {
      if(deal_type==DEAL_TYPE_BUY)
         CancelPendingType(ORDER_TYPE_SELL_STOP,"OCO BUY activated");
      else if(deal_type==DEAL_TYPE_SELL)
         CancelPendingType(ORDER_TYPE_BUY_STOP,"OCO SELL activated");
     }
  }

//+------------------------------------------------------------------+
bool ValidateInputs()
  {
   if(InpFixedLot<=0.0 || InpLevelsPerSide<1 || InpGridSpacingPoints<1)
     {
      Print("Invalid lot, levels, or spacing input.");
      return(false);
     }
   if(InpStopLossPoints<=0 || InpTakeProfitPoints<=0)
     {
      Print("SL and TP points must be positive.");
      return(false);
     }
   if(InpMaxOpenPositions<1 || InpMaxOpenLots<=0.0 || InpMaxPendingLots<=0.0)
     {
      Print("Position and lot safety limits must be positive.");
      return(false);
     }
   if(InpPartialClosePercent<=0.0 || InpPartialClosePercent>=100.0)
     {
      Print("Partial close percent must be between 0 and 100.");
      return(false);
     }
   if(InpSessionStartHour<0 || InpSessionStartHour>23 || InpSessionEndHour<1 || InpSessionEndHour>24)
     {
      Print("Session hours are invalid.");
      return(false);
     }
   double lot=NormalizeVolume(InpFixedLot);
   int potential_orders=InpLevelsPerSide*2;
   double potential_lots=lot*potential_orders;
   if(potential_lots>InpMaxPendingLots+1e-8 || potential_lots>InpMaxOpenLots+1e-8)
     {
      PrintFormat("Unsafe grid: potential lots %.2f exceed pending/open cap.",potential_lots);
      return(false);
     }
   ENUM_ACCOUNT_MARGIN_MODE margin_mode=(ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE);
   if(margin_mode==ACCOUNT_MARGIN_MODE_RETAIL_HEDGING && potential_orders>InpMaxOpenPositions)
     {
      PrintFormat("Unsafe grid: %d potential positions exceed hard cap %d.",
                  potential_orders,InpMaxOpenPositions);
      return(false);
     }
   return(true);
  }

//+------------------------------------------------------------------+
void ResetDailyBaseline(const bool force)
  {
   MqlDateTime now;
   TimeToStruct(TimeCurrent(),now);
   int key=now.year*10000+now.mon*100+now.day;
   if(!force && key==g_day_key)
      return;

   string day_key=RiskKey("day");
   string balance_key=RiskKey("balance");
   string equity_key=RiskKey("equity");
   string lock_key=RiskKey("lock");
   bool same_day=(GlobalVariableCheck(day_key) &&
                  (int)GlobalVariableGet(day_key)==key &&
                  GlobalVariableCheck(balance_key) &&
                  GlobalVariableCheck(equity_key));
   bool stored_lock=(GlobalVariableCheck(lock_key) && GlobalVariableGet(lock_key)>0.5);
   bool owned_exposure=(CountOurPositions()>0 || CountOurPendings()>0);

   // A broker-day rollover must never unlock residual exposure from a prior
   // emergency. Keep the old lock/baseline until liquidation is verified.
   if(!same_day && (g_risk_lock || stored_lock) && owned_exposure)
     {
      bool newly_restored=!g_risk_lock;
      g_risk_lock=true;
      if(GlobalVariableCheck(balance_key))
         g_day_start_balance=GlobalVariableGet(balance_key);
      if(GlobalVariableCheck(equity_key))
         g_start_equity=GlobalVariableGet(equity_key);
      if(GlobalVariableCheck(day_key))
         g_day_key=(int)GlobalVariableGet(day_key);
      if(newly_restored)
         Print("Risk lock carried across broker-day rollover until exposure is zero.");
      return;
     }

   g_day_key=key;
   if(same_day)
     {
      g_day_start_balance=GlobalVariableGet(balance_key);
      g_start_equity=GlobalVariableGet(equity_key);
      g_risk_lock=(GlobalVariableCheck(lock_key) && GlobalVariableGet(lock_key)>0.5);
      PrintFormat("Daily baseline restored: balance=%.2f equity=%.2f lock=%s",
                  g_day_start_balance,g_start_equity,(g_risk_lock ? "ON" : "OFF"));
      return;
     }

   g_day_start_balance=AccountInfoDouble(ACCOUNT_BALANCE);
   g_start_equity=AccountInfoDouble(ACCOUNT_EQUITY);
   g_risk_lock=false;
   GlobalVariableSet(day_key,(double)key);
   GlobalVariableSet(balance_key,g_day_start_balance);
   GlobalVariableSet(equity_key,g_start_equity);
   GlobalVariableSet(lock_key,0.0);
   GlobalVariablesFlush();
   PrintFormat("Daily baseline reset: balance=%.2f equity=%.2f",
               g_day_start_balance,g_start_equity);
  }

//+------------------------------------------------------------------+
bool IsSessionOpen()
  {
   MqlDateTime now;
   TimeToStruct(TimeCurrent(),now);
   if(InpSessionStartHour==0 && InpSessionEndHour==24)
      return(true);
   if(InpSessionStartHour<InpSessionEndHour)
      return(now.hour>=InpSessionStartHour && now.hour<InpSessionEndHour);
   return(now.hour>=InpSessionStartHour || now.hour<InpSessionEndHour);
  }

//+------------------------------------------------------------------+
double CurrentSpreadPoints()
  {
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick))
      return(DBL_MAX);
   return((tick.ask-tick.bid)/_Point);
  }

//+------------------------------------------------------------------+
void MaintainGrid()
  {
   int positions=CountOurPositions();
   int pendings=CountOurPendings();

   if(InpGridMode==GRID_OCO && positions>0)
     {
      bool has_buy=HasPositionType(POSITION_TYPE_BUY);
      bool has_sell=HasPositionType(POSITION_TYPE_SELL);
      if(has_buy && has_sell)
         CancelAllPendings("OCO reconciliation: both sides already active");
      else if(has_buy)
         CancelPendingType(ORDER_TYPE_SELL_STOP,"OCO reconciliation BUY");
      else if(has_sell)
         CancelPendingType(ORDER_TYPE_BUY_STOP,"OCO reconciliation SELL");
      pendings=CountOurPendings();
     }

   if(positions>0)
      g_cycle_active=true;
   bool became_flat=(positions==0 &&
                     (g_previous_positions>0 || (g_cycle_active && g_exit_seen)));
   bool pending_cycle_ended=(positions==0 && pendings==0 && g_previous_pendings>0);
   if(became_flat)
     {
      CancelAllPendings("flat-cycle cleanup");
      pendings=CountOurPendings();
      g_last_flat_time=TimeCurrent();
      g_cycle_active=false;
      g_exit_seen=false;
     }
   else if(pending_cycle_ended)
      g_last_flat_time=TimeCurrent();
   else if(g_exit_seen && positions>0)
      g_exit_seen=false;

   if(positions==0 && pendings>0 && g_last_flat_time>0 &&
      TimeCurrent()-g_last_flat_time<InpCooldownMinutes*60)
     {
      CancelAllPendings("cooldown cleanup retry");
      pendings=CountOurPendings();
     }

   g_previous_positions=positions;
   g_previous_pendings=pendings;

   if(g_risk_lock)
     {
      if(pendings>0)
         CancelAllPendings("risk lock");
      return;
     }

   if(!IsSessionOpen())
     {
      if(InpCancelPendingsOutsideSession && pendings>0)
         CancelAllPendings("outside session");
      return;
     }

   if(CurrentSpreadPoints()>InpMaxSpreadPoints)
      return;

   double open_lots=OurOpenLots();
   if(positions>=InpMaxOpenPositions || open_lots>=InpMaxOpenLots-1e-8)
     {
      if(pendings>0)
         CancelAllPendings("position cap");
      return;
     }

   if(positions==0 && pendings==0)
     {
      if(g_last_flat_time>0 && TimeCurrent()-g_last_flat_time<InpCooldownMinutes*60)
         return;
      PlaceFreshGrid();
      return;
     }

   if(positions==0 && pendings>0 && InpRecenterDistancePoints>0)
     {
      MqlTick tick;
      if(SymbolInfoTick(_Symbol,tick))
        {
         double midpoint=(tick.ask+tick.bid)/2.0;
         if(g_anchor_price>0.0 && MathAbs(midpoint-g_anchor_price)/_Point>=InpRecenterDistancePoints)
           {
            CancelAllPendings("recenter");
            PlaceFreshGrid();
           }
        }
     }
  }

//+------------------------------------------------------------------+
bool PlaceFreshGrid()
  {
   if(CountOurPositions()>0 || CountOurPendings()>0)
      return(false);

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick))
      return(false);

   double lot=NormalizeVolume(InpFixedLot);
   double requested=lot*InpLevelsPerSide*2.0;
   if(requested>InpMaxPendingLots+1e-8)
     {
      PrintFormat("Grid rejected: requested pending lots %.2f exceeds cap %.2f",
                  requested,InpMaxPendingLots);
      return(false);
     }

   int stops_level=(int)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   int offset=MathMax(InpInitialOffsetPoints,stops_level+1);
   ENUM_ORDER_TYPE_TIME time_type=(InpPendingExpiryHours>0 ? ORDER_TIME_SPECIFIED : ORDER_TIME_GTC);
   datetime expiration=(InpPendingExpiryHours>0 ? TimeCurrent()+InpPendingExpiryHours*3600 : 0);
   int buy_ok=0;
   int sell_ok=0;

   g_anchor_price=(tick.ask+tick.bid)/2.0;

   for(int level=0; level<InpLevelsPerSide; level++)
     {
      int distance=offset+level*InpGridSpacingPoints;
      double buy_price=NormalizePrice(tick.ask+distance*_Point);
      double buy_sl=NormalizePrice(buy_price-InpStopLossPoints*_Point);
      double buy_tp=NormalizePrice(buy_price+InpTakeProfitPoints*_Point);
      string buy_comment=StringFormat("%s:B:%02d",InpOrderPrefix,level+1);

      bool buy_sent=trade.BuyStop(lot,buy_price,_Symbol,buy_sl,buy_tp,time_type,expiration,buy_comment);
      if(TradeResultAccepted(buy_sent,true,false,false) && trade.ResultOrder()>0)
         buy_ok++;
      else
         PrintTradeFailure("BuyStop",level+1);

      double sell_price=NormalizePrice(tick.bid-distance*_Point);
      double sell_sl=NormalizePrice(sell_price+InpStopLossPoints*_Point);
      double sell_tp=NormalizePrice(sell_price-InpTakeProfitPoints*_Point);
      string sell_comment=StringFormat("%s:S:%02d",InpOrderPrefix,level+1);

      bool sell_sent=trade.SellStop(lot,sell_price,_Symbol,sell_sl,sell_tp,time_type,expiration,sell_comment);
      if(TradeResultAccepted(sell_sent,true,false,false) && trade.ResultOrder()>0)
         sell_ok++;
      else
         PrintTradeFailure("SellStop",level+1);
     }

   if(buy_ok!=InpLevelsPerSide || sell_ok!=InpLevelsPerSide)
     {
      PrintFormat("Incomplete grid rejected: BUY STOP=%d/%d, SELL STOP=%d/%d",
                  buy_ok,InpLevelsPerSide,sell_ok,InpLevelsPerSide);
      CancelAllPendings("incomplete grid rollback");
      g_anchor_price=0.0;
      return(false);
     }

   PrintFormat("Grid placed at anchor %.5f: BUY STOP=%d, SELL STOP=%d",
               g_anchor_price,buy_ok,sell_ok);
   return(true);
  }

//+------------------------------------------------------------------+
void ManageRiskAndPositions()
  {
   if(g_risk_lock)
     {
      CancelAllPendings("persistent risk-lock enforcement");
      CloseAllPositions("persistent risk-lock enforcement");
      return;
     }

   double basket=OurFloatingProfit();
   int positions=CountOurPositions();

   if(positions>0 && InpBasketTakeProfitMoney>0.0 && basket>=InpBasketTakeProfitMoney)
     {
      CloseAllPositions("basket TP");
      CancelAllPendings("basket TP");
      g_last_flat_time=TimeCurrent();
      return;
     }

   if(positions>0 && InpBasketStopLossMoney>0.0 && basket<=-InpBasketStopLossMoney)
     {
      CloseAllPositions("basket SL");
      CancelAllPendings("basket SL");
      g_last_flat_time=TimeCurrent();
      SetRiskLock(true);
      return;
     }

   double equity=AccountInfoDouble(ACCOUNT_EQUITY);
   if(InpMaxEquityDrawdownPct>0.0 && g_start_equity>0.0)
     {
      double dd=(g_start_equity-equity)/g_start_equity*100.0;
      if(dd>=InpMaxEquityDrawdownPct)
        {
         EmergencyStop(StringFormat("equity DD %.2f%%",dd));
         return;
        }
     }

   if(InpMaxDailyLossPercent>0.0 && g_day_start_balance>0.0)
     {
      double daily_loss=(g_day_start_balance-equity)/g_day_start_balance*100.0;
      if(daily_loss>=InpMaxDailyLossPercent)
        {
         EmergencyStop(StringFormat("daily loss %.2f%%",daily_loss));
         return;
        }
     }

   if(positions>=InpMaxOpenPositions || OurOpenLots()>=InpMaxOpenLots-1e-8)
      CancelAllPendings("max exposure reached");

   ManageBreakEvenPartialAndTrail();
  }

//+------------------------------------------------------------------+
void ManageBreakEvenPartialAndTrail()
  {
   for(int i=PositionsTotal()-1; i>=0; i--)
     {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol)
         continue;
      if((long)PositionGetInteger(POSITION_MAGIC)!=InpMagic)
         continue;

      ENUM_POSITION_TYPE type=(ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      double open=PositionGetDouble(POSITION_PRICE_OPEN);
      double current=(type==POSITION_TYPE_BUY ? SymbolInfoDouble(_Symbol,SYMBOL_BID)
                                               : SymbolInfoDouble(_Symbol,SYMBOL_ASK));
      double old_sl=PositionGetDouble(POSITION_SL);
      double tp=PositionGetDouble(POSITION_TP);
      double profit_points=(type==POSITION_TYPE_BUY ? (current-open) : (open-current))/_Point;

      if(InpEnablePartialClose && profit_points>=InpPartialTriggerPoints)
         TryPartialClose(ticket);

      double candidate_sl=old_sl;
      bool modify=false;

      if(profit_points>=InpBreakEvenTriggerPoints)
        {
         double be=(type==POSITION_TYPE_BUY ? open+InpBreakEvenLockPoints*_Point
                                            : open-InpBreakEvenLockPoints*_Point);
         if(IsBetterStop(type,be,candidate_sl))
           {
            candidate_sl=be;
            modify=true;
           }
        }

      if(profit_points>=InpTrailingStartPoints)
        {
         double trail=(type==POSITION_TYPE_BUY ? current-InpTrailingDistancePoints*_Point
                                               : current+InpTrailingDistancePoints*_Point);
         if(IsBetterStop(type,trail,candidate_sl))
           {
            candidate_sl=trail;
            modify=true;
           }
        }

      if(modify)
        {
         candidate_sl=NormalizePrice(candidate_sl);
         bool modify_sent=trade.PositionModify(ticket,candidate_sl,tp);
         if(!TradeResultAccepted(modify_sent,false,false,true))
            PrintTradeFailure("PositionModify",(int)ticket);
        }
     }
  }

//+------------------------------------------------------------------+
void TryPartialClose(const ulong ticket)
  {
   string key=PartialKey(ticket);
   if(GlobalVariableCheck(key))
      return;
   if(!PositionSelectByTicket(ticket))
      return;

   ENUM_ACCOUNT_MARGIN_MODE margin_mode=(ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE);
   if(margin_mode!=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
     {
      GlobalVariableSet(key,(double)TimeCurrent());
      Print("Partial close skipped: account is not hedging mode.");
      return;
     }

   double volume=PositionGetDouble(POSITION_VOLUME);
   double min_volume=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double close_volume=NormalizeVolume(volume*InpPartialClosePercent/100.0);
   if(close_volume<min_volume || volume-close_volume<min_volume-1e-8)
     {
      GlobalVariableSet(key,(double)TimeCurrent());
      return;
     }

   bool partial_sent=trade.PositionClosePartial(ticket,close_volume,InpMaxSlippagePoints);
   if(TradeResultAccepted(partial_sent,false,true,false))
     {
      GlobalVariableSet(key,(double)TimeCurrent());
      PrintFormat("Partial close ticket=%I64u volume=%.2f",ticket,close_volume);
     }
   else
      PrintTradeFailure("PositionClosePartial",(int)ticket);
  }

//+------------------------------------------------------------------+
bool IsBetterStop(const ENUM_POSITION_TYPE type,const double candidate,const double current_sl)
  {
   if(type==POSITION_TYPE_BUY)
      return(current_sl==0.0 || candidate>current_sl+_Point);
   return(current_sl==0.0 || candidate<current_sl-_Point);
  }

//+------------------------------------------------------------------+
void EmergencyStop(const string reason)
  {
   if(!g_risk_lock)
      Print("EMERGENCY STOP: ",reason);
   SetRiskLock(true);
   CancelAllPendings(reason);
   CloseAllPositions(reason);
   g_last_flat_time=TimeCurrent();
  }

//+------------------------------------------------------------------+
int CountOurPositions()
  {
   int count=0;
   for(int i=PositionsTotal()-1; i>=0; i--)
     {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL)==_Symbol &&
         (long)PositionGetInteger(POSITION_MAGIC)==InpMagic)
         count++;
     }
   return(count);
  }

//+------------------------------------------------------------------+
bool HasPositionType(const ENUM_POSITION_TYPE wanted)
  {
   for(int i=PositionsTotal()-1; i>=0; i--)
     {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL)==_Symbol &&
         (long)PositionGetInteger(POSITION_MAGIC)==InpMagic &&
         (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE)==wanted)
         return(true);
     }
   return(false);
  }

//+------------------------------------------------------------------+
double OurOpenLots()
  {
   double lots=0.0;
   for(int i=PositionsTotal()-1; i>=0; i--)
     {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL)==_Symbol &&
         (long)PositionGetInteger(POSITION_MAGIC)==InpMagic)
         lots+=PositionGetDouble(POSITION_VOLUME);
     }
   return(lots);
  }

//+------------------------------------------------------------------+
double OurFloatingProfit()
  {
   double value=0.0;
   for(int i=PositionsTotal()-1; i>=0; i--)
     {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL)==_Symbol &&
         (long)PositionGetInteger(POSITION_MAGIC)==InpMagic)
         value+=PositionGetDouble(POSITION_PROFIT)+PositionGetDouble(POSITION_SWAP);
     }
   return(value);
  }

//+------------------------------------------------------------------+
int CountOurPendings()
  {
   int count=0;
   for(int i=OrdersTotal()-1; i>=0; i--)
     {
      ulong ticket=OrderGetTicket(i);
      if(ticket==0)
         continue;
      if(OrderGetString(ORDER_SYMBOL)==_Symbol &&
         (long)OrderGetInteger(ORDER_MAGIC)==InpMagic)
         count++;
     }
   return(count);
  }

//+------------------------------------------------------------------+
void CancelPendingType(const ENUM_ORDER_TYPE wanted,const string reason)
  {
   for(int i=OrdersTotal()-1; i>=0; i--)
     {
      ulong ticket=OrderGetTicket(i);
      if(ticket==0)
         continue;
      if(OrderGetString(ORDER_SYMBOL)!=_Symbol ||
         (long)OrderGetInteger(ORDER_MAGIC)!=InpMagic)
         continue;
      if((ENUM_ORDER_TYPE)OrderGetInteger(ORDER_TYPE)!=wanted)
         continue;
      bool delete_sent=trade.OrderDelete(ticket);
      if(!TradeResultAccepted(delete_sent,false,false,false))
         PrintTradeFailure("OrderDelete",(int)ticket);
     }
   Print("Pending side cancelled: ",reason);
  }

//+------------------------------------------------------------------+
void CancelAllPendings(const string reason)
  {
   int removed=0;
   for(int i=OrdersTotal()-1; i>=0; i--)
     {
      ulong ticket=OrderGetTicket(i);
      if(ticket==0)
         continue;
      if(OrderGetString(ORDER_SYMBOL)!=_Symbol ||
         (long)OrderGetInteger(ORDER_MAGIC)!=InpMagic)
         continue;
      bool delete_sent=trade.OrderDelete(ticket);
      if(TradeResultAccepted(delete_sent,false,false,false))
         removed++;
      else
         PrintTradeFailure("OrderDelete",(int)ticket);
     }
   if(removed>0)
      PrintFormat("Cancelled %d pending orders: %s",removed,reason);
  }

//+------------------------------------------------------------------+
void CloseAllPositions(const string reason)
  {
   int closed=0;
   for(int i=PositionsTotal()-1; i>=0; i--)
     {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol ||
         (long)PositionGetInteger(POSITION_MAGIC)!=InpMagic)
         continue;
      bool close_sent=trade.PositionClose(ticket,InpMaxSlippagePoints);
      bool fully_closed=(TradeResultAccepted(close_sent,false,false,false) &&
                         !PositionSelectByTicket(ticket));
      if(fully_closed)
         closed++;
      else
         PrintTradeFailure("PositionClose",(int)ticket);
     }
   if(closed>0)
      PrintFormat("Closed %d positions: %s",closed,reason);
  }

//+------------------------------------------------------------------+
double NormalizePrice(const double price)
  {
   int digits=(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS);
   double tick_size=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
   if(tick_size<=0.0)
      return(NormalizeDouble(price,digits));
   return(NormalizeDouble(MathRound(price/tick_size)*tick_size,digits));
  }

//+------------------------------------------------------------------+
double NormalizeVolume(const double volume)
  {
   double min_volume=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double max_volume=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(step<=0.0)
      step=min_volume;
   double value=MathFloor(volume/step+1e-8)*step;
   value=MathMax(min_volume,MathMin(max_volume,value));
   int digits=0;
   double probe=step;
   while(digits<8 && MathAbs(probe-MathRound(probe))>1e-8)
     {
      probe*=10.0;
      digits++;
     }
   return(NormalizeDouble(value,digits));
  }

//+------------------------------------------------------------------+
string RiskKey(const string suffix)
  {
   long login=AccountInfoInteger(ACCOUNT_LOGIN);
   string symbol_key=StringSubstr(_Symbol,0,12);
   return(StringFormat("SGR.%I64X.%s.%I64X.%s",login,symbol_key,InpMagic,suffix));
  }

//+------------------------------------------------------------------+
void SetRiskLock(const bool enabled)
  {
   g_risk_lock=enabled;
   GlobalVariableSet(RiskKey("lock"),(enabled ? 1.0 : 0.0));
   GlobalVariablesFlush();
  }

//+------------------------------------------------------------------+
string PartialKey(const ulong ticket)
  {
   return(StringFormat("%s.partial.%I64u",InpOrderPrefix,ticket));
  }

//+------------------------------------------------------------------+
bool TradeResultAccepted(const bool request_sent,
                         const bool allow_placed,
                         const bool allow_partial,
                         const bool allow_no_changes)
  {
   if(!request_sent)
      return(false);
   uint code=trade.ResultRetcode();
   if(code==TRADE_RETCODE_DONE)
      return(true);
   if(allow_placed && code==TRADE_RETCODE_PLACED)
      return(true);
   if(allow_partial && code==TRADE_RETCODE_DONE_PARTIAL)
      return(true);
   if(allow_no_changes && code==TRADE_RETCODE_NO_CHANGES)
      return(true);
   return(false);
  }

//+------------------------------------------------------------------+
void PrintTradeFailure(const string action,const int ref)
  {
   PrintFormat("%s failed ref=%d retcode=%u (%s)",action,ref,
               trade.ResultRetcode(),trade.ResultRetcodeDescription());
  }
//+------------------------------------------------------------------+

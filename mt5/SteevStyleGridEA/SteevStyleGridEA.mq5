//+------------------------------------------------------------------+
//| SteevStyleGridEA.mq5                                             |
//| Symmetric BUY STOP / SELL STOP grid with OCO and risk controls   |
//| Shadow/demo validation first. No martingale.                     |
//+------------------------------------------------------------------+
#property copyright "WaipopDev"
#property version   "1.04"
#property strict
#property description "Pending-order grid with OCO, Hedge, and video-style one-position reversal; exits are calculated from basket floating P/L."

#include <Trade/Trade.mqh>

enum ENUM_GRID_MODE
  {
   GRID_OCO = 0,       // First side triggered -> delete opposite pending side
   GRID_HEDGE = 1,     // Keep both pending sides until another safety rule removes them
   GRID_REVERSAL = 2   // One position plus one opposite pending reversal
  };

input group "Grid"
input ENUM_GRID_MODE InpGridMode              = GRID_REVERSAL; // โหมดกริด OCO/Hedge/Reversal
input double         InpFixedLot              = 0.01;      // ล็อตต่อไม้
input int            InpLevelsPerSide         = 1;         // จำนวนชั้นต่อฝั่ง (Reversal ใช้ 1)
input int            InpInitialOffsetPoints   = 200;       // ระยะชั้นแรก points
input int            InpGridSpacingPoints     = 200;       // ระยะห่างแต่ละชั้น points
input int            InpPendingExpiryHours    = 4;         // อายุ pending ชั่วโมง
input int            InpRecenterDistancePoints= 900;       // ระยะเลื่อนจุดกริดใหม่

// ไม่มี TP/SL ต่อออเดอร์: EA คำนวณทางออกจาก Basket Floating P/L เท่านั้น

input group "Account and basket safety"
input double         InpBasketTakeProfitMoney = 5.0;       // กำไรรวมปิดทั้งหมด เหรียญ
input bool           InpRestartImmediatelyAfterBasketTP = true; // ปิดกำไรแล้วเปิดใหม่ทันที
input double         InpBasketStopLossMoney   = 5.0;       // ขาดทุนรวมปิดทั้งหมด เหรียญ
input bool           InpRestartImmediatelyAfterBasketSL = true; // ปิดขาดทุนแล้วเปิดกริดใหม่ทันที
input bool           InpClearRiskLockOnInit   = true;      // ล้าง persistent risk lock ตอนเปิด EA

input group "Execution filters"
input int            InpMaxSpreadPoints       = 80;        // spread สูงสุด points
input int            InpMaxSlippagePoints     = 30;        // slippage สูงสุด points
input int            InpSessionStartHour      = 0;         // เวลาเริ่มเทรด ชั่วโมง
input int            InpSessionEndHour        = 24;        // เวลาหยุดเทรด ชั่วโมง
input bool           InpCancelPendingsOutsideSession = true; // ลบ pending นอกเวลา
input bool           InpCancelPendingsOnRemove       = false; // ถอด EA แล้วลบ pending

input group "Identity"
input long           InpMagic                 = 26080602;  // Magic number ของ Reversal Shadow
input string         InpOrderPrefix           = "SGRID-R"; // prefix comment คำสั่ง Reversal

CTrade   trade;
double   g_anchor_price       = 0.0;
datetime g_last_flat_time     = 0;
bool     g_risk_lock          = false;
int      g_previous_positions = 0;
int      g_previous_pendings  = 0;
bool     g_cycle_active       = false;
bool     g_exit_seen          = false;
bool     g_basket_tp_closing  = false;
bool     g_basket_sl_closing  = false;

//+------------------------------------------------------------------+
int OnInit()
  {
   if(!ValidateInputs())
      return(INIT_PARAMETERS_INCORRECT);

   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(InpMaxSlippagePoints);
   trade.SetTypeFillingBySymbol(_Symbol);
   trade.SetAsyncMode(false);

   RestoreRiskLock();
   ClearLegacyPerOrderExits();
   g_previous_positions=CountOurPositions();
   g_previous_pendings=CountOurPendings();
   g_cycle_active=(g_previous_positions>0);
   if(g_previous_positions==0 && g_previous_pendings>0)
     {
      CancelAllPendings("restart orphan-safety reset");
      g_previous_pendings=CountOurPendings();
     }
   EventSetTimer(5);

   PrintFormat("%s initialized on %s. Mode=%s, levels=%d, lot=%.2f, basket_tp=%.2f, basket_sl=%.2f",
               InpOrderPrefix,_Symbol,GridModeName(),
               InpLevelsPerSide,InpFixedLot,InpBasketTakeProfitMoney,InpBasketStopLossMoney);
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
   ManageRiskAndPositions();
   MaintainGrid();
  }

//+------------------------------------------------------------------+
void OnTimer()
  {
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

   if(is_entry && InpGridMode==GRID_REVERSAL)
     {
      // Keep only the opposite stop after a reversal entry.
      if(deal_type==DEAL_TYPE_BUY)
         CancelPendingType(ORDER_TYPE_BUY_STOP,"REVERSAL BUY activated");
      else if(deal_type==DEAL_TYPE_SELL)
         CancelPendingType(ORDER_TYPE_SELL_STOP,"REVERSAL SELL activated");
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
   if(InpSessionStartHour<0 || InpSessionStartHour>23 || InpSessionEndHour<1 || InpSessionEndHour>24)
     {
      Print("Session hours are invalid.");
      return(false);
     }
   return(true);
  }

//+------------------------------------------------------------------+
void ClearLegacyPerOrderExits()
  {
   for(int i=PositionsTotal()-1; i>=0; i--)
     {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol ||
         (long)PositionGetInteger(POSITION_MAGIC)!=InpMagic)
         continue;
      double old_sl=PositionGetDouble(POSITION_SL);
      double old_tp=PositionGetDouble(POSITION_TP);
      if(old_sl==0.0 && old_tp==0.0)
         continue;
      bool modify_sent=trade.PositionModify(ticket,0.0,0.0);
      if(TradeResultAccepted(modify_sent,false,false,true))
         PrintFormat("Cleared legacy position SL/TP ticket=%I64u",ticket);
      else
         PrintTradeFailure("ClearLegacyPositionSLTP",(int)ticket);
     }

   for(int i=OrdersTotal()-1; i>=0; i--)
     {
      ulong ticket=OrderGetTicket(i);
      if(ticket==0)
         continue;
      if(OrderGetString(ORDER_SYMBOL)!=_Symbol ||
         (long)OrderGetInteger(ORDER_MAGIC)!=InpMagic)
         continue;
      double old_sl=OrderGetDouble(ORDER_SL);
      double old_tp=OrderGetDouble(ORDER_TP);
      if(old_sl==0.0 && old_tp==0.0)
         continue;
      bool delete_sent=trade.OrderDelete(ticket);
      if(TradeResultAccepted(delete_sent,false,false,false))
         PrintFormat("Deleted legacy pending SL/TP ticket=%I64u",ticket);
      else
         PrintTradeFailure("DeleteLegacyPendingSLTP",(int)ticket);
     }
  }

//+------------------------------------------------------------------+
void RestoreRiskLock()
  {
   string lock_key=RiskKey("lock");
   bool stored_lock=(GlobalVariableCheck(lock_key) && GlobalVariableGet(lock_key)>0.5);
   bool owned_exposure=(CountOurPositions()>0 || CountOurPendings()>0);

   if(InpClearRiskLockOnInit && !owned_exposure)
     {
      stored_lock=false;
      GlobalVariableSet(lock_key,0.0);
      GlobalVariablesFlush();
      Print("Persistent risk lock cleared on init.");
     }

   g_risk_lock=stored_lock;
   PrintFormat("Persistent risk lock restored: %s",(g_risk_lock ? "ON" : "OFF"));
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

   if(InpGridMode==GRID_REVERSAL)
     {
      MaintainReversal(positions,pendings);
      return;
     }

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
      g_cycle_active=false;
      g_exit_seen=false;
     }
   else if(pending_cycle_ended)
     {
      g_cycle_active=false;
      g_exit_seen=false;
     }
   else if(g_exit_seen && positions>0)
      g_exit_seen=false;

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
   if(positions==0 && pendings==0)
     {
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
string GridModeName()
  {
   if(InpGridMode==GRID_OCO)
      return("OCO");
   if(InpGridMode==GRID_HEDGE)
      return("HEDGE");
   return("REVERSAL");
  }

//+------------------------------------------------------------------+
int CountOurPendingsType(const ENUM_ORDER_TYPE wanted)
  {
   int count=0;
   for(int i=OrdersTotal()-1; i>=0; i--)
     {
      ulong ticket=OrderGetTicket(i);
      if(ticket==0)
         continue;
      if(OrderGetString(ORDER_SYMBOL)!=_Symbol ||
         (long)OrderGetInteger(ORDER_MAGIC)!=InpMagic)
         continue;
      if((ENUM_ORDER_TYPE)OrderGetInteger(ORDER_TYPE)==wanted)
         count++;
     }
   return(count);
  }

//+------------------------------------------------------------------+
bool PlaceReversalPending(const ENUM_ORDER_TYPE order_type,const double price,const string comment)
  {
   double lot=NormalizeVolume(InpFixedLot);
   ENUM_ORDER_TYPE_TIME time_type=(InpPendingExpiryHours>0 ? ORDER_TIME_SPECIFIED : ORDER_TIME_GTC);
   datetime expiration=(InpPendingExpiryHours>0 ? TimeCurrent()+InpPendingExpiryHours*3600 : 0);
   bool sent=false;
   if(order_type==ORDER_TYPE_BUY_STOP)
      sent=trade.BuyStop(lot,NormalizePrice(price),_Symbol,0.0,0.0,time_type,expiration,comment);
   else if(order_type==ORDER_TYPE_SELL_STOP)
      sent=trade.SellStop(lot,NormalizePrice(price),_Symbol,0.0,0.0,time_type,expiration,comment);
   if(TradeResultAccepted(sent,true,false,false) && trade.ResultOrder()>0)
      return(true);
   PrintTradeFailure("ReversalPending",0);
   return(false);
  }

//+------------------------------------------------------------------+
bool PlaceFreshReversal()
  {
   if(CountOurPositions()>0 || CountOurPendings()>0)
      return(false);

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick))
      return(false);

   int stops_level=(int)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   int offset=MathMax(InpInitialOffsetPoints,stops_level+1);
   g_anchor_price=(tick.ask+tick.bid)/2.0;
   double buy_price=tick.ask+offset*_Point;
   double sell_price=tick.bid-offset*_Point;
   bool buy_ok=PlaceReversalPending(ORDER_TYPE_BUY_STOP,buy_price,
                                    StringFormat("%s:R:B",InpOrderPrefix));
   bool sell_ok=PlaceReversalPending(ORDER_TYPE_SELL_STOP,sell_price,
                                     StringFormat("%s:R:S",InpOrderPrefix));
   if(!buy_ok || !sell_ok)
     {
      CancelAllPendings("reversal pair rollback");
      return(false);
     }
   PrintFormat("Reversal pair placed at anchor %.5f: BUY STOP=1, SELL STOP=1",
               g_anchor_price);
   return(true);
  }

//+------------------------------------------------------------------+
void MaintainReversal(const int positions,const int pendings)
  {
   if(positions>1)
     {
      PrintFormat("Reversal exposure violation: positions=%d; flattening before restart.",positions);
      CloseAllPositions("reversal max-one-position enforcement");
      CancelAllPendings("reversal max-one-position enforcement");
      return;
     }

   if(positions==0)
     {
      if(g_previous_positions>0 || g_exit_seen)
         CancelAllPendings("reversal flat reset");
      if(CountOurPendings()==0)
         PlaceFreshReversal();
      return;
     }

   ENUM_POSITION_TYPE position_type=POSITION_TYPE_BUY;
   for(int i=PositionsTotal()-1; i>=0; i--)
     {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL)==_Symbol &&
         (long)PositionGetInteger(POSITION_MAGIC)==InpMagic)
        {
         position_type=(ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         break;
        }
     }

   ENUM_ORDER_TYPE wanted=(position_type==POSITION_TYPE_BUY ? ORDER_TYPE_SELL_STOP : ORDER_TYPE_BUY_STOP);
   ENUM_ORDER_TYPE unwanted=(position_type==POSITION_TYPE_BUY ? ORDER_TYPE_BUY_STOP : ORDER_TYPE_SELL_STOP);
   if(CountOurPendingsType(unwanted)>0)
      CancelPendingType(unwanted,"reversal same-side pending cleanup");

   int opposite_count=CountOurPendingsType(wanted);
   if(opposite_count>1)
     {
      CancelPendingType(wanted,"reversal duplicate pending cleanup");
      opposite_count=0;
     }
   if(opposite_count==0)
     {
      MqlTick tick;
      if(!SymbolInfoTick(_Symbol,tick))
         return;
      int stops_level=(int)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
      int offset=MathMax(InpInitialOffsetPoints,stops_level+1);
      double price=(wanted==ORDER_TYPE_BUY_STOP ? tick.ask+offset*_Point : tick.bid-offset*_Point);
      PlaceReversalPending(wanted,price,
                           StringFormat("%s:R:%s",InpOrderPrefix,
                                        wanted==ORDER_TYPE_BUY_STOP ? "B" : "S"));
     }
  }

//+------------------------------------------------------------------+
bool PlaceFreshGrid()
  {
   if(InpGridMode==GRID_REVERSAL)
      return(PlaceFreshReversal());

   if(CountOurPositions()>0 || CountOurPendings()>0)
      return(false);

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick))
      return(false);

   double lot=NormalizeVolume(InpFixedLot);
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
      string buy_comment=StringFormat("%s:B:%02d",InpOrderPrefix,level+1);

      bool buy_sent=trade.BuyStop(lot,buy_price,_Symbol,0.0,0.0,time_type,expiration,buy_comment);
      if(TradeResultAccepted(buy_sent,true,false,false) && trade.ResultOrder()>0)
         buy_ok++;
      else
         PrintTradeFailure("BuyStop",level+1);

      double sell_price=NormalizePrice(tick.bid-distance*_Point);
      string sell_comment=StringFormat("%s:S:%02d",InpOrderPrefix,level+1);

      bool sell_sent=trade.SellStop(lot,sell_price,_Symbol,0.0,0.0,time_type,expiration,sell_comment);
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
   // Re-run after terminal/account synchronization so legacy server-side
   // SL/TP is removed from positions and pendings created by older builds.
   ClearLegacyPerOrderExits();

   if(g_risk_lock)
     {
      CancelAllPendings("persistent risk-lock enforcement");
      CloseAllPositions("persistent risk-lock enforcement");
      return;
     }

   double basket=OurFloatingProfit();
   int positions=CountOurPositions();

   if(g_basket_tp_closing)
     {
      CloseAllPositions("basket TP retry until flat");
      CancelAllPendings("basket TP retry until flat");
      if(CountOurPositions()==0 && CountOurPendings()==0)
        {
         g_basket_tp_closing=false;
         g_last_flat_time=0;
         g_cycle_active=false;
         g_exit_seen=false;
         g_previous_positions=0;
         g_previous_pendings=0;
         Print("Basket TP cleanup complete: all owned positions/pending orders are closed; grid may restart immediately.");
        }
      return;
     }

   if(g_basket_sl_closing)
     {
      CloseAllPositions("basket SL retry until flat");
      CancelAllPendings("basket SL retry until flat");
      if(RestartAfterBasketSL())
         Print("Basket SL cleanup complete: all owned exposure is zero; grid may restart immediately.");
      return;
     }

   if(positions>0 && InpBasketTakeProfitMoney>0.0 && basket>=InpBasketTakeProfitMoney)
     {
      g_basket_tp_closing=true;
      CloseAllPositions("basket TP");
      CancelAllPendings("basket TP");
      if(InpRestartImmediatelyAfterBasketTP && CountOurPositions()==0 && CountOurPendings()==0)
        {
         g_basket_tp_closing=false;
         g_last_flat_time=0;
         g_cycle_active=false;
         g_exit_seen=false;
         g_previous_positions=0;
         g_previous_pendings=0;
         PrintFormat("Basket TP %.2f reached: restarting grid immediately without cooldown.",basket);
        }
      else
         PrintFormat("Basket TP %.2f reached: retrying close/delete until all owned exposure is zero.",basket);
      return;
     }

   if(positions>0 && InpBasketStopLossMoney>0.0 && basket<=-InpBasketStopLossMoney)
     {
      if(InpRestartImmediatelyAfterBasketSL)
        {
         g_basket_sl_closing=true;
         CloseAllPositions("basket SL");
         CancelAllPendings("basket SL");
         if(RestartAfterBasketSL())
            PrintFormat("Basket SL %.2f reached: restarting grid immediately without risk lock.",basket);
         else
            PrintFormat("Basket SL %.2f reached: retrying close/delete until all owned exposure is zero.",basket);
        }
      else
        {
         CloseAllPositions("basket SL");
         CancelAllPendings("basket SL");
         SetRiskLock(true);
         PrintFormat("Basket SL %.2f reached: persistent risk lock enabled.",basket);
        }
      return;
     }
  }

//+------------------------------------------------------------------+
bool RestartAfterBasketSL()
  {
   if(CountOurPositions()>0 || CountOurPendings()>0)
      return(false);

   g_basket_sl_closing=false;
   g_last_flat_time=0;
   g_cycle_active=false;
   g_exit_seen=false;
   g_previous_positions=0;
   g_previous_pendings=0;
   return(true);
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

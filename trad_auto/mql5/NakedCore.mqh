// Pure chronological closed-bar port of trad_auto/core.py.
struct Setup { int side; int bos_index; datetime bos_time; double level; double stop; };
bool ValidBars(const MqlRates &b[],int seconds,datetime now,int width=2)
{
   int n=ArraySize(b);
   if(n<2*width+6) return false;
   datetime previous=-1;
   for(int i=0;i<n;i++) {
      if(b[i].time<0 || b[i].time<=previous || b[i].time+seconds>now) return false;
      if(!MathIsValidNumber(b[i].open)||!MathIsValidNumber(b[i].high)||!MathIsValidNumber(b[i].low)||!MathIsValidNumber(b[i].close)) return false;
      if(b[i].low<=0 || b[i].low>MathMin(b[i].open,b[i].close) || MathMax(b[i].open,b[i].close)>b[i].high) return false;
      previous=b[i].time;
   }
   return now-(b[n-1].time+seconds)<=seconds;
}
int Structure(const MqlRates &b[],int n,int width,double &last_high,double &last_low)
{
   double prev_high=0,prev_low=0; int highs=0,lows=0;
   last_high=0;last_low=0;
   for(int i=width;i<n-width;i++) {
      bool hi=true,lo=true;
      for(int k=i-width;k<=i+width;k++) {
         if(k==i) continue;
         if(b[i].high<=b[k].high) hi=false;
         if(b[i].low>=b[k].low) lo=false;
      }
      if(hi) {prev_high=last_high;last_high=b[i].high;highs++;}
      if(lo) {prev_low=last_low;last_low=b[i].low;lows++;}
   }
   if(highs<2||lows<2) return 0;
   if(last_high>prev_high&&last_low>prev_low) return 1;
   if(last_high<prev_high&&last_low<prev_low) return -1;
   return 0;
}
bool FindSetup(const MqlRates &b[],int higher_trend,Setup &s,int width=2,int retest=4)
{
   s.side=0;s.bos_index=-1;s.bos_time=0;s.level=0;s.stop=0;
   int n=ArraySize(b); if(n<2*width+6) return false;
   MqlRates latest=b[n-1];
   for(int j=n-2;j>MathMax(0,n-retest-2);j--) {
      double hi,lo;int trend=Structure(b,j,width,hi,lo);
      if(trend==0||higher_trend!=trend) continue;
      bool buy=trend==1; double level=buy?hi:lo;
      bool broken=buy?(b[j-1].close<=level&&level<b[j].close):(b[j-1].close>=level&&level>b[j].close);
      if(!broken) continue;
      double body=MathAbs(latest.close-latest.open);
      double wick=buy?MathMin(latest.open,latest.close)-latest.low:latest.high-MathMax(latest.open,latest.close);
      bool rejection=buy?(latest.close>latest.open&&latest.close>level):(latest.close<latest.open&&latest.close<level);
      bool intact=true;
      for(int k=j+1;k<n;k++) if(buy?b[k].close<=level:b[k].close>=level) intact=false;
      if(!(latest.low<=level&&level<=latest.high&&rejection&&wick>=body&&intact)) continue;
      double stop=buy?b[j].low:b[j].high;
      for(int k=j+1;k<n;k++) stop=buy?MathMin(stop,b[k].low):MathMax(stop,b[k].high);
      double risk=MathAbs(latest.close-stop),target=latest.close+trend*risk;
      if(risk<=0||target<=0||!MathIsValidNumber(target)) continue;
      s.side=trend;s.bos_index=j;s.bos_time=b[j].time;s.level=level;s.stop=stop;return true;
   }
   return false;
}
double FloorVolume(double budget,double loss_per_lot,double step,double minimum,double maximum)
{
   if(budget<=0||loss_per_lot<=0||step<=0||minimum<=0||maximum<minimum) return 0;
   double lots=MathFloor(MathMin(budget/loss_per_lot,maximum)/step)*step;
   if(lots<minimum||lots*loss_per_lot>budget+1e-9) return 0;
   return NormalizeDouble(lots,8);
}

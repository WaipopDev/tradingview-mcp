// Generated synthetic reference fixtures. DO NOT treat as market results.
bool RunCoreSelfTests()
{
   int failures=0;
   MqlRates b[]; Setup s; double hi,lo;
   // Fixture 0; Python reference side=0
   ArrayResize(b,44);
   b[0].time=0;b[0].open=100;b[0].high=101.13126555125983;b[0].low=98.359855780292378;b[0].close=100.2504229741004;
   b[1].time=300;b[1].open=100.2504229741004;b[1].high=101.47757065452922;b[1].low=100.15740913794872;b[1].close=101.01752731683712;
   b[2].time=600;b[2].open=101.01752731683712;b[2].high=102.01448325488029;b[2].low=99.522884794765204;b[2].close=101.12858476821893;
   b[3].time=900;b[3].open=101.12858476821893;b[3].high=103.05322923683761;b[3].low=100.13940053242167;b[3].close=101.49656723222076;
   b[4].time=1200;b[4].open=101.49656723222076;b[4].high=104.40619832452052;b[4].low=100.52747462507186;b[4].close=102.96343053157807;
   b[5].time=1500;b[5].open=102.96343053157807;b[5].high=103.09472325387713;b[5].low=102.7728063091218;b[5].close=103.08086162060098;
   b[6].time=1800;b[6].open=103.08086162060098;b[6].high=103.6974579523221;b[6].low=101.64676484976995;b[6].close=102.74688265930611;
   b[7].time=2100;b[7].open=102.74688265930611;b[7].high=105.91958649934904;b[7].low=102.24803007939158;b[7].close=104.29572136085088;
   b[8].time=2400;b[8].open=104.29572136085088;b[8].high=105.69879766341563;b[8].low=102.59049758836966;b[8].close=105.4110028079978;
   b[9].time=2700;b[9].open=105.4110028079978;b[9].high=106.88894500427378;b[9].low=103.44838289910906;b[9].close=104.41433390878733;
   b[10].time=3000;b[10].open=104.41433390878733;b[10].high=107.83884397117231;b[10].low=103.61082857527845;b[10].close=105.84510777068917;
   b[11].time=3300;b[11].open=105.84510777068917;b[11].high=106.28220926110723;b[11].low=103.47606550918013;b[11].close=104.81819375814453;
   b[12].time=3600;b[12].open=104.81819375814453;b[12].high=106.99584499231436;b[12].low=104.78200242411545;b[12].close=106.20970739515919;
   b[13].time=3900;b[13].open=106.20970739515919;b[13].high=108.53871720018454;b[13].low=105.0301643087174;b[13].close=107.78907523270775;
   b[14].time=4200;b[14].open=107.78907523270775;b[14].high=108.642219995538;b[14].low=106.90819322577856;b[14].close=107.1585723718896;
   b[15].time=4500;b[15].open=107.1585723718896;b[15].high=107.61331129266138;b[15].low=105.21895304950721;b[15].close=106.82703749698295;
   b[16].time=4800;b[16].open=106.82703749698295;b[16].high=107.4554912163959;b[16].low=104.81419877723839;b[16].close=105.39403499348786;
   b[17].time=5100;b[17].open=105.39403499348786;b[17].high=105.568797766606;b[17].low=103.26320080283122;b[17].close=103.57399950307708;
   b[18].time=5400;b[18].open=103.57399950307708;b[18].high=103.92496610806649;b[18].low=103.39218065133768;b[18].close=103.85991528643231;
   b[19].time=5700;b[19].open=103.85991528643231;b[19].high=104.57140773286102;b[19].low=100.99047171868047;b[19].close=102.00669515308797;
   b[20].time=6000;b[20].open=102.00669515308797;b[20].high=102.86543004060056;b[20].low=98.500115496979959;b[20].close=100.41589603626521;
   b[21].time=6300;b[21].open=100.41589603626521;b[21].high=103.26294478980031;b[21].low=98.856713886263236;b[21].close=101.99262044619653;
   b[22].time=6600;b[22].open=101.99262044619653;b[22].high=103.71718644307434;b[22].low=101.00272015873502;b[22].close=101.90699639405115;
   b[23].time=6900;b[23].open=101.90699639405115;b[23].high=102.93136959328655;b[23].low=99.507494220414657;b[23].close=100.84278207669536;
   b[24].time=7200;b[24].open=100.84278207669536;b[24].high=102.38810620960268;b[24].low=99.322991752459501;b[24].close=100.11893744993647;
   b[25].time=7500;b[25].open=100.11893744993647;b[25].high=101.97041023772186;b[25].low=98.871588574598235;b[25].close=100.43563503510752;
   b[26].time=7800;b[26].open=100.43563503510752;b[26].high=102.95890651519318;b[26].low=98.740584028526655;b[26].close=102.11312377719408;
   b[27].time=8100;b[27].open=102.11312377719408;b[27].high=104.2385044075167;b[27].low=101.99512421582104;b[27].close=102.85964634687792;
   b[28].time=8400;b[28].open=102.85964634687792;b[28].high=105.36690493551454;b[28].low=102.55980299420797;b[28].close=103.48017327903248;
   b[29].time=8700;b[29].open=103.48017327903248;b[29].high=106.04309215972988;b[29].low=103.17846140927779;b[29].close=104.09934921781957;
   b[30].time=9000;b[30].open=104.09934921781957;b[30].high=104.81506909711727;b[30].low=103.02020679644038;b[30].close=103.9416157865065;
   b[31].time=9300;b[31].open=103.9416157865065;b[31].high=105.84506001471551;b[31].low=103.91712042132048;b[31].close=104.66333166566568;
   b[32].time=9600;b[32].open=104.66333166566568;b[32].high=106.42639097362525;b[32].low=102.6058546125784;b[32].close=102.74548542581178;
   b[33].time=9900;b[33].open=102.74548542581178;b[33].high=105.62837104917665;b[33].low=101.34725579101665;b[33].close=104.04475751506237;
   b[34].time=10200;b[34].open=104.04475751506237;b[34].high=105.77707710293407;b[34].low=104.01053006266704;b[34].close=104.93916972691382;
   b[35].time=10500;b[35].open=104.93916972691382;b[35].high=108.44469930034241;b[35].low=103.95696551447821;b[35].close=106.84908779231671;
   b[36].time=10800;b[36].open=106.84908779231671;b[36].high=107.69529536234107;b[36].low=104.89805625607315;b[36].close=106.33832558185767;
   b[37].time=11100;b[37].open=106.33832558185767;b[37].high=106.74087618886502;b[37].low=105.38181596201457;b[37].close=105.81537150277396;
   b[38].time=11400;b[38].open=105.81537150277396;b[38].high=105.9432900007302;b[38].low=103.57781417065375;b[38].close=104.67316943993954;
   b[39].time=11700;b[39].open=104.67316943993954;b[39].high=105.10297377227245;b[39].low=102.48918755197091;b[39].close=104.07942460620765;
   b[40].time=12000;b[40].open=104.07942460620765;b[40].high=105.996034527007;b[40].low=103.78642997961687;b[40].close=104.2199345639708;
   b[41].time=12300;b[41].open=104.2199345639708;b[41].high=105.34232072050409;b[41].low=101.86146145958567;b[41].close=103.48792811443982;
   b[42].time=12600;b[42].open=103.48792811443982;b[42].high=104.63348398827313;b[42].low=102.35331642433857;b[42].close=102.97310923291921;
   b[43].time=12900;b[43].open=102.97310923291921;b[43].high=104.41276703691693;b[43].low=101.738415874274;b[43].close=101.78656330156242;
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 1; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 2; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 3; Python reference side=0
   ArrayResize(b,45);
   b[44].time=13200;b[44].open=101.78656330156242;b[44].high=101.98898183437821;b[44].low=100.30688112823019;b[44].close=101.37563414402317;
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 4; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 5; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 6; Python reference side=0
   ArrayResize(b,46);
   b[45].time=13500;b[45].open=101.37563414402317;b[45].high=102.86218047212186;b[45].low=100.68639241371882;b[45].close=102.74991329032476;
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 7; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 8; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 9; Python reference side=0
   ArrayResize(b,47);
   b[46].time=13800;b[46].open=102.74991329032476;b[46].high=104.64279013148798;b[46].low=102.02263542670677;b[46].close=102.79053958868947;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 10; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 11; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 12; Python reference side=0
   ArrayResize(b,48);
   b[47].time=14100;b[47].open=102.79053958868947;b[47].high=103.42383007600722;b[47].low=100.73230659254958;b[47].close=101.52374595414065;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 13; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 14; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 15; Python reference side=0
   ArrayResize(b,49);
   b[48].time=14400;b[48].open=101.52374595414065;b[48].high=103.21171673621481;b[48].low=98.972122530350433;b[48].close=99.956501252570689;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 16; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 17; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 18; Python reference side=-1
   ArrayResize(b,50);
   b[49].time=14700;b[49].open=99.956501252570689;b[49].high=100.86941112674188;b[49].low=99.014751668776555;b[49].close=99.76287599743867;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=-1) failures++;
   if(s.bos_index!=48 || MathAbs(s.stop-103.21171673621481)>1e-8 || MathAbs(s.level-100.30688112823019)>1e-8) failures++;
   // Fixture 19; Python reference side=0
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 20; Python reference side=0
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 21; Python reference side=0
   ArrayResize(b,44);
   b[0].time=0;b[0].open=100;b[0].high=102.09712603700086;b[0].low=99.992000146272318;b[0].close=100.40748262277489;
   b[1].time=300;b[1].open=100.40748262277489;b[1].high=101.33727650664468;b[1].low=99.904930763315633;b[1].close=100.27572909443393;
   b[2].time=600;b[2].open=100.27572909443393;b[2].high=102.43403445489602;b[2].low=99.07060449014665;b[2].close=101.32021816105269;
   b[3].time=900;b[3].open=101.32021816105269;b[3].high=101.84407149606443;b[3].low=100.1509752947707;b[3].close=100.60892548956146;
   b[4].time=1200;b[4].open=100.60892548956146;b[4].high=103.68285392255561;b[4].low=100.56224386235367;b[4].close=101.9304862392965;
   b[5].time=1500;b[5].open=101.9304862392965;b[5].high=103.92920485674222;b[5].low=100.92751871698238;b[5].close=102.65601283411223;
   b[6].time=1800;b[6].open=102.65601283411223;b[6].high=103.66643941899389;b[6].low=101.18492794163016;b[6].close=102.64603296657525;
   b[7].time=2100;b[7].open=102.64603296657525;b[7].high=103.74395623561526;b[7].low=100.24162094512712;b[7].close=101.32654742901343;
   b[8].time=2400;b[8].open=101.32654742901343;b[8].high=102.76456280148483;b[8].low=100.27245455081803;b[8].close=100.84261823353738;
   b[9].time=2700;b[9].open=100.84261823353738;b[9].high=103.1030594719183;b[9].low=99.436750962898458;b[9].close=101.75042613768305;
   b[10].time=3000;b[10].open=101.75042613768305;b[10].high=103.42926171495021;b[10].low=101.4412791098937;b[10].close=101.89069212616741;
   b[11].time=3300;b[11].open=101.89069212616741;b[11].high=102.78581455771827;b[11].low=100.10462739213239;b[11].close=102.15090494052184;
   b[12].time=3600;b[12].open=102.15090494052184;b[12].high=102.27553235321862;b[12].low=99.781172752764306;b[12].close=100.46036625785949;
   b[13].time=3900;b[13].open=100.46036625785949;b[13].high=101.04667509573629;b[13].low=98.95338282624671;b[13].close=99.707925748311467;
   b[14].time=4200;b[14].open=99.707925748311467;b[14].high=100.58081884483245;b[14].low=98.476281214793048;b[14].close=98.501149047034275;
   b[15].time=4500;b[15].open=98.501149047034275;b[15].high=99.521742607446868;b[15].low=96.877444570129043;b[15].close=97.159026168666941;
   b[16].time=4800;b[16].open=97.159026168666941;b[16].high=99.021028628290452;b[16].low=97.105939224670337;b[16].close=98.520929522617891;
   b[17].time=5100;b[17].open=98.520929522617891;b[17].high=100.10558300281028;b[17].low=97.414592648568359;b[17].close=99.457071410018415;
   b[18].time=5400;b[18].open=99.457071410018415;b[18].high=99.713310902308748;b[18].low=97.556563959205093;b[18].close=98.688091488532308;
   b[19].time=5700;b[19].open=98.688091488532308;b[19].high=99.99992604148251;b[19].low=96.56447120404502;b[19].close=97.026179209270424;
   b[20].time=6000;b[20].open=97.026179209270424;b[20].high=98.322647103274718;b[20].low=96.407378445361516;b[20].close=96.985229903987857;
   b[21].time=6300;b[21].open=96.985229903987857;b[21].high=99.173732468364165;b[21].low=95.833276273970341;b[21].close=97.959586031907449;
   b[22].time=6600;b[22].open=97.959586031907449;b[22].high=98.717335688347447;b[22].low=96.797627402024915;b[22].close=97.129597317151536;
   b[23].time=6900;b[23].open=97.129597317151536;b[23].high=97.310866439104927;b[23].low=96.768812515313371;b[23].close=97.137575096357267;
   b[24].time=7200;b[24].open=97.137575096357267;b[24].high=97.721910628524796;b[24].low=94.840150743620313;b[24].close=96.524749718733005;
   b[25].time=7500;b[25].open=96.524749718733005;b[25].high=99.506720930633861;b[25].low=96.498631613854755;b[25].close=98.129585740769414;
   b[26].time=7800;b[26].open=98.129585740769414;b[26].high=98.667344829463474;b[26].low=97.291992283790535;b[26].close=97.891307326465025;
   b[27].time=8100;b[27].open=97.891307326465025;b[27].high=100.05296208959588;b[27].low=97.50254318134921;b[27].close=99.849503878379153;
   b[28].time=8400;b[28].open=99.849503878379153;b[28].high=100.51123219149628;b[28].low=97.455107196673424;b[28].close=99.133182584906109;
   b[29].time=8700;b[29].open=99.133182584906109;b[29].high=100.15729053490307;b[29].low=97.437419764359944;b[29].close=97.849038023253129;
   b[30].time=9000;b[30].open=97.849038023253129;b[30].high=99.49372762539906;b[30].low=95.138918134409622;b[30].close=96.880854733808647;
   b[31].time=9300;b[31].open=96.880854733808647;b[31].high=98.516531503936491;b[31].low=96.294139194341511;b[31].close=97.292550215641725;
   b[32].time=9600;b[32].open=97.292550215641725;b[32].high=98.61569446201959;b[32].low=95.912973929638383;b[32].close=97.064586622776645;
   b[33].time=9900;b[33].open=97.064586622776645;b[33].high=97.284749257231681;b[33].low=94.771808635257699;b[33].close=95.332556688932954;
   b[34].time=10200;b[34].open=95.332556688932954;b[34].high=96.852370312876602;b[34].low=94.603185443997276;b[34].close=95.912686305460724;
   b[35].time=10500;b[35].open=95.912686305460724;b[35].high=97.558316781899549;b[35].low=94.149698740206162;b[35].close=96.558833859667061;
   b[36].time=10800;b[36].open=96.558833859667061;b[36].high=97.232894021585736;b[36].low=94.783833249489717;b[36].close=95.174324302797856;
   b[37].time=11100;b[37].open=95.174324302797856;b[37].high=97.504931275072224;b[37].low=94.434698682133416;b[37].close=96.306322025651838;
   b[38].time=11400;b[38].open=96.306322025651838;b[38].high=97.698818492751684;b[38].low=95.255745054553287;b[38].close=96.719210923418771;
   b[39].time=11700;b[39].open=96.719210923418771;b[39].high=98.328401911132204;b[39].low=95.164805371673239;b[39].close=97.574739468687753;
   b[40].time=12000;b[40].open=97.574739468687753;b[40].high=99.435972268859857;b[40].low=96.223198276996627;b[40].close=96.786278601962039;
   b[41].time=12300;b[41].open=96.786278601962039;b[41].high=98.748010485725075;b[41].low=96.376923640260117;b[41].close=98.316578724050402;
   b[42].time=12600;b[42].open=98.316578724050402;b[42].high=98.478184137448224;b[42].low=96.383501836947318;b[42].close=96.810432986083953;
   b[43].time=12900;b[43].open=96.810432986083953;b[43].high=98.429914303475783;b[43].low=95.803267055450107;b[43].close=98.168627368721502;
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 22; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 23; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 24; Python reference side=0
   ArrayResize(b,45);
   b[44].time=13200;b[44].open=98.168627368721502;b[44].high=99.568323393578169;b[44].low=96.136782388289731;b[44].close=97.122128569073155;
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 25; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 26; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 27; Python reference side=0
   ArrayResize(b,46);
   b[45].time=13500;b[45].open=97.122128569073155;b[45].high=99.231325927686399;b[45].low=96.336603351582582;b[45].close=98.081633528736361;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 28; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 29; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 30; Python reference side=0
   ArrayResize(b,47);
   b[46].time=13800;b[46].open=98.081633528736361;b[46].high=100.54897270908148;b[46].low=96.838578887481489;b[46].close=99.434102492836999;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 31; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 32; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 33; Python reference side=0
   ArrayResize(b,48);
   b[47].time=14100;b[47].open=99.434102492836999;b[47].high=100.72330198210135;b[47].low=98.409607357705198;b[47].close=99.471028372617738;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 34; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 35; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 36; Python reference side=0
   ArrayResize(b,49);
   b[48].time=14400;b[48].open=99.471028372617738;b[48].high=101.58529613940149;b[48].low=98.567306605088703;b[48].close=101.26106176178048;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 37; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 38; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 39; Python reference side=0
   ArrayResize(b,50);
   b[49].time=14700;b[49].open=101.26106176178048;b[49].high=102.36890479180495;b[49].low=99.415339034625617;b[49].close=102.081098188493;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 40; Python reference side=0
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 41; Python reference side=1
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=1) failures++;
   if(s.bos_index!=47 || MathAbs(s.stop-98.409607357705198)>1e-8 || MathAbs(s.level-99.435972268859857)>1e-8) failures++;
   // Fixture 42; Python reference side=0
   ArrayResize(b,44);
   b[0].time=0;b[0].open=100;b[0].high=102.1821581944178;b[0].low=99.772702488089337;b[0].close=101.59506935986629;
   b[1].time=300;b[1].open=101.59506935986629;b[1].high=103.38609931541588;b[1].low=101.27261801809006;b[1].close=102.99099769181605;
   b[2].time=600;b[2].open=102.99099769181605;b[2].high=104.02040992941768;b[2].low=100.69845928651822;b[2].close=101.72248884556075;
   b[3].time=900;b[3].open=101.72248884556075;b[3].high=101.76790852630435;b[3].low=100.25632751329228;b[3].close=100.72626767644381;
   b[4].time=1200;b[4].open=100.72626767644381;b[4].high=101.50367629374561;b[4].low=99.97443320798989;b[4].close=100.81502119888634;
   b[5].time=1500;b[5].open=100.81502119888634;b[5].high=101.91406420593253;b[5].low=98.698821235557133;b[5].close=100.09673788078112;
   b[6].time=1800;b[6].open=100.09673788078112;b[6].high=101.19911124574483;b[6].low=97.364374863198989;b[6].close=99.083056277601543;
   b[7].time=2100;b[7].open=99.083056277601543;b[7].high=99.969481253252084;b[7].low=95.806590680824854;b[7].close=97.537669145157267;
   b[8].time=2400;b[8].open=97.537669145157267;b[8].high=99.482829241181548;b[8].low=96.202432978451029;b[8].close=97.481482765559164;
   b[9].time=2700;b[9].open=97.481482765559164;b[9].high=98.571706700187235;b[9].low=95.986270073557591;b[9].close=96.011438938474214;
   b[10].time=3000;b[10].open=96.011438938474214;b[10].high=97.464040962356819;b[10].low=93.919525778907271;b[10].close=94.085949836300145;
   b[11].time=3300;b[11].open=94.085949836300145;b[11].high=95.651883828424758;b[11].low=90.707808415162646;b[11].close=92.250576005452587;
   b[12].time=3600;b[12].open=92.250576005452587;b[12].high=94.239422290609511;b[12].low=90.54396388371876;b[12].close=91.085497960568958;
   b[13].time=3900;b[13].open=91.085497960568958;b[13].high=94.65965850924286;b[13].low=90.425625586735123;b[13].close=92.845796530874424;
   b[14].time=4200;b[14].open=92.845796530874424;b[14].high=95.378613851202431;b[14].low=91.118211221249283;b[14].close=94.798163437030993;
   b[15].time=4500;b[15].open=94.798163437030993;b[15].high=97.200217118685302;b[15].low=93.602965966414189;b[15].close=95.978215800014937;
   b[16].time=4800;b[16].open=95.978215800014937;b[16].high=96.42336288932583;b[16].low=95.347307894241823;b[16].close=95.556394715654264;
   b[17].time=5100;b[17].open=95.556394715654264;b[17].high=95.746598835386095;b[17].low=93.637049107804685;b[17].close=94.437430931039984;
   b[18].time=5400;b[18].open=94.437430931039984;b[18].high=97.80948880490395;b[18].low=93.174822405302621;b[18].close=96.259719767810836;
   b[19].time=5700;b[19].open=96.259719767810836;b[19].high=98.73909944033467;b[19].low=95.433160379407113;b[19].close=96.895235792879717;
   b[20].time=6000;b[20].open=96.895235792879717;b[20].high=98.092603947970218;b[20].low=94.207677487067613;b[20].close=95.340308558353783;
   b[21].time=6300;b[21].open=95.340308558353783;b[21].high=95.931844513491058;b[21].low=93.467448524185258;b[21].close=95.621444328777372;
   b[22].time=6600;b[22].open=95.621444328777372;b[22].high=96.718220391037391;b[22].low=92.733493827351481;b[22].close=93.879288325750508;
   b[23].time=6900;b[23].open=93.879288325750508;b[23].high=94.33058631636564;b[23].low=91.919204021989657;b[23].close=91.923801406361619;
   b[24].time=7200;b[24].open=91.923801406361619;b[24].high=93.611735006010406;b[24].low=90.704448451886918;b[24].close=93.438846048753732;
   b[25].time=7500;b[25].open=93.438846048753732;b[25].high=94.699372368701304;b[25].low=91.341035906610401;b[25].close=92.36713704965392;
   b[26].time=7800;b[26].open=92.36713704965392;b[26].high=93.346576983858199;b[26].low=89.327294395058232;b[26].close=90.977173736508888;
   b[27].time=8100;b[27].open=90.977173736508888;b[27].high=92.361365752850915;b[27].low=88.565086376275204;b[27].close=90.187675266646991;
   b[28].time=8400;b[28].open=90.187675266646991;b[28].high=90.293080340851589;b[28].low=88.20085926316662;b[28].close=89.504976426759356;
   b[29].time=8700;b[29].open=89.504976426759356;b[29].high=90.830271070015442;b[29].low=87.137265818174996;b[29].close=88.085198417364964;
   b[30].time=9000;b[30].open=88.085198417364964;b[30].high=90.872763835407113;b[30].low=88.0067314931418;b[30].close=89.327897190199963;
   b[31].time=9300;b[31].open=89.327897190199963;b[31].high=90.105761536108403;b[31].low=89.067401152481224;b[31].close=89.415441495222325;
   b[32].time=9600;b[32].open=89.415441495222325;b[32].high=91.695662145101323;b[32].low=88.401168758271524;b[32].close=90.180401791663343;
   b[33].time=9900;b[33].open=90.180401791663343;b[33].high=92.021394529909799;b[33].low=88.208088249502595;b[33].close=91.885423232335413;
   b[34].time=10200;b[34].open=91.885423232335413;b[34].high=94.527311685630252;b[34].low=90.202893086135063;b[34].close=93.775068578445641;
   b[35].time=10500;b[35].open=93.775068578445641;b[35].high=93.793245289844876;b[35].low=92.791329397338316;b[35].close=93.749249112890638;
   b[36].time=10800;b[36].open=93.749249112890638;b[36].high=94.421922830926576;b[36].low=90.896063874779585;b[36].close=92.568251028153256;
   b[37].time=11100;b[37].open=92.568251028153256;b[37].high=94.259623052694565;b[37].low=90.447275292423711;b[37].close=91.039133491024472;
   b[38].time=11400;b[38].open=91.039133491024472;b[38].high=92.263627691228862;b[38].low=87.714972168826421;b[38].close=89.537880377178098;
   b[39].time=11700;b[39].open=89.537880377178098;b[39].high=90.21299761679812;b[39].low=86.554915971242934;b[39].close=87.877440412981628;
   b[40].time=12000;b[40].open=87.877440412981628;b[40].high=88.579348179448388;b[40].low=85.278032003954735;b[40].close=87.160762852714811;
   b[41].time=12300;b[41].open=87.160762852714811;b[41].high=88.551677558067041;b[41].low=85.254466510114;b[41].close=87.915811861494234;
   b[42].time=12600;b[42].open=87.915811861494234;b[42].high=89.807856346614685;b[42].low=87.60958871830718;b[42].close=88.912964381137428;
   b[43].time=12900;b[43].open=88.912964381137428;b[43].high=90.747343556804068;b[43].low=88.873363991236161;b[43].close=89.024700177078756;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 43; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 44; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 45; Python reference side=0
   ArrayResize(b,45);
   b[44].time=13200;b[44].open=89.024700177078756;b[44].high=89.385436211141112;b[44].low=86.8709229101933;b[44].close=87.226573004396272;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 46; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 47; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 48; Python reference side=0
   ArrayResize(b,46);
   b[45].time=13500;b[45].open=87.226573004396272;b[45].high=87.603439734419624;b[45].low=84.475678081392914;b[45].close=85.34228297015305;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 49; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 50; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 51; Python reference side=0
   ArrayResize(b,47);
   b[46].time=13800;b[46].open=85.34228297015305;b[46].high=87.056897538787268;b[46].low=83.20357183702184;b[46].close=84.114902581565829;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 52; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 53; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 54; Python reference side=0
   ArrayResize(b,48);
   b[47].time=14100;b[47].open=84.114902581565829;b[47].high=85.671839192103349;b[47].low=82.401075229111584;b[47].close=84.414355370083456;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 55; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 56; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 57; Python reference side=0
   ArrayResize(b,49);
   b[48].time=14400;b[48].open=84.414355370083456;b[48].high=85.086726602433075;b[48].low=82.539381615318931;b[48].close=84.665277501156822;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 58; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 59; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 60; Python reference side=-1
   ArrayResize(b,50);
   b[49].time=14700;b[49].open=84.665277501156822;b[49].high=85.861339633336755;b[49].low=84.232367607229676;b[49].close=84.30548234431231;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=-1) failures++;
   if(s.bos_index!=46 || MathAbs(s.stop-87.056897538787268)>1e-8 || MathAbs(s.level-85.254466510114)>1e-8) failures++;
   // Fixture 61; Python reference side=0
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 62; Python reference side=0
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 63; Python reference side=0
   ArrayResize(b,44);
   b[0].time=0;b[0].open=100;b[0].high=101.00288941892067;b[0].low=99.471788059753848;b[0].close=100.92796545507548;
   b[1].time=300;b[1].open=100.92796545507548;b[1].high=101.56170448065311;b[1].low=100.0107715233498;b[1].close=100.80954441443673;
   b[2].time=600;b[2].open=100.80954441443673;b[2].high=103.235192591992;b[2].low=99.86706127535885;b[2].close=102.77328765811139;
   b[3].time=900;b[3].open=102.77328765811139;b[3].high=104.44259900264852;b[3].low=99.06029976931886;b[3].close=100.81858330852786;
   b[4].time=1200;b[4].open=100.81858330852786;b[4].high=102.75921169983837;b[4].low=100.35500891401259;b[4].close=100.36715050631022;
   b[5].time=1500;b[5].open=100.36715050631022;b[5].high=101.37142555156507;b[5].low=96.477020591823901;b[5].close=98.446420402711041;
   b[6].time=1800;b[6].open=98.446420402711041;b[6].high=99.325680615013923;b[6].low=98.304106677301547;b[6].close=98.648778392448861;
   b[7].time=2100;b[7].open=98.648778392448861;b[7].high=99.031420378833573;b[7].low=95.858445241047605;b[7].close=97.833571409809068;
   b[8].time=2400;b[8].open=97.833571409809068;b[8].high=100.52619452403295;b[8].low=95.844511998478325;b[8].close=98.737627227982557;
   b[9].time=2700;b[9].open=98.737627227982557;b[9].high=99.163261996525591;b[9].low=97.189622148901861;b[9].close=97.789291069606321;
   b[10].time=3000;b[10].open=97.789291069606321;b[10].high=98.306147071413093;b[10].low=95.551912732788907;b[10].close=96.799956831769833;
   b[11].time=3300;b[11].open=96.799956831769833;b[11].high=98.254052530295851;b[11].low=93.966859860858222;b[11].close=95.521337082581155;
   b[12].time=3600;b[12].open=95.521337082581155;b[12].high=98.104668692805973;b[12].low=94.544096632550861;b[12].close=97.284562212662465;
   b[13].time=3900;b[13].open=97.284562212662465;b[13].high=100.28851673800098;b[13].low=96.110110551082442;b[13].close=98.85600026079436;
   b[14].time=4200;b[14].open=98.85600026079436;b[14].high=102.34429946950308;b[14].low=98.835460520811552;b[14].close=100.4406349961755;
   b[15].time=4500;b[15].open=100.4406349961755;b[15].high=100.95336278850164;b[15].low=98.083271575104831;b[15].close=99.082166409823841;
   b[16].time=4800;b[16].open=99.082166409823841;b[16].high=101.01249831789363;b[16].low=96.155224266608741;b[16].close=97.157528869135731;
   b[17].time=5100;b[17].open=97.157528869135731;b[17].high=97.632126250707032;b[17].low=96.182953807453558;b[17].close=96.640982827897929;
   b[18].time=5400;b[18].open=96.640982827897929;b[18].high=97.359455501223522;b[18].low=93.150874751742307;b[18].close=94.653689915219431;
   b[19].time=5700;b[19].open=94.653689915219431;b[19].high=95.82298104103441;b[19].low=93.993247105633557;b[19].close=95.449783707761725;
   b[20].time=6000;b[20].open=95.449783707761725;b[20].high=95.759873559070996;b[20].low=92.811632443904145;b[20].close=94.187501634800498;
   b[21].time=6300;b[21].open=94.187501634800498;b[21].high=94.80654727170166;b[21].low=93.073606277449542;b[21].close=93.957833267409413;
   b[22].time=6600;b[22].open=93.957833267409413;b[22].high=95.25247961875111;b[22].low=93.550182549337208;b[22].close=94.482173065293637;
   b[23].time=6900;b[23].open=94.482173065293637;b[23].high=95.797798887707245;b[23].low=93.772139256699916;b[23].close=94.053812445945908;
   b[24].time=7200;b[24].open=94.053812445945908;b[24].high=95.202857401467213;b[24].low=93.330941950952337;b[24].close=94.869715928933147;
   b[25].time=7500;b[25].open=94.869715928933147;b[25].high=94.973085991292621;b[25].low=91.806511252542464;b[25].close=93.483891812649944;
   b[26].time=7800;b[26].open=93.483891812649944;b[26].high=95.141242926847426;b[26].low=92.140342149052515;b[26].close=93.724481057139542;
   b[27].time=8100;b[27].open=93.724481057139542;b[27].high=95.43307715224131;b[27].low=92.971615915710942;b[27].close=93.433015593181338;
   b[28].time=8400;b[28].open=93.433015593181338;b[28].high=96.428725635318941;b[28].low=93.413474443151657;b[28].close=95.262370447806603;
   b[29].time=8700;b[29].open=95.262370447806603;b[29].high=96.014149698252893;b[29].low=94.574943343962744;b[29].close=95.583493320924958;
   b[30].time=9000;b[30].open=95.583493320924958;b[30].high=96.486631379427521;b[30].low=92.493726329564339;b[30].close=93.995905166705739;
   b[31].time=9300;b[31].open=93.995905166705739;b[31].high=95.549112419358678;b[31].low=93.118000722856848;b[31].close=94.465223660994511;
   b[32].time=9600;b[32].open=94.465223660994511;b[32].high=96.24529474387252;b[32].low=93.535009249911212;b[32].close=94.358761297258283;
   b[33].time=9900;b[33].open=94.358761297258283;b[33].high=95.468524581430216;b[33].low=93.06027538537208;b[33].close=93.278673198239161;
   b[34].time=10200;b[34].open=93.278673198239161;b[34].high=96.18345391976483;b[34].low=93.103402308354504;b[34].close=94.921201207307959;
   b[35].time=10500;b[35].open=94.921201207307959;b[35].high=98.309660292505441;b[35].low=94.255362672274643;b[35].close=96.600366296232565;
   b[36].time=10800;b[36].open=96.600366296232565;b[36].high=98.096602140187699;b[36].low=94.676817627921906;b[36].close=97.817702601981424;
   b[37].time=11100;b[37].open=97.817702601981424;b[37].high=99.80980569657909;b[37].low=96.094654937709194;b[37].close=98.928861840388691;
   b[38].time=11400;b[38].open=98.928861840388691;b[38].high=100.17704071831852;b[38].low=97.042122456105631;b[38].close=100.05155408302832;
   b[39].time=11700;b[39].open=100.05155408302832;b[39].high=101.26128331839652;b[39].low=98.229902992629263;b[39].close=100.31569921755882;
   b[40].time=12000;b[40].open=100.31569921755882;b[40].high=102.44729373864598;b[40].low=99.598086715912714;b[40].close=100.58703156693183;
   b[41].time=12300;b[41].open=100.58703156693183;b[41].high=103.48539757185512;b[41].low=98.661649385534204;b[41].close=101.91823668725169;
   b[42].time=12600;b[42].open=101.91823668725169;b[42].high=103.29517868651604;b[42].low=100.13016768678851;b[42].close=102.41578934339569;
   b[43].time=12900;b[43].open=102.41578934339569;b[43].high=103.09282297978783;b[43].low=100.63671575945824;b[43].close=101.79362488542787;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 64; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 65; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 66; Python reference side=0
   ArrayResize(b,45);
   b[44].time=13200;b[44].open=101.79362488542787;b[44].high=104.2438330133121;b[44].low=100.72500288741455;b[44].close=103.66648329949828;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 67; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 68; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 69; Python reference side=0
   ArrayResize(b,46);
   b[45].time=13500;b[45].open=103.66648329949828;b[45].high=104.21300199878939;b[45].low=102.00473112026673;b[45].close=103.15944924540244;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 70; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 71; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 72; Python reference side=0
   ArrayResize(b,47);
   b[46].time=13800;b[46].open=103.15944924540244;b[46].high=105.9289001511831;b[46].low=101.9399297199069;b[46].close=105.04512775065997;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 73; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 74; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 75; Python reference side=0
   ArrayResize(b,48);
   b[47].time=14100;b[47].open=105.04512775065997;b[47].high=107.01187373912195;b[47].low=104.77504928907064;b[47].close=106.50374373237392;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 76; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 77; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 78; Python reference side=0
   ArrayResize(b,49);
   b[48].time=14400;b[48].open=106.50374373237392;b[48].high=108.36708704053619;b[48].low=104.11347382458803;b[48].close=104.63664234793103;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 79; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 80; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 81; Python reference side=0
   ArrayResize(b,50);
   b[49].time=14700;b[49].open=104.63664234793103;b[49].high=106.21562295566562;b[49].low=103.32312838760889;b[49].close=105.47117856411754;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 82; Python reference side=0
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 83; Python reference side=1
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=1) failures++;
   if(s.bos_index!=46 || MathAbs(s.stop-101.9399297199069)>1e-8 || MathAbs(s.level-103.48539757185512)>1e-8) failures++;
   // Fixture 84; Python reference side=0
   ArrayResize(b,44);
   b[0].time=0;b[0].open=100;b[0].high=102.97200111647226;b[0].low=98.754445630852601;b[0].close=101.57165001912855;
   b[1].time=300;b[1].open=101.57165001912855;b[1].high=101.80322480566373;b[1].low=98.856519997526576;b[1].close=100.45099624902221;
   b[2].time=600;b[2].open=100.45099624902221;b[2].high=101.86744841890231;b[2].low=98.502785289086432;b[2].close=100.91710636036875;
   b[3].time=900;b[3].open=100.91710636036875;b[3].high=102.24369485154961;b[3].low=98.026533759298118;b[3].close=99.835713676902856;
   b[4].time=1200;b[4].open=99.835713676902856;b[4].high=100.6879945781393;b[4].low=97.991723518248008;b[4].close=100.60764459630977;
   b[5].time=1500;b[5].open=100.60764459630977;b[5].high=102.26085225047507;b[5].low=99.431998321169516;b[5].close=100.93090310839484;
   b[6].time=1800;b[6].open=100.93090310839484;b[6].high=103.11377865173685;b[6].low=100.30989504314626;b[6].close=101.20183037129178;
   b[7].time=2100;b[7].open=101.20183037129178;b[7].high=104.81991823317462;b[7].low=100.49221869383967;b[7].close=103.13649607490021;
   b[8].time=2400;b[8].open=103.13649607490021;b[8].high=104.1098451271302;b[8].low=101.52303226207869;b[8].close=102.71137876721096;
   b[9].time=2700;b[9].open=102.71137876721096;b[9].high=104.22262072761053;b[9].low=101.16575301090208;b[9].close=101.41129006886133;
   b[10].time=3000;b[10].open=101.41129006886133;b[10].high=103.29315964388169;b[10].low=98.763215967260166;b[10].close=100.40603925097643;
   b[11].time=3300;b[11].open=100.40603925097643;b[11].high=100.62578261658001;b[11].low=98.469314206372289;b[11].close=98.954242868786409;
   b[12].time=3600;b[12].open=98.954242868786409;b[12].high=99.923443128525292;b[12].low=97.493967116761581;b[12].close=97.918904307642833;
   b[13].time=3900;b[13].open=97.918904307642833;b[13].high=101.37121191129197;b[13].low=97.209134255348602;b[13].close=99.863582947404893;
   b[14].time=4200;b[14].open=99.863582947404893;b[14].high=103.82123711123003;b[14].low=99.533230623669908;b[14].close=101.85741236575822;
   b[15].time=4500;b[15].open=101.85741236575822;b[15].high=104.98143363028316;b[15].low=100.97977028472089;b[15].close=103.78273368329972;
   b[16].time=4800;b[16].open=103.78273368329972;b[16].high=103.95333717983785;b[16].low=102.02268121517034;b[16].close=102.08371793385018;
   b[17].time=5100;b[17].open=102.08371793385018;b[17].high=104.09925542076779;b[17].low=101.39553610395865;b[17].close=102.83709485014398;
   b[18].time=5400;b[18].open=102.83709485014398;b[18].high=104.22552776095046;b[18].low=100.60614365763095;b[18].close=101.90299447170881;
   b[19].time=5700;b[19].open=101.90299447170881;b[19].high=103.32214429764633;b[19].low=101.77312779420897;b[19].close=102.11353236753123;
   b[20].time=6000;b[20].open=102.11353236753123;b[20].high=104.42550057818126;b[20].low=100.65318463098815;b[20].close=102.87541516516249;
   b[21].time=6300;b[21].open=102.87541516516249;b[21].high=102.89926819802589;b[21].low=101.09177251241066;b[21].close=102.86439008068751;
   b[22].time=6600;b[22].open=102.86439008068751;b[22].high=104.43910736198578;b[22].low=101.28133575192233;b[22].close=102.28547658877804;
   b[23].time=6900;b[23].open=102.28547658877804;b[23].high=104.07823011864197;b[23].low=100.1226692108452;b[23].close=101.67348054793042;
   b[24].time=7200;b[24].open=101.67348054793042;b[24].high=104.53127017841339;b[24].low=100.87772375477134;b[24].close=103.36411700330335;
   b[25].time=7500;b[25].open=103.36411700330335;b[25].high=105.06578393541177;b[25].low=102.16625701816079;b[25].close=102.25124059169976;
   b[26].time=7800;b[26].open=102.25124059169976;b[26].high=102.84905231523558;b[26].low=101.02366904350302;b[26].close=102.01473912326763;
   b[27].time=8100;b[27].open=102.01473912326763;b[27].high=103.56184130553773;b[27].low=101.60817270672928;b[27].close=103.34195497890448;
   b[28].time=8400;b[28].open=103.34195497890448;b[28].high=104.4008277443258;b[28].low=100.91750931856392;b[28].close=101.94365682583798;
   b[29].time=8700;b[29].open=101.94365682583798;b[29].high=105.03933728468;b[29].low=101.72085792800262;b[29].close=103.14457005752161;
   b[30].time=9000;b[30].open=103.14457005752161;b[30].high=103.99897099507263;b[30].low=100.09348949984944;b[30].close=101.60839098473225;
   b[31].time=9300;b[31].open=101.60839098473225;b[31].high=102.82854791943301;b[31].low=98.840988145769103;b[31].close=100.00838286973072;
   b[32].time=9600;b[32].open=100.00838286973072;b[32].high=101.54817445840332;b[32].low=98.493421009432851;b[32].close=100.6882664932054;
   b[33].time=9900;b[33].open=100.6882664932054;b[33].high=101.64014791208943;b[33].low=99.727808932068612;b[33].close=100.49887737345038;
   b[34].time=10200;b[34].open=100.49887737345038;b[34].high=100.63858690209919;b[34].low=98.375479395734374;b[34].close=100.30535617930792;
   b[35].time=10500;b[35].open=100.30535617930792;b[35].high=101.76635172312291;b[35].low=98.016974021434436;b[35].close=98.305688662621321;
   b[36].time=10800;b[36].open=98.305688662621321;b[36].high=98.686009935034576;b[36].low=97.177233999375858;b[36].close=98.081818750856257;
   b[37].time=11100;b[37].open=98.081818750856257;b[37].high=101.43147165337516;b[37].low=97.907670156742427;b[37].close=99.847556665394563;
   b[38].time=11400;b[38].open=99.847556665394563;b[38].high=101.93607751556422;b[38].low=98.129605710603244;b[38].close=100.48031646957756;
   b[39].time=11700;b[39].open=100.48031646957756;b[39].high=101.28936108889984;b[39].low=98.500973180479107;b[39].close=100.01676608102629;
   b[40].time=12000;b[40].open=100.01676608102629;b[40].high=100.70612811375858;b[40].low=98.615320019619688;b[40].close=100.50104531777595;
   b[41].time=12300;b[41].open=100.50104531777595;b[41].high=102.43702921561211;b[41].low=99.966118895069997;b[41].close=100.01918655376238;
   b[42].time=12600;b[42].open=100.01918655376238;b[42].high=100.91265059284358;b[42].low=98.590467444476346;b[42].close=99.676275593589224;
   b[43].time=12900;b[43].open=99.676275593589224;b[43].high=101.32278421925911;b[43].low=98.504689895571573;b[43].close=101.30911554305726;
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 85; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 86; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 87; Python reference side=0
   ArrayResize(b,45);
   b[44].time=13200;b[44].open=101.30911554305726;b[44].high=102.41204656207137;b[44].low=99.809578222295443;b[44].close=100.5494412896693;
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 88; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 89; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 90; Python reference side=0
   ArrayResize(b,46);
   b[45].time=13500;b[45].open=100.5494412896693;b[45].high=103.94443316547829;b[45].low=99.179219492214386;b[45].close=102.08960339210154;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 91; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 92; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 93; Python reference side=0
   ArrayResize(b,47);
   b[46].time=13800;b[46].open=102.08960339210154;b[46].high=105.91805244752861;b[46].low=101.24013489765576;b[46].close=104.04979198455793;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 94; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 95; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 96; Python reference side=0
   ArrayResize(b,48);
   b[47].time=14100;b[47].open=104.04979198455793;b[47].high=104.93761593341431;b[47].low=103.82096234521165;b[47].close=104.86544430011298;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 97; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 98; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 99; Python reference side=0
   ArrayResize(b,49);
   b[48].time=14400;b[48].open=104.86544430011298;b[48].high=105.47254260285429;b[48].low=102.72748529060077;b[48].close=103.95037263728624;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 100; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 101; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 102; Python reference side=0
   ArrayResize(b,50);
   b[49].time=14700;b[49].open=103.95037263728624;b[49].high=106.29040700137332;b[49].low=102.17021771275277;b[49].close=104.86859679931652;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 103; Python reference side=0
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 104; Python reference side=1
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=1) failures++;
   if(s.bos_index!=46 || MathAbs(s.stop-101.24013489765576)>1e-8 || MathAbs(s.level-102.43702921561211)>1e-8) failures++;
   // Fixture 105; Python reference side=0
   ArrayResize(b,44);
   b[0].time=0;b[0].open=100;b[0].high=101.04934702149716;b[0].low=98.940443435802962;b[0].close=100.44944295944823;
   b[1].time=300;b[1].open=100.44944295944823;b[1].high=101.55619243817695;b[1].low=99.013423759773247;b[1].close=100.02287756951641;
   b[2].time=600;b[2].open=100.02287756951641;b[2].high=100.05165778311761;b[2].low=99.33286791784829;b[2].close=99.402032108883418;
   b[3].time=900;b[3].open=99.402032108883418;b[3].high=101.48359783066098;b[3].low=99.26458033434173;b[3].close=99.652332436208681;
   b[4].time=1200;b[4].open=99.652332436208681;b[4].high=102.04847755060342;b[4].low=99.407277691663097;b[4].close=100.35686522979005;
   b[5].time=1500;b[5].open=100.35686522979005;b[5].high=101.66891523319565;b[5].low=97.244257152851247;b[5].close=98.620895901635933;
   b[6].time=1800;b[6].open=98.620895901635933;b[6].high=100.92716671883367;b[6].low=98.258133554585143;b[6].close=99.393000996873823;
   b[7].time=2100;b[7].open=99.393000996873823;b[7].high=100.70529747207567;b[7].low=96.156623669273756;b[7].close=97.494255929029123;
   b[8].time=2400;b[8].open=97.494255929029123;b[8].high=98.536390688133025;b[8].low=95.458239902331627;b[8].close=96.192915434671789;
   b[9].time=2700;b[9].open=96.192915434671789;b[9].high=96.494443041506628;b[9].low=95.590319388949155;b[9].close=96.18444470672506;
   b[10].time=3000;b[10].open=96.18444470672506;b[10].high=96.598775966895658;b[10].low=92.849440531882067;b[10].close=94.749814938151701;
   b[11].time=3300;b[11].open=94.749814938151701;b[11].high=98.013873882392801;b[11].low=93.311566476754962;b[11].close=96.727747317145997;
   b[12].time=3600;b[12].open=96.727747317145997;b[12].high=100.63574305888793;b[12].low=95.829097149383585;b[12].close=98.723026817877184;
   b[13].time=3900;b[13].open=98.723026817877184;b[13].high=100.46272699740292;b[13].low=96.703008419889798;b[13].close=98.588066660538473;
   b[14].time=4200;b[14].open=98.588066660538473;b[14].high=100.18773337321906;b[14].low=96.914247463175172;b[14].close=97.671186711555947;
   b[15].time=4500;b[15].open=97.671186711555947;b[15].high=98.463881830059321;b[15].low=96.458827496954328;b[15].close=97.836354481555574;
   b[16].time=4800;b[16].open=97.836354481555574;b[16].high=100.95626034805431;b[16].low=96.715243930466883;b[16].close=99.56383616654162;
   b[17].time=5100;b[17].open=99.56383616654162;b[17].high=100.43579949753754;b[17].low=98.056541903085503;b[17].close=99.397549928597101;
   b[18].time=5400;b[18].open=99.397549928597101;b[18].high=101.09608072753646;b[18].low=98.390330460989915;b[18].close=99.335808429600974;
   b[19].time=5700;b[19].open=99.335808429600974;b[19].high=100.42783427118631;b[19].low=98.543407306589017;b[19].close=99.326402922436259;
   b[20].time=6000;b[20].open=99.326402922436259;b[20].high=102.06606365680808;b[20].low=97.8499078180417;b[20].close=100.34372061194934;
   b[21].time=6300;b[21].open=100.34372061194934;b[21].high=100.65579853859207;b[21].low=97.295060756268896;b[21].close=98.675307909479272;
   b[22].time=6600;b[22].open=98.675307909479272;b[22].high=99.059898885341084;b[22].low=97.693265652611373;b[22].close=97.965907053168593;
   b[23].time=6900;b[23].open=97.965907053168593;b[23].high=101.19065500878213;b[23].low=97.521500584594222;b[23].close=99.288146873968884;
   b[24].time=7200;b[24].open=99.288146873968884;b[24].high=100.05258845685364;b[24].low=97.226764549182079;b[24].close=98.333985216724912;
   b[25].time=7500;b[25].open=98.333985216724912;b[25].high=100.52104680061785;b[25].low=97.845094604282295;b[25].close=99.149482846027539;
   b[26].time=7800;b[26].open=99.149482846027539;b[26].high=101.51989101052745;b[26].low=98.372814026128765;b[26].close=99.981830571317531;
   b[27].time=8100;b[27].open=99.981830571317531;b[27].high=100.83290545501282;b[27].low=97.267369282557667;b[27].close=98.143162197086582;
   b[28].time=8400;b[28].open=98.143162197086582;b[28].high=99.491740511109029;b[28].low=97.048051533220416;b[28].close=98.762251943865024;
   b[29].time=8700;b[29].open=98.762251943865024;b[29].high=98.817516852580184;b[29].low=96.603270174979627;b[29].close=97.371468535306761;
   b[30].time=9000;b[30].open=97.371468535306761;b[30].high=97.869668387323529;b[30].low=95.067987328441674;b[30].close=96.738036472848563;
   b[31].time=9300;b[31].open=96.738036472848563;b[31].high=97.637099266340385;b[31].low=94.134834019937159;b[31].close=95.765576254958276;
   b[32].time=9600;b[32].open=95.765576254958276;b[32].high=97.65994471112792;b[32].low=93.41874329390815;b[32].close=94.699011956699664;
   b[33].time=9900;b[33].open=94.699011956699664;b[33].high=96.454294692232153;b[33].low=92.943388672537296;b[33].close=94.076168652121098;
   b[34].time=10200;b[34].open=94.076168652121098;b[34].high=95.508350776415369;b[34].low=92.092197888729785;b[34].close=93.586631942552017;
   b[35].time=10500;b[35].open=93.586631942552017;b[35].high=94.825761822344646;b[35].low=91.605879344519508;b[35].close=93.909350767954948;
   b[36].time=10800;b[36].open=93.909350767954948;b[36].high=94.499977776258461;b[36].low=91.775479173170211;b[36].close=93.076668814722353;
   b[37].time=11100;b[37].open=93.076668814722353;b[37].high=93.979548679037023;b[37].low=91.440096943986532;b[37].close=93.564171417335146;
   b[38].time=11400;b[38].open=93.564171417335146;b[38].high=95.054918551978446;b[38].low=91.966196154899137;b[38].close=95.034529861170142;
   b[39].time=11700;b[39].open=95.034529861170142;b[39].high=97.543029261746923;b[39].low=94.273180047005667;b[39].close=96.68019356149;
   b[40].time=12000;b[40].open=96.68019356149;b[40].high=97.212364159965787;b[40].low=94.996971918866464;b[40].close=96.995505974490129;
   b[41].time=12300;b[41].open=96.995505974490129;b[41].high=97.068315324481347;b[41].low=96.497930999709538;b[41].close=96.6359744504758;
   b[42].time=12600;b[42].open=96.6359744504758;b[42].high=97.426326688253283;b[42].low=94.480198351950051;b[42].close=95.106358387144439;
   b[43].time=12900;b[43].open=95.106358387144439;b[43].high=96.148580984048252;b[43].low=91.375179619206691;b[43].close=93.20245826216825;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 106; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 107; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 108; Python reference side=0
   ArrayResize(b,45);
   b[44].time=13200;b[44].open=93.20245826216825;b[44].high=95.229284056746025;b[44].low=92.467943084620856;b[44].close=94.019793426613376;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 109; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 110; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 111; Python reference side=0
   ArrayResize(b,46);
   b[45].time=13500;b[45].open=94.019793426613376;b[45].high=94.906093760244048;b[45].low=92.506133248352512;b[45].close=93.062943454421543;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 112; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 113; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 114; Python reference side=0
   ArrayResize(b,47);
   b[46].time=13800;b[46].open=93.062943454421543;b[46].high=93.819234215491079;b[46].low=90.851938781560804;b[46].close=91.400186390258867;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 115; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 116; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 117; Python reference side=0
   ArrayResize(b,48);
   b[47].time=14100;b[47].open=91.400186390258867;b[47].high=91.568618189205608;b[47].low=89.141166505504984;b[47].close=89.929480219838752;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 118; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 119; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 120; Python reference side=0
   ArrayResize(b,49);
   b[48].time=14400;b[48].open=89.929480219838752;b[48].high=91.156428706564611;b[48].low=87.976210051258505;b[48].close=90.59070273005922;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 121; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 122; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 123; Python reference side=-1
   ArrayResize(b,50);
   b[49].time=14700;b[49].open=90.59070273005922;b[49].high=92.474843988612733;b[49].low=87.956861726322288;b[49].close=89.763325745333418;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=-1) failures++;
   if(s.bos_index!=47 || MathAbs(s.stop-92.474843988612733)>1e-8 || MathAbs(s.level-91.375179619206691)>1e-8) failures++;
   // Fixture 124; Python reference side=0
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 125; Python reference side=0
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 126; Python reference side=0
   ArrayResize(b,44);
   b[0].time=0;b[0].open=100;b[0].high=100.41594400823917;b[0].low=98.05104804334259;b[0].close=100.2173092785653;
   b[1].time=300;b[1].open=100.2173092785653;b[1].high=102.77865275036589;b[1].low=98.426634356524659;b[1].close=101.88947617065799;
   b[2].time=600;b[2].open=101.88947617065799;b[2].high=103.55501995454992;b[2].low=99.674817083485195;b[2].close=101.17175776601745;
   b[3].time=900;b[3].open=101.17175776601745;b[3].high=102.90259901721799;b[3].low=100.77198499051754;b[3].close=100.95574726359199;
   b[4].time=1200;b[4].open=100.95574726359199;b[4].high=102.33812443318621;b[4].low=99.861630431061485;b[4].close=100.39327275656056;
   b[5].time=1500;b[5].open=100.39327275656056;b[5].high=101.00320595662531;b[5].low=98.815576676406181;b[5].close=100.36664217560295;
   b[6].time=1800;b[6].open=100.36664217560295;b[6].high=101.04021594923898;b[6].low=98.709500828129592;b[6].close=99.688827484146842;
   b[7].time=2100;b[7].open=99.688827484146842;b[7].high=100.4387844679438;b[7].low=96.040165402018474;b[7].close=97.724650110834489;
   b[8].time=2400;b[8].open=97.724650110834489;b[8].high=98.365927744994323;b[8].low=95.119536405811047;b[8].close=96.283654759104365;
   b[9].time=2700;b[9].open=96.283654759104365;b[9].high=96.737484193226805;b[9].low=93.117096829249988;b[9].close=94.419192308486458;
   b[10].time=3000;b[10].open=94.419192308486458;b[10].high=95.622694413093285;b[10].low=93.623351638972224;b[10].close=95.041978563588486;
   b[11].time=3300;b[11].open=95.041978563588486;b[11].high=96.888074770938061;b[11].low=91.332081342737766;b[11].close=93.098454899749314;
   b[12].time=3600;b[12].open=93.098454899749314;b[12].high=95.011718729027777;b[12].low=92.459945774244105;b[12].close=93.933538208173275;
   b[13].time=3900;b[13].open=93.933538208173275;b[13].high=94.173796277127778;b[13].low=92.933901553180235;b[13].close=93.455481337735236;
   b[14].time=4200;b[14].open=93.455481337735236;b[14].high=95.27732518426248;b[14].low=92.718569303124525;b[14].close=95.059251563227775;
   b[15].time=4500;b[15].open=95.059251563227775;b[15].high=98.132814211626197;b[15].low=93.429553687076393;b[15].close=97.029073073870975;
   b[16].time=4800;b[16].open=97.029073073870975;b[16].high=97.365993216695529;b[16].low=95.019061010030185;b[16].close=95.463866153812603;
   b[17].time=5100;b[17].open=95.463866153812603;b[17].high=97.207172264117048;b[17].low=95.08215446206971;b[17].close=96.504293601544802;
   b[18].time=5400;b[18].open=96.504293601544802;b[18].high=97.434101648414227;b[18].low=95.196643442280646;b[18].close=95.569212001732353;
   b[19].time=5700;b[19].open=95.569212001732353;b[19].high=97.141640869138556;b[19].low=94.024023207883459;b[19].close=94.098440928383852;
   b[20].time=6000;b[20].open=94.098440928383852;b[20].high=94.284497131412891;b[20].low=91.969744260466854;b[20].close=93.441919029732233;
   b[21].time=6300;b[21].open=93.441919029732233;b[21].high=95.747063529328145;b[21].low=92.277845672450908;b[21].close=94.831017300764529;
   b[22].time=6600;b[22].open=94.831017300764529;b[22].high=96.582414363241782;b[22].low=92.759078791906134;b[22].close=94.508715743872159;
   b[23].time=6900;b[23].open=94.508715743872159;b[23].high=94.881446318678883;b[23].low=93.291442504301429;b[23].close=94.425290522279482;
   b[24].time=7200;b[24].open=94.425290522279482;b[24].high=96.780899704353672;b[24].low=94.214157593134715;b[24].close=96.074267087375787;
   b[25].time=7500;b[25].open=96.074267087375787;b[25].high=96.677792945688239;b[25].low=94.824432888726847;b[25].close=96.074906593398936;
   b[26].time=7800;b[26].open=96.074906593398936;b[26].high=96.386903219924505;b[26].low=93.588656631394102;b[26].close=94.449208037211477;
   b[27].time=8100;b[27].open=94.449208037211477;b[27].high=95.368931956434849;b[27].low=94.133242162427322;b[27].close=94.379853321095041;
   b[28].time=8400;b[28].open=94.379853321095041;b[28].high=96.131978121741071;b[28].low=91.104617921056928;b[28].close=92.435042292498935;
   b[29].time=8700;b[29].open=92.435042292498935;b[29].high=94.020243806460982;b[29].low=90.873362084682228;b[29].close=93.817398317106139;
   b[30].time=9000;b[30].open=93.817398317106139;b[30].high=95.332087616989568;b[30].low=93.032641813062938;b[30].close=94.825769728440591;
   b[31].time=9300;b[31].open=94.825769728440591;b[31].high=98.457216831181583;b[31].low=93.207153590145253;b[31].close=96.616705896431966;
   b[32].time=9600;b[32].open=96.616705896431966;b[32].high=98.836138608167161;b[32].low=94.953666280181068;b[32].close=97.975887823834782;
   b[33].time=9900;b[33].open=97.975887823834782;b[33].high=99.486525005384351;b[33].low=96.676283557947741;b[33].close=98.828848748312126;
   b[34].time=10200;b[34].open=98.828848748312126;b[34].high=100.55010168794114;b[34].low=98.072432295022637;b[34].close=98.555706887289034;
   b[35].time=10500;b[35].open=98.555706887289034;b[35].high=100.17899559274555;b[35].low=95.61674083047113;b[35].close=97.194100080045132;
   b[36].time=10800;b[36].open=97.194100080045132;b[36].high=99.068065831612117;b[36].low=94.877746845234242;b[36].close=96.203379217760485;
   b[37].time=11100;b[37].open=96.203379217760485;b[37].high=98.374367703293132;b[37].low=95.524692324098041;b[37].close=96.594201774750573;
   b[38].time=11400;b[38].open=96.594201774750573;b[38].high=97.512392409520373;b[38].low=94.709083728524192;b[38].close=97.04373372900443;
   b[39].time=11700;b[39].open=97.04373372900443;b[39].high=98.991132329987565;b[39].low=95.393001454383352;b[39].close=98.280714271827648;
   b[40].time=12000;b[40].open=98.280714271827648;b[40].high=98.879168225730965;b[40].low=95.638052822157192;b[40].close=96.698141355050183;
   b[41].time=12300;b[41].open=96.698141355050183;b[41].high=99.245962795767838;b[41].low=96.057696315842904;b[41].close=97.549810226267383;
   b[42].time=12600;b[42].open=97.549810226267383;b[42].high=98.221682492046824;b[42].low=95.469338015253413;b[42].close=97.00927500512384;
   b[43].time=12900;b[43].open=97.00927500512384;b[43].high=97.196065590187956;b[43].low=94.699689376933435;b[43].close=95.137675168412514;
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 127; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 128; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 129; Python reference side=0
   ArrayResize(b,45);
   b[44].time=13200;b[44].open=95.137675168412514;b[44].high=96.190930381179555;b[44].low=95.030604311312388;b[44].close=95.822033996215211;
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 130; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 131; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 132; Python reference side=0
   ArrayResize(b,46);
   b[45].time=13500;b[45].open=95.822033996215211;b[45].high=96.104679766389864;b[45].low=92.386345331730425;b[45].close=94.078080350449028;
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 133; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 134; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 135; Python reference side=0
   ArrayResize(b,47);
   b[46].time=13800;b[46].open=94.078080350449028;b[46].high=95.092997610562037;b[46].low=93.240531192710861;b[46].close=94.285495548466969;
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 136; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 137; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 138; Python reference side=0
   ArrayResize(b,48);
   b[47].time=14100;b[47].open=94.285495548466969;b[47].high=95.43324803968261;b[47].low=93.395590582270799;b[47].close=93.773257855303683;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 139; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 140; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 141; Python reference side=0
   ArrayResize(b,49);
   b[48].time=14400;b[48].open=93.773257855303683;b[48].high=94.192178431090397;b[48].low=90.742480469104436;b[48].close=91.998370783121587;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 142; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 143; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 144; Python reference side=-1
   ArrayResize(b,50);
   b[49].time=14700;b[49].open=91.998370783121587;b[49].high=93.688235343600667;b[49].low=90.832606942440208;b[49].close=91.31581533596912;
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=-1) failures++;
   if(s.bos_index!=48 || MathAbs(s.stop-94.192178431090397)>1e-8 || MathAbs(s.level-92.386345331730425)>1e-8) failures++;
   // Fixture 145; Python reference side=0
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 146; Python reference side=0
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=-1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 147; Python reference side=0
   ArrayResize(b,44);
   b[0].time=0;b[0].open=100;b[0].high=101.81941978185669;b[0].low=98.272876299620521;b[0].close=99.85276271892468;
   b[1].time=300;b[1].open=99.85276271892468;b[1].high=100.91408760118608;b[1].low=98.847783939877857;b[1].close=100.39188312178709;
   b[2].time=600;b[2].open=100.39188312178709;b[2].high=100.56167774749275;b[2].low=99.236243268046366;b[2].close=99.706952636051327;
   b[3].time=900;b[3].open=99.706952636051327;b[3].high=100.44748582249917;b[3].low=96.865102274465372;b[3].close=97.868757135234816;
   b[4].time=1200;b[4].open=97.868757135234816;b[4].high=99.229398136782748;b[4].low=95.948918003364824;b[4].close=96.972787032036919;
   b[5].time=1500;b[5].open=96.972787032036919;b[5].high=97.26026361238678;b[5].low=96.039472206474002;b[5].close=97.054261831940323;
   b[6].time=1800;b[6].open=97.054261831940323;b[6].high=98.202046368198083;b[6].low=95.358957513769695;b[6].close=97.021634954399232;
   b[7].time=2100;b[7].open=97.021634954399232;b[7].high=99.634689978929501;b[7].low=95.893099752989428;b[7].close=97.878522899643457;
   b[8].time=2400;b[8].open=97.878522899643457;b[8].high=99.305863433763804;b[8].low=95.61458556463613;b[8].close=97.291546991568993;
   b[9].time=2700;b[9].open=97.291546991568993;b[9].high=99.730393917215835;b[9].low=95.537122416417262;b[9].close=99.146781119186301;
   b[10].time=3000;b[10].open=99.146781119186301;b[10].high=102.05192902028631;b[10].low=97.713992652813644;b[10].close=100.65795526958259;
   b[11].time=3300;b[11].open=100.65795526958259;b[11].high=101.66120740469061;b[11].low=99.832455104402726;b[11].close=101.36101496470609;
   b[12].time=3600;b[12].open=101.36101496470609;b[12].high=104.83405712616737;b[12].low=99.63434568671488;b[12].close=103.21860380984266;
   b[13].time=3900;b[13].open=103.21860380984266;b[13].high=104.01674859709807;b[13].low=101.47756777488985;b[13].close=103.87984117268743;
   b[14].time=4200;b[14].open=103.87984117268743;b[14].high=104.82002502143915;b[14].low=103.72667817537834;b[14].close=104.43653436114181;
   b[15].time=4500;b[15].open=104.43653436114181;b[15].high=106.21130102844106;b[15].low=103.44835189723618;b[15].close=104.28188305158878;
   b[16].time=4800;b[16].open=104.28188305158878;b[16].high=107.03551458892971;b[16].low=102.49976643872075;b[16].close=105.66600264595307;
   b[17].time=5100;b[17].open=105.66600264595307;b[17].high=106.88373131693956;b[17].low=103.10592433626435;b[17].close=104.49975847857334;
   b[18].time=5400;b[18].open=104.49975847857334;b[18].high=105.73082341373268;b[18].low=101.70275428040746;b[18].close=103.4554525193937;
   b[19].time=5700;b[19].open=103.4554525193937;b[19].high=104.75587893093511;b[19].low=102.05403157015265;b[19].close=102.82788377693601;
   b[20].time=6000;b[20].open=102.82788377693601;b[20].high=103.38052021670006;b[20].low=99.84450523755369;b[20].close=101.17830579945858;
   b[21].time=6300;b[21].open=101.17830579945858;b[21].high=105.13005720592237;b[21].low=101.06104714605256;b[21].close=103.14747550705172;
   b[22].time=6600;b[22].open=103.14747550705172;b[22].high=105.84891381837006;b[22].low=102.16000642615842;b[22].close=104.32110521773316;
   b[23].time=6900;b[23].open=104.32110521773316;b[23].high=104.3514011187939;b[23].low=103.0753062735764;b[23].close=103.07622823731366;
   b[24].time=7200;b[24].open=103.07622823731366;b[24].high=103.3248850171734;b[24].low=100.8369947493005;b[24].close=102.4835681632847;
   b[25].time=7500;b[25].open=102.4835681632847;b[25].high=103.84120930631515;b[25].low=101.34607397404947;b[25].close=103.01559091242228;
   b[26].time=7800;b[26].open=103.01559091242228;b[26].high=104.15119405855296;b[26].low=100.29498906165992;b[26].close=101.27188324617845;
   b[27].time=8100;b[27].open=101.27188324617845;b[27].high=103.23041396994229;b[27].low=97.631307236866121;b[27].close=99.303652176783217;
   b[28].time=8400;b[28].open=99.303652176783217;b[28].high=100.46564380054997;b[28].low=97.213050624281948;b[28].close=98.625155917160001;
   b[29].time=8700;b[29].open=98.625155917160001;b[29].high=100.47932826017515;b[29].low=95.975467282503814;b[29].close=97.060159270736733;
   b[30].time=9000;b[30].open=97.060159270736733;b[30].high=99.041228526305716;b[30].low=96.845450783555805;b[30].close=98.595467207627394;
   b[31].time=9300;b[31].open=98.595467207627394;b[31].high=99.756210671052258;b[31].low=98.22940139280368;b[31].close=99.6120882734742;
   b[32].time=9600;b[32].open=99.6120882734742;b[32].high=101.61293916991001;b[32].low=99.153359443172121;b[32].close=100.52738993568552;
   b[33].time=9900;b[33].open=100.52738993568552;b[33].high=102.08458050849619;b[33].low=98.164313297168718;b[33].close=99.004332672476608;
   b[34].time=10200;b[34].open=99.004332672476608;b[34].high=99.632437677437011;b[34].low=97.187333911126203;b[34].close=98.812437506654206;
   b[35].time=10500;b[35].open=98.812437506654206;b[35].high=99.523859643777371;b[35].low=96.942544819109983;b[35].close=98.493952261422805;
   b[36].time=10800;b[36].open=98.493952261422805;b[36].high=98.633635994928611;b[36].low=96.343413461067328;b[36].close=97.617664546230245;
   b[37].time=11100;b[37].open=97.617664546230245;b[37].high=99.474283854719246;b[37].low=96.655794959108476;b[37].close=99.162725167155472;
   b[38].time=11400;b[38].open=99.162725167155472;b[38].high=101.12485064645976;b[38].low=97.663391449766692;b[38].close=98.742680985344222;
   b[39].time=11700;b[39].open=98.742680985344222;b[39].high=100.54426175144854;b[39].low=97.61327947351397;b[39].close=99.454450476267567;
   b[40].time=12000;b[40].open=99.454450476267567;b[40].high=101.06297356210931;b[40].low=97.806935190769963;b[40].close=100.51335810532012;
   b[41].time=12300;b[41].open=100.51335810532012;b[41].high=102.68615877613229;b[41].low=100.1417659075143;b[41].close=102.17738889585843;
   b[42].time=12600;b[42].open=102.17738889585843;b[42].high=104.4033306206574;b[42].low=101.06744015128798;b[42].close=104.12456300275549;
   b[43].time=12900;b[43].open=104.12456300275549;b[43].high=105.93946467369604;b[43].low=102.71317392571807;b[43].close=105.78132179594911;
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 148; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 149; Python reference side=0
   ArrayResize(b,44);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 150; Python reference side=0
   ArrayResize(b,45);
   b[44].time=13200;b[44].open=105.78132179594911;b[44].high=107.97102942132597;b[44].low=105.38996169026208;b[44].close=106.37751885510765;
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 151; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 152; Python reference side=0
   ArrayResize(b,45);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 153; Python reference side=0
   ArrayResize(b,46);
   b[45].time=13500;b[45].open=106.37751885510765;b[45].high=106.52531584087761;b[45].low=103.97086763307267;b[45].close=104.57855917479763;
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 154; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 155; Python reference side=0
   ArrayResize(b,46);
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 156; Python reference side=0
   ArrayResize(b,47);
   b[46].time=13800;b[46].open=104.57855917479763;b[46].high=107.85092753822912;b[46].low=102.79864742861764;b[46].close=106.04560292452472;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 157; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 158; Python reference side=0
   ArrayResize(b,47);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 159; Python reference side=0
   ArrayResize(b,48);
   b[47].time=14100;b[47].open=106.04560292452472;b[47].high=108.44976148298248;b[47].low=104.2208814364956;b[47].close=107.7969904876685;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 160; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 161; Python reference side=0
   ArrayResize(b,48);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 162; Python reference side=0
   ArrayResize(b,49);
   b[48].time=14400;b[48].open=107.7969904876685;b[48].high=110.16710914230667;b[48].low=106.4067501793008;b[48].close=108.31895521571394;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 163; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 164; Python reference side=0
   ArrayResize(b,49);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   // Fixture 165; Python reference side=0
   ArrayResize(b,50);
   b[49].time=14700;b[49].open=108.31895521571394;b[49].high=109.74732139380505;b[49].low=106.38906386938402;b[49].close=109.58918919300693;
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,-1,s);
   if(s.side!=0) failures++;
   // Fixture 166; Python reference side=0
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,0,s);
   if(s.side!=0) failures++;
   // Fixture 167; Python reference side=1
   ArrayResize(b,50);
   if(Structure(b,ArraySize(b),2,hi,lo)!=1) failures++;
   FindSetup(b,1,s);
   if(s.side!=1) failures++;
   if(s.bos_index!=48 || MathAbs(s.stop-106.38906386938402)>1e-8 || MathAbs(s.level-107.97102942132597)>1e-8) failures++;
   // Fixture 168; Python reference side=0
   ArrayResize(b,50);
   b[0].time=0;b[0].open=100;b[0].high=101;b[0].low=99;b[0].close=100;
   b[1].time=300;b[1].open=100;b[1].high=101;b[1].low=99;b[1].close=100;
   b[2].time=600;b[2].open=100;b[2].high=101;b[2].low=99;b[2].close=100;
   b[3].time=900;b[3].open=100;b[3].high=101;b[3].low=99;b[3].close=100;
   b[4].time=1200;b[4].open=100;b[4].high=101;b[4].low=99;b[4].close=100;
   b[5].time=1500;b[5].open=100;b[5].high=101;b[5].low=99;b[5].close=100;
   b[6].time=1800;b[6].open=100;b[6].high=101;b[6].low=99;b[6].close=100;
   b[7].time=2100;b[7].open=100;b[7].high=101;b[7].low=99;b[7].close=100;
   b[8].time=2400;b[8].open=100;b[8].high=101;b[8].low=99;b[8].close=100;
   b[9].time=2700;b[9].open=100;b[9].high=101;b[9].low=99;b[9].close=100;
   b[10].time=3000;b[10].open=100;b[10].high=101;b[10].low=99;b[10].close=100;
   b[11].time=3300;b[11].open=100;b[11].high=101;b[11].low=99;b[11].close=100;
   b[12].time=3600;b[12].open=100;b[12].high=101;b[12].low=99;b[12].close=100;
   b[13].time=3900;b[13].open=100;b[13].high=101;b[13].low=99;b[13].close=100;
   b[14].time=4200;b[14].open=100;b[14].high=101;b[14].low=99;b[14].close=100;
   b[15].time=4500;b[15].open=100;b[15].high=101;b[15].low=99;b[15].close=100;
   b[16].time=4800;b[16].open=100;b[16].high=101;b[16].low=99;b[16].close=100;
   b[17].time=5100;b[17].open=100;b[17].high=101;b[17].low=99;b[17].close=100;
   b[18].time=5400;b[18].open=100;b[18].high=101;b[18].low=99;b[18].close=100;
   b[19].time=5700;b[19].open=100;b[19].high=101;b[19].low=99;b[19].close=100;
   b[20].time=6000;b[20].open=100;b[20].high=101;b[20].low=99;b[20].close=100;
   b[21].time=6300;b[21].open=100;b[21].high=101;b[21].low=99;b[21].close=100;
   b[22].time=6600;b[22].open=100;b[22].high=101;b[22].low=99;b[22].close=100;
   b[23].time=6900;b[23].open=100;b[23].high=101;b[23].low=99;b[23].close=100;
   b[24].time=7200;b[24].open=100;b[24].high=101;b[24].low=99;b[24].close=100;
   b[25].time=7500;b[25].open=100;b[25].high=101;b[25].low=99;b[25].close=100;
   b[26].time=7800;b[26].open=100;b[26].high=101;b[26].low=99;b[26].close=100;
   b[27].time=8100;b[27].open=100;b[27].high=101;b[27].low=99;b[27].close=100;
   b[28].time=8400;b[28].open=100;b[28].high=101;b[28].low=99;b[28].close=100;
   b[29].time=8700;b[29].open=100;b[29].high=101;b[29].low=99;b[29].close=100;
   b[30].time=9000;b[30].open=100;b[30].high=101;b[30].low=99;b[30].close=100;
   b[31].time=9300;b[31].open=100;b[31].high=101;b[31].low=99;b[31].close=100;
   b[32].time=9600;b[32].open=100;b[32].high=101;b[32].low=99;b[32].close=100;
   b[33].time=9900;b[33].open=100;b[33].high=101;b[33].low=99;b[33].close=100;
   b[34].time=10200;b[34].open=100;b[34].high=101;b[34].low=99;b[34].close=100;
   b[35].time=10500;b[35].open=100;b[35].high=101;b[35].low=99;b[35].close=100;
   b[36].time=10800;b[36].open=100;b[36].high=101;b[36].low=99;b[36].close=100;
   b[37].time=11100;b[37].open=100;b[37].high=101;b[37].low=99;b[37].close=100;
   b[38].time=11400;b[38].open=100;b[38].high=101;b[38].low=99;b[38].close=100;
   b[39].time=11700;b[39].open=100;b[39].high=101;b[39].low=99;b[39].close=100;
   b[40].time=12000;b[40].open=100;b[40].high=101;b[40].low=99;b[40].close=100;
   b[41].time=12300;b[41].open=100;b[41].high=101;b[41].low=99;b[41].close=100;
   b[42].time=12600;b[42].open=100;b[42].high=101;b[42].low=99;b[42].close=100;
   b[43].time=12900;b[43].open=100;b[43].high=101;b[43].low=99;b[43].close=100;
   b[44].time=13200;b[44].open=100;b[44].high=101;b[44].low=99;b[44].close=100;
   b[45].time=13500;b[45].open=100;b[45].high=101;b[45].low=99;b[45].close=100;
   b[46].time=13800;b[46].open=100;b[46].high=101;b[46].low=99;b[46].close=100;
   b[47].time=14100;b[47].open=100;b[47].high=101;b[47].low=99;b[47].close=100;
   b[48].time=14400;b[48].open=100;b[48].high=101;b[48].low=99;b[48].close=100;
   b[49].time=14700;b[49].open=100;b[49].high=101;b[49].low=99;b[49].close=100;
   if(Structure(b,ArraySize(b),2,hi,lo)!=0) failures++;
   FindSetup(b,1,s);
   if(s.side!=0) failures++;
   if(FloorVolume(1,200,0.01,0.01,100)!=0) failures++;
   if(MathAbs(FloorVolume(1,40,0.01,0.01,100)-0.02)>1e-10) failures++;
   if(!ValidBars(b,300,15000)) failures++;
   if(ValidBars(b,300,14999)) failures++;
   if(ValidBars(b,300,15301)) failures++;
   b[1].time=b[0].time; if(ValidBars(b,300,15000)) failures++;
   Print("CORE_SELFTEST fixtures=169 failures=",failures);
   return failures==0;
}

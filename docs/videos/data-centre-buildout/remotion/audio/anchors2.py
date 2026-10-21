import re, json
W=json.load(open('/tmp/film2r/audio/words.json'))['words']
norm=lambda w: re.sub(r"[^a-z0-9']","",w.lower().replace("’","'"))
N=[norm(w['w']) for w in W]
PH=[ # key, phrase (in narration order)
("open","more than seven hundred"),("amazon","amazon"),("alphabet","alphabet"),("microsoft","microsoft"),("meta","meta"),
("eighty1","up around eighty"),("fiveq","five questions"),("letsgo","let's go through"),
("q1","question one"),("q1_right","right now it is"),("q1_chip","the big chip makers"),("q1_capex","capital budgets"),("q1_pace","orders are keeping pace"),
("q2","question two"),("q2_yes","yes but tightly"),("q2_mem","the memory that feeds"),("q2_pack","the advanced packaging"),("q2_short","a shortage helps"),("q2_but","but it also means"),("q2_queue","projects wait"),
("q3","question three"),("q3_track","i track"),("q3_plan","about seventyseven"),("q3_op","only about eight"),("q3_30","around thirty percent"),("q3_partial","count partial"),
("q3_slip","fivegigawatt campus"),("q3_seven","another is roughly"),("q3_uk","in the uk"),("q3_bldg","a building without power"),("q3_car","very expensive car"),
("q3_iea","international energy agency"),("q3_fifth","fifth of planned"),
("q4","question four"),("q4_12","above one point two"),("q4_lead","lead times"),("q4_ahead","demand is ahead"),("q4_watch","the thing to watch"),
("q5","question five"),("q5_notyet","not yet"),("q5_40","around forty percent"),("q5_google","growing faster"),("q5_capex","capital spending is growing"),
("q5_backlog","order backlogs"),("q5_promise","promise not cash"),("q5_borrow","borrowing and clever"),("q5_bonds","bonds this year"),
("q5_meta","meta reported"),("q5_jv","joint venture"),("q5_circ","circular"),("q5_boom","past booms"),
("map","before the takeaway"),("l_chips","chips and memory get"),("l_net","networking and optical"),("l_fab","the factories and packaging"),
("l_pow","the power and cooling"),("l_build","the builders and landlords"),("l_gen","power generation"),("l_wait","each layer is paid"),("l_spend","the spenders at the top"),
("sowhat","so what does"),("sw1","one remember"),("sw2","two notice"),("sw3","three size it"),("sw_isa","stocks and shares isa"),
("close","five questions orders"),("disc","this is education"),("sub","if this helped"),
]
A={}; cur=0
for key,ph in PH:
    p=[norm(x) for x in ph.split()]
    found=None
    for i in range(cur,len(N)-len(p)+1):
        if N[i:i+len(p)]==p: found=i;break
    if found is None: print("MISSING",key,ph); continue
    A[key]=W[found]['s']; cur=found
A['end']=W[-1]['e']
json.dump(A,open('/tmp/film2r/audio/anchors.json','w'),indent=1)
for k,v in A.items(): print(f"{v:7.2f} {k}")

import random, json, sys
N = 19
CORE  = ["CARENCIALIDAD","VULNERABILIDAD","BUROCRATIZACION","PARTICIPACION","OBSOLESCENCIA",
         "DESVIACION","IDENTIDAD","COBERTURA","CUESTION","ESTANDAR","PROGRAMA","POBREZA",
         "MASIVOS","SUAREZ","OSZLAK","CIDES"]
EXTRA = ["DESORGANIZACION","REPRODUCCION","CAPACIDADES","NUSSBAUM","TERRITORIO","BOURDIEU",
         "PASSERON","SEMAFORO","HABITUS","AGENCIA","ANOMIA","COMBOS","MCKAY","SHAW","SEN"]
def empty(): return [[None]*N for _ in range(N)]
def can_place(g,w,r,c,d):
    L=len(w)
    if d=='H':
        if c+L>N: return None
        if c>0 and g[r][c-1] is not None: return None
        if c+L<N and g[r][c+L] is not None: return None
    else:
        if r+L>N: return None
        if r>0 and g[r-1][c] is not None: return None
        if r+L<N and g[r+L][c] is not None: return None
    cross=0
    for i,ch in enumerate(w):
        rr,cc=(r,c+i) if d=='H' else (r+i,c)
        cur=g[rr][cc]
        if cur is not None:
            if cur!=ch: return None
            cross+=1
        elif d=='H':
            if (rr>0 and g[rr-1][cc] is not None) or (rr+1<N and g[rr+1][cc] is not None): return None
        else:
            if (cc>0 and g[rr][cc-1] is not None) or (cc+1<N and g[rr][cc+1] is not None): return None
    return cross
def place(g,w,r,c,d):
    for i,ch in enumerate(w):
        if d=='H': g[r][c+i]=ch
        else: g[r+i][c]=ch
def candidates(g,w):
    # only positions that cross an existing letter
    out=[]
    for r in range(N):
        for c in range(N):
            ch=g[r][c]
            if ch is None: continue
            for i,wc in enumerate(w):
                if wc!=ch: continue
                if c-i>=0: out.append((r,c-i,'H'))
                if r-i>=0: out.append((r-i,c,'V'))
    return set(out)
def batch(g,placed,words,rnd,passes):
    rest=list(words)
    for _ in range(passes):
        left=[]
        for w in rest:
            best=None
            for (r,c,d) in candidates(g,w):
                cr=can_place(g,w,r,c,d)
                if cr:
                    sc=cr*8-0.6*(abs(r-N//2)+abs(c-N//2))+rnd.random()*6
                    if best is None or sc>best[0]: best=(sc,r,c,d)
            if best: _,r,c,d=best; place(g,w,r,c,d); placed.append((w,r,c,d))
            else: left.append(w)
        if not left: break
        rest=left
    return rest
def build(seed):
    rnd=random.Random(seed); g=empty(); placed=[]
    core=sorted(CORE,key=lambda w:-len(w)+rnd.random()*2.5)
    first=core[0]; r0,c0=N//2,(N-len(first))//2
    place(g,first,r0,c0,'H'); placed.append((first,r0,c0,'H'))
    mc=batch(g,placed,core[1:],rnd,6)
    batch(g,placed,sorted(EXTRA,key=lambda w:-len(w)+rnd.random()*3),rnd,3)
    return g,placed,mc
best=None
for s in range(int(sys.argv[1])):
    g,placed,mc=build(s); key=(-len(mc),len(placed))
    if best is None or key>best[0]: best=(key,g,placed,mc,s)
key,g,placed,mc,seed=best
print("seed",seed,"| core faltante:",mc,"| colocadas",len(placed))
rs=[r for r in range(N) if any(g[r])]; cs=[c for c in range(N) if any(g[r][c] for r in range(N))]
r1,r2,c1,c2=min(rs),max(rs),min(cs),max(cs)
G=[[g[r][c] for c in range(c1,c2+1)] for r in range(r1,r2+1)]
P=[(w,r-r1,c-c1,d) for (w,r,c,d) in placed]
H,W=len(G),len(G[0]); print("rejilla",H,"x",W)
starts={}; num=0
for r in range(H):
    for c in range(W):
        if G[r][c] is None: continue
        sh=(c==0 or G[r][c-1] is None) and (c+1<W and G[r][c+1] is not None)
        sv=(r==0 or G[r-1][c] is None) and (r+1<H and G[r+1][c] is not None)
        if sh or sv: num+=1; starts[(r,c)]=num
across=sorted([(starts[(r,c)],w) for (w,r,c,d) in P if d=='H'])
down=sorted([(starts[(r,c)],w) for (w,r,c,d) in P if d=='V'])
print("H:",across); print("V:",down)
for r in range(H): print(''.join(G[r][c] or '.' for c in range(W)))
json.dump({"grid":G,"nums":{f"{r},{c}":n for (r,c),n in starts.items()},"across":across,"down":down,"H":H,"W":W},open("crucigrama.json","w",encoding="utf8"))

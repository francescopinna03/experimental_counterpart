"""Preliminary battery. Fisher information of the recursive benchmark, not of the SBB bridge.

Predictions depend on a uniform L0 and on quadratic loss. The grid has
step 1. The criterion profiles lambda and lapse. It excludes intermediate bets,
source preferences and any dynamic process: those require the pilot.
Additive information assumes a level redrawn independently in each game.
"""
from pathlib import Path
import itertools as it
import json,csv
import numpy as np
from scipy.special import softmax,gammaln

ROOT=Path(__file__).resolve().parent;DATA=ROOT/'design_data'
def write(name,rows):
    with (DATA/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def game(lo0,hi0,p0,lo1,hi1,p1):
    grids=[np.arange(lo0,hi0+1,dtype=float),np.arange(lo1,hi1+1,dtype=float)]
    ps=[p0,p1];u=[]
    for i in [0,1]:
        raw=-(grids[i][:,None]-ps[i]*grids[1-i][None,:])**2
        u.append((raw-raw.min())/(raw.max()-raw.min()))
    policies=[[np.ones(len(grids[i]))/len(grids[i])] for i in [0,1]]
    values=[[],[]]
    for k in range(1,7):
        for i in [0,1]:
            val=u[i]@policies[1-i][k-1]; values[i].append(val)
            best=np.isclose(val,val.max(),atol=1e-12,rtol=0)
            policies[i].append(best/best.sum())
    best=[np.isclose(z,z.max(axis=0,keepdims=True),rtol=0,atol=1e-12) for z in u]
    ne=np.argwhere(best[0]&best[1].T)
    if len(ne)!=1:return None
    eq=[grids[i][ne[0,i]] for i in [0,1]]
    for i in [0,1]:
        supports=[grids[i][policies[i][k]>0] for k in [1,2,3]]+[np.array([eq[i]])]
        if min(np.abs(a[:,None]-b[None,:]).min() for a,b in it.combinations(supports,2))<2:return None
    return dict(grids=grids,u=u,values=values,policies=policies,eq=eq,
                specs=(lo0,hi0,p0,lo1,hi1,p1))

def mixture(g,i,lam,tau,lapse):
    k=np.arange(7);w=softmax(k*np.log(tau)-gammaln(k+1))
    components=[g['policies'][i][0]]+[softmax(lam*v) for v in g['values'][i]]
    m=w@np.array(components)
    return (1-lapse)*m+lapse/len(m)

def fisher(g,par):
    out=np.zeros((3,3));h=1e-4
    for i in [0,1]:
        prob=mixture(g,i,*par);der=[]
        for j in range(3):
            hi=np.array(par,dtype=float);lo=hi.copy();hi[j]+=h;lo[j]-=h
            der.append((mixture(g,i,*hi)-mixture(g,i,*lo))/(2*h))
        d=np.array(der).T;out+=(d.T/prob)@d/2
    return out

def efficient(z):
    j=[0,2];a=z[np.ix_(j,j)]
    return max(0.,float(z[1,1]-z[1,j]@np.linalg.pinv(a,rcond=1e-12)@z[j,1]))

bounds=[(10,50),(10,90),(30,50),(30,90)]
candidates=[]
for b0,b1,p0,p1 in it.product(bounds,bounds,[.5,.7,1.3,1.5],[.5,.7,1.3,1.5]):
    specs=(*b0,p0,*b1,p1)
    if specs>(*b1,p1,*b0,p0):continue
    g=game(*specs)
    if g is not None:candidates.append(g)
parameters=list(it.product([4.,12.,30.],[.7,1.5,2.5],[.02,.10]))
matrices=np.array([[fisher(g,p) for p in parameters] for g in candidates])
selected=[];total=np.zeros((len(parameters),3,3))
for _ in range(3):
    scores=[min(efficient(z) for z in total+2*matrices[j]) if j not in selected else -np.inf
            for j in range(len(candidates))]
    pick=int(np.argmax(scores));selected.append(pick);total+=2*matrices[pick]
rows=[]
for rank,j in enumerate(selected,1):
    g=candidates[j]
    for role in [0,1]:
        gr=g['grids'][role]
        means=[float(gr@g['policies'][role][k]) for k in [1,2,3]]
        ordered=sorted(means)
        thresholds=[int(np.ceil((a+b)/2)) for a,b in zip(sorted([g['eq'][role]]+means)[:-1],sorted([g['eq'][role]]+means)[1:])]
        rows.append(dict(game=f'K{rank}',role='A' if role==0 else 'B',
            lower=int(gr[0]),upper=int(gr[-1]),coefficient=g['specs'][2 if role==0 else 5],
            L0='uniform on the grid',L1=means[0],L2=means[1],L3=means[2],
            equilibrium=g['eq'][role],thresholds=';'.join(map(str,thresholds))))
write('K_battery.csv',rows)
diagnostics=[]
for par,mat in zip(parameters,total):
    e=efficient(mat)
    diagnostics.append(dict(lambda_K=par[0],tau=par[1],lapse=par[2],
        efficient_information_tau_per_person=e,
        ideal_SE_tau_n300=(300*e)**-.5 if e>0 else float('inf'),
        smallest_eigenvalue=float(np.linalg.eigvalsh(mat)[0])))
write('fisher_K_benchmark.csv',diagnostics)
out=dict(candidate_count=len(candidates),selected_games=[candidates[j]['specs'] for j in selected],
    rounds=6,roles_swapped_in_second_repetition=True,
    criterion='greedy maximin Schur tau, nuisance lambda and lapse, fixed recursive policies',
    parameter_grid=parameters,minimum_efficient_information=min(efficient(z) for z in total),
    nature='theoretical benchmark, not a bridge estimate or validated power',L0_is_distribution=True,
    independent_level_draw_per_game=True)
(DATA/'K_selection.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(dict(candidate_count=len(candidates),selected=rows,
    worst_ideal_SE=min(diagnostics,key=lambda d:d['efficient_information_tau_per_person'])),ensure_ascii=False,indent=2))

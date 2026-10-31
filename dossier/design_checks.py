"""Exact calculations and design scenarios. No human data, no SBB estimation."""
from pathlib import Path
import csv
import itertools as it
import json
import numpy as np
from scipy.integrate import quad
from scipy.stats import chi2, norm, t, nct
from scipy.optimize import brentq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA, FIG = ROOT/'design_data', ROOT/'figures'
DATA.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)

def csv_out(name, rows):
    with (DATA/name).open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def update(p,a,s):
    lh = a if s else 1-a
    w = p*lh+(1-p)*(1-lh)
    return p*lh/w, w

def unconditional(p): return 30+60*np.asarray(p)
def conditional(p,a=.2,b=.8):
    p=np.asarray(p)
    return 30+60*a*p/(a*p+b*(1-p))
def inferred_chi(u,s,a=.2,b=.8):
    p=(u-30)/60
    c=conditional(p,a,b)
    return (s-c)/(u-c)

oldnew=[]; paths=[]
for a,b in [(.7,.85),(.6,.7)]:
    eff=np.zeros(3); discr=0.
    for p in [.4,.6]:
        eff[0]+=4*(p*(1-p)/.25)**2
        for acc in [a,b]:
            for s in [0,1]:
                pp,w=update(p,acc,s)
                eff[1]+=2*w*(pp*(1-pp)/.25)**2
        for sw,ss in it.product([0,1],repeat=2):
            pw,ww=update(p,a,sw); pf,wf=update(pw,b,ss)
            ps,ws=update(p,b,ss); pr,wr=update(ps,a,sw)
            assert np.isclose(pf,pr) and np.isclose(ww*wf,ws*wr)
            eff[2]+=4*ww*wf*(pf*(1-pf)/.25)**2
            for price in [45,65]:
                discr+=2*ww*wf*(conditional(pf)<price<unconditional(pf))
            if a==.6:
                paths.append(dict(prior=p,weak_signal=sw,strong_signal=ss,
                    probability=ww*wf,posterior=pf,U=unconditional(pf),
                    C_strong=conditional(pf),C_weak=conditional(pf,.35,.65)))
    oldnew.append(dict(weak=a,strong=b,discriminating_of_8=discr,
        effective_initial=eff[0],effective_middle=eff[1],effective_final=eff[2],
        effective_S_old_three_windows=float(eff.mean())))
csv_out('signals_audit.csv',oldnew);csv_out('posterior_and_prices.csv',paths)

# Identity under the static Gamma restriction, including marginal availability.
maxerr=0.
for p,a,b,chi in it.product(np.linspace(.16,.84,29),[.2,.35],[.8,.65],np.linspace(0,1,9)):
    if (a,b) not in [(.2,.8),(.35,.65)]:continue
    joint=np.array([p*a,p*(1-a),(1-p)*b,(1-p)*(1-b)])
    avail=p*a+(1-p)*b
    independent=np.array([p*avail,p*(1-avail),(1-p)*avail,(1-p)*(1-avail)])
    contracted=(1-chi)*joint+chi*independent
    price=(90*contracted[0]+30*contracted[2])/(contracted[0]+contracted[2])
    predicted=conditional(p,a,b)+chi*(unconditional(p)-conditional(p,a,b))
    maxerr=max(maxerr,abs(price-predicted))
    assert np.isclose(inferred_chi(unconditional(p),price,a,b),chi)

# Flattening toward the price center: counterexample to the two-intensity check.
center=[]
for p,z,anchor in it.product([.4,.6],[.1,.2],[55.,57.5,65.]):
    u=(1-z)*unconditional(p)+z*anchor
    out=dict(prior=p,shrinkage=z,anchor=anchor,U_observed=u)
    for a,b,label in [(.2,.8,'strong'),(.35,.65,'weak')]:
        s=(1-z)*conditional(p,a,b)+z*anchor
        out[f'chi_apparent_{label}']=float(inferred_chi(u,s,a,b))
    center.append(out)
csv_out('anchoring_counterexample.csv',center)

# Step 5 yields intervals, not exact prices: example without stochastic error.
u0=54.;s0=conditional(.4)+.25*(54-conditional(.4))
u_bounds=(50.,55.);s_bounds=(40.,45.)
u_mesh=np.linspace(50,55,1001);s_mesh=np.array([40.,45.])
chi_possible=inferred_chi(u_mesh[:,None],s_mesh[None,:])

# Normal TOST with estimated pooled variance, exact in the declared scenario.
def eq_power(sd,n=100,icc=.2,margin=3,delta=0,alpha=.025):
    df=n-2 # 2*(n/2 diadi)-2
    se=sd*np.sqrt(2*(1+icc)/n)
    crit=t.ppf(1-alpha,df)
    def conditional_power(v):
        half=crit*np.sqrt(v/df)
        lo=(-margin-delta)/se+half
        hi=(margin-delta)/se-half
        return max(0.,norm.cdf(hi)-norm.cdf(lo))*chi2.pdf(v,df)
    return quad(conditional_power,chi2.ppf(1e-10,df),chi2.ppf(1-1e-10,df),epsabs=1e-9)[0]
power=[]
for n,sd,delta in it.product([100,160,200],[4,5,6,7,8,10],[0,1]):
    power.append(dict(n_per_arm=n,dyads_per_arm=n//2,icc=.2,individual_sd=sd,
        true_difference=delta,margin=3,alpha_each_TOST=.025,power=eq_power(sd,n,delta=delta)))
csv_out('equivalence_power.csv',power)
sigma80=brentq(lambda sd:eq_power(sd)-.8,1,15)

templates=[]
for p,label,a,b,rep in it.product([.4,.6],['strong','weak'],[0],[0],[1,2]):
    a,b=(.2,.8) if label=='strong' else (.35,.65)
    templates.append(dict(condition='dependence',prior=p,q_high=a,q_low=b,repeat=rep,reveal='no'))
for p,rep in it.product([.4,.6],[1,2]):
    templates.append(dict(condition='independence',prior=p,q_high=.5,q_low=.5,repeat=rep,reveal='no'))
for p,label in it.product([.4,.6],['strong','weak']):
    a,b=(.2,.8) if label=='strong' else (.35,.65)
    templates.append(dict(condition='revelation',prior=p,q_high=a,q_low=b,repeat=1,reveal='J before final list'))
for k,row in enumerate(templates,1): row['trial_id']=f'X{k:02d}'
csv_out('template_X.csv',templates)

calibration=[]
for value,availability in [(36,.2),(48,.65),(66,.35),(78,.8)]:
    for lo,hi in [(20,90),(30,100)]:
        calibration.append(dict(trial_id=f'C{len(calibration)+1:02d}',known_value=value,
            selective_availability=availability,grid_lower=lo,grid_upper=hi,grid_step=1,
            benchmark_U=value,benchmark_S=value))
csv_out('template_price_calibration.csv',calibration)
rng=np.random.default_rng(20261009)
sides=np.array(['left']*8+['right']*8);rng.shuffle(sides)
urns=[]
for j in range(16):
    low=[20,40,60][j%3];high=low+j+1
    urns.append(dict(trial_id=f'U{j+1:02d}',total_tokens=100,gap_pp=j+1,
        winning_left=high if sides[j]=='left' else low,
        winning_right=high if sides[j]=='right' else low,best_side=sides[j]))
csv_out('template_urns.csv',urns)
computers=[
    dict(trial_id='PC1',game='K1',own_role='A',partner_policy='uniform 10 to 90',optimal_actions='25'),
    dict(trial_id='PC2',game='K1',own_role='B',partner_policy='uniform 10 to 90',optimal_actions='65'),
    dict(trial_id='PC3',game='K1',own_role='A',partner_policy='certain number 65',optimal_actions='32;33'),
    dict(trial_id='PC4',game='K3',own_role='B',partner_policy='certain number 25',optimal_actions='32;33')]
csv_out('template_computer.csv',computers)

# Fixed payment per slot and reserve lottery independent of behavior.
weights=dict(X_final=.30,K_action=.20,X_early0=.08,X_early1=.08,
    K_bets0=.06,K_bets1=.06,price_calibration=.10,urns=.06,computer=.06)
assert np.isclose(sum(weights.values()),1)
for lo,hi in [(20,90),(30,100)]:
    pay=[.5+j*(v-p)/200 for j,v,p in it.product([0,1],[30,90],range(lo,hi+1))]
    assert min(pay)>=0 and max(pay)<=1

checks=dict(nature='design calculations without human data',
    gamma_price_identity_max_error=maxerr,
    signal_order_invariance=True,
    posterior_range_new=[min(x['posterior'] for x in paths),max(x['posterior'] for x in paths)],
    gain_in_old_report_information=oldnew[1]['effective_S_old_three_windows']/oldnew[0]['effective_S_old_three_windows']-1,
    ratio_old_report_SE=np.sqrt(oldnew[0]['effective_S_old_three_windows']/oldnew[1]['effective_S_old_three_windows']),
    five_point_interval_example=dict(true_U=u0,true_S=float(s0),true_chi=.25,
        interval_U=u_bounds,interval_S=s_bounds,chi_range=[float(chi_possible.min()),float(chi_possible.max())]),
    sigma_limit_80pct_equivalence_n100=sigma80,payment_weights=weights,
    empty_slot_fallback_final_relative_probability=dict(F=1,S=2/3,R=1/3),
    chosen_empty_slot_probability=.5,number_X=len(templates))
(DATA/'checks_v2.json').write_text(json.dumps(checks,indent=2,ensure_ascii=False)+'\n')

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,2,figsize=(10.7,4.1))
x=np.linspace(0,1,101)
for a,b,label,col in [(.2,.8,'Strong selection','#1b6079'),(.35,.65,'Weak selection','#b86d27')]:
    c=conditional(.4,a,b)
    ax[0].plot(x,c+x*(54-c),label=label,color=col,lw=2.4)
ax[0].axhline(54,color='#666666',ls='--',label='Always available')
ax[0].set(xlabel='Effective contraction',ylabel='Reservation price in points',title='Static restriction, posterior 0.4')
ax[0].legend(frameon=False,fontsize=8)
for n,col in [(100,'#1b6079'),(160,'#b86d27'),(200,'#56815a')]:
    xx=np.linspace(4,10,25)
    ax[1].plot(xx,[eq_power(sd,n) for sd in xx],label=f'{3*n} subjects in total',color=col,lw=2)
ax[1].axhline(.8,color='#666666',ls='--',lw=.8)
ax[1].set(xlabel='Individual SD of the adjusted mean price',ylabel='Power in the scenario',ylim=(0,1),title='Equivalence within 3 points')
ax[1].legend(frameon=False,fontsize=8)
fig.text(.5,.015,'Theoretical calculations. TOST: alpha 0.025 per side; ICC 0.2; true difference zero.',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.055,1,1));fig.savefig(FIG/'prices_and_power_v2.png',dpi=170)
print(json.dumps(checks,ensure_ascii=False,indent=2))

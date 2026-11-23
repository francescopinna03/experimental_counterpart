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
RULES = {'weak': (.35, .65), 'strong': (.2, .8), 'very_strong': (.05, .95)}

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
def logit(p): return np.log(p/(1-p))
def expit(x): return 1/(1+np.exp(-x))
def sale_belief(p,a,b): return a*p/(a*p+b*(1-p))
def averaging(p,chi,a,b): return (1-chi)*sale_belief(p,a,b)+chi*p
def dampening(p,chi,a,b): return expit(logit(p)+(1-chi)*np.log(a/b))

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
                    C_strong=conditional(pf),C_weak=conditional(pf,.35,.65),
                    C_very_strong=conditional(pf,.05,.95)))
    oldnew.append(dict(weak=a,strong=b,discriminating_of_8=discr,
        effective_initial=eff[0],effective_middle=eff[1],effective_final=eff[2],
        effective_S_old_three_windows=float(eff.mean())))
csv_out('signals_audit.csv',oldnew);csv_out('posterior_and_prices.csv',paths)

# Identity under the static Gamma restriction, including marginal availability.
maxerr=0.
for p,(a,b),chi in it.product(np.linspace(.16,.84,29),RULES.values(),np.linspace(0,1,9)):
    joint=np.array([p*a,p*(1-a),(1-p)*b,(1-p)*(1-b)])
    avail=p*a+(1-p)*b
    independent=np.array([p*avail,p*(1-avail),(1-p)*avail,(1-p)*(1-avail)])
    contracted=(1-chi)*joint+chi*independent
    price=(90*contracted[0]+30*contracted[2])/(contracted[0]+contracted[2])
    predicted=conditional(p,a,b)+chi*(unconditional(p)-conditional(p,a,b))
    maxerr=max(maxerr,abs(price-predicted))
    assert np.isclose(inferred_chi(unconditional(p),price,a,b),chi)
    assert np.isclose(30+60*averaging(p,chi,a,b),predicted)

bench=[]
for p,(label,(a,b)) in it.product([.4,.6],RULES.items()):
    u=float(unconditional(p)); c=float(conditional(p,a,b))
    bench.append(dict(belief=p,intensity=label,sale_if_90=a,sale_if_30=b,belief_after_sale=sale_belief(p,a,b),
        U=u,C=c,gap=u-c,S_degree_0_25=c+.25*(u-c),S_degree_1=u))
csv_out('benchmark_prices.csv',bench)

beliefs=[.4]
for acc in [.7,.6]: beliefs.append(update(beliefs[-1],acc,0)[0])
example=[]
for (seconds,p1,p2),q in zip([('10 to 40',54,43),('60 to 90',43,37),('120 to 150',39,35)],beliefs):
    example.append(dict(seconds=seconds,belief=q,U=float(unconditional(q)),C=float(conditional(q)),
        stated_P1=p1,stated_P2=p2,implied_degree=float(inferred_chi(p1,p2))))
csv_out('example_trial.csv',example)

# Flattening toward the price center: counterexample to the two-intensity check.
center=[]
for p,z,anchor in it.product([.4,.6],[.1,.2],[55.,57.5,65.]):
    u=(1-z)*unconditional(p)+z*anchor
    out=dict(prior=p,shrinkage=z,anchor=anchor,U_observed=u)
    for label,(a,b) in RULES.items():
        s=(1-z)*conditional(p,a,b)+z*anchor
        out[f'chi_apparent_{label}']=float(inferred_chi(u,s,a,b))
    center.append(out)
csv_out('anchoring_counterexample.csv',center)

# Step 5 yields intervals, not exact prices: example without stochastic error.
u0=54.;s0=conditional(.4)+.25*(54-conditional(.4))
u_bounds=(50.,55.);s_bounds=(40.,45.)
u_mesh=np.linspace(50,55,1001);s_mesh=np.array([40.,45.])
chi_possible=inferred_chi(u_mesh[:,None],s_mesh[None,:])

pull_error=0.
for p,(a,b),chi,kappa in it.product([.16,.4,.7],RULES.values(),[0.,.25,.5],[.1,.3]):
    u=unconditional(p); c=conditional(p,a,b)
    for alone in [c+chi*(u-c),30+60*dampening(p,chi,a,b)]:
        share=(alone-c)/(u-c)
        pull_error=max(pull_error,abs((alone+kappa*(u-alone)-c)/(u-c)-(share+kappa*(1-share))))

two_rules=[]
for label,(a,b) in RULES.items():
    u=float(unconditional(.4)); c=float(conditional(.4,a,b))
    for chi in [.25,.5]:
        sa=30+60*averaging(.4,chi,a,b); sd=30+60*dampening(.4,chi,a,b)
        two_rules.append(dict(belief=.4,intensity=label,degree=chi,U=u,C=c,S_averaging=float(sa),S_dampening=float(sd),
            excess_averaging=float(sa-c),excess_dampening=float(sd-c),uncovered_share_dampening=float((sd-c)/(u-c))))
csv_out('two_rules.csv',two_rules)
a,b=RULES['strong']
dampening_plus=30+60*dampening(.4,.15,a,b)-conditional(.4,a,b)
dampening_minus=30+60*dampening(.4,-.15,a,b)-conditional(.4,a,b)
a,b=RULES['very_strong']
negative_below=-sale_belief(.4,a,b)/(.4-sale_belief(.4,a,b))

def information_states(prior,stage):
    odds=prior/(1-prior)
    if stage=='prior': return [(1.,prior)]
    out=[]
    if stage=='one':
        for acc,high in it.product([.7,.6],[1,0]):
            pr=.5*(prior*(acc if high else 1-acc)+(1-prior)*((1-acc) if high else acc))
            q=odds*(acc/(1-acc) if high else (1-acc)/acc); out.append((pr,q/(1+q)))
        return out
    for h7,h6 in it.product([1,0],repeat=2):
        pr=prior*(.7 if h7 else .3)*(.6 if h6 else .4)+(1-prior)*(.3 if h7 else .7)*(.4 if h6 else .6)
        q=odds*(7/3 if h7 else 3/7)*(3/2 if h6 else 2/3); out.append((pr,q/(1+q)))
    return out
def weighted_states(stage):
    out=[]
    for prior in [.4,.6]:
        if stage=='final': out+=[(.5*w,q) for w,q in information_states(prior,'final')]
        else: out+=[(.25*w,q) for w,q in information_states(prior,'prior')+information_states(prior,'one')]
    assert np.isclose(sum(w for w,_ in out),1)
    return out
gaps={}
for stage in ['final','intermediate']:
    for label,(a,b) in RULES.items():
        g=[(w,float(unconditional(q)-conditional(q,a,b))) for w,q in weighted_states(stage)]
        gaps[stage,label]=(sum(w*x for w,x in g),sum(w*x*x for w,x in g))
mean_gap_final={label:gaps['final',label][0] for label in RULES}
mean_gap_joint_trials=float(np.mean(list(mean_gap_final.values())))
information_share={stage:{label:gaps[stage,label][1]/sum(gaps[stage,k][1] for k in RULES) for label in RULES} for stage in ['final','intermediate']}

nodes,hw=np.polynomial.hermite_e.hermegauss(80);hw=hw/hw.sum()
num=den=0.
for label,(a,b) in RULES.items():
    for prior in [.4,.6]:
        for w,q in [(.5*x,y) for x,y in information_states(prior,'prior')+information_states(prior,'one')]:
            gap=60*(q-sale_belief(q,a,b))
            bias=60*(np.sum(hw*dampening(q,.15*nodes,a,b))-sale_belief(q,a,b))
            num+=w*bias*gap;den+=w*gap*gap
dampening_bias_zero_mean=num/den

p,(a,b)=.4,RULES['strong']
joint=np.array([p*a,p*(1-a),(1-p)*b,(1-p)*(1-b)])
avail=p*a+(1-p)*b
product=np.array([p*avail,p*(1-avail),(1-p)*avail,(1-p)*(1-avail)])
def information(law): return float(np.sum(law*np.log(law/product)))
mixture_information_ratio=information(.75*joint+.25*product)/information(joint)
geometric=joint**.75*product**.25;geometric=geometric/geometric.sum()
assert np.isclose(geometric[0]/(geometric[0]+geometric[2]),dampening(p,.25,a,b))

def certainty_equivalent(p,r): return 30-np.log(1-p+p*np.exp(-60*r))/r
risk={}
for target in [55.,50.]:
    r=brentq(lambda x:certainty_equivalent(.5,x)-target,1e-6,1.)
    worst=0.
    for prior,(a,b) in it.product([.4,.6],RULES.values()):
        for stage in ['prior','one','final']:
            for _,q in information_states(prior,stage):
                p1=certainty_equivalent(q,r);p2=certainty_equivalent(sale_belief(q,a,b),r)
                worst=max(worst,abs(float(inferred_chi(p1,p2,a,b))))
    a,b=RULES['strong']
    p1=certainty_equivalent(.4,r);p2=certainty_equivalent(sale_belief(.4,a,b),r)
    risk[f'certainty_equivalent_{int(target)}']=dict(P1=float(p1),P2=float(p2),belief_read=float((p1-30)/60),
        C_at_belief_read=float(conditional((p1-30)/60,a,b)),apparent_degree=float(inferred_chi(p1,p2,a,b)),
        largest_apparent_degree=worst)

incentive={f'threshold_{d}_points_above_optimum':dict(expected_points_lost=d*(d+1)/142,
    probability_points_lost=100*d*(d+1)/142/140,euros_lost=16*d*(d+1)/142/140) for d in [1,5,10]}

calendars=[]
for window,trials in [(30,22),(45,22),(45,16)]:
    trial=10+window+10+10+window+15+15+window
    calendars.append(dict(window_seconds=window,purchase_trials=trials,trial_seconds=trial,
        first_window=f'10 to {10+window}',first_certificate=20+window,second_window=f'{30+window} to {30+2*window}',
        second_certificate=45+2*window,final_decision=f'{60+2*window} to {trial}',
        purchase_task_minutes=trial*trials/60,wait_before_final_seconds=trial-window,
        wait_before_final_minutes=(trial-window)*trials/60))
csv_out('calendars.csv',calendars)

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
sigma80_margin2=brentq(lambda sd:eq_power(sd,margin=2)-.8,1,15)

templates=[]
for p,label,rep in it.product([.4,.6],RULES,[1,2]):
    a,b=RULES[label]
    templates.append(dict(condition='joint',prior=p,intensity=label,q_high=a,q_low=b,repeat=rep,
        sellers='both',reveal='no',short_variant='no' if label=='weak' else 'yes'))
for p,label in it.product([.4,.6],RULES):
    a,b=RULES[label]
    templates.append(dict(condition='single_seller',prior=p,intensity=label,q_high=a,q_low=b,repeat=1,
        sellers='one for each member of the pair',reveal='no',short_variant='no' if label=='weak' else 'yes'))
for p in [.4,.6]:
    templates.append(dict(condition='placebo',prior=p,intensity='placebo',q_high=.5,q_low=.5,repeat=1,
        sellers='both',reveal='no',short_variant='yes'))
for p in [.4,.6]:
    a,b=RULES['strong']
    templates.append(dict(condition='revelation',prior=p,intensity='strong',q_high=a,q_low=b,repeat=1,
        sellers='both',reveal='sale before the final decision',short_variant='yes'))
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

# Fixed payment per slot and reserve lottery independent of behavior.
weights=dict(final_decision=.48,first_intermediate_window=.13,second_intermediate_window=.13,
    announced_value_lists=.16,urns=.10)
assert np.isclose(sum(weights.values()),1)
kept=dict(final_decision=.30,first_intermediate_window=.08,second_intermediate_window=.08,
    announced_value_lists=.10,urns=.06)
assert all(round(100*kept[k]/sum(kept.values()))==round(100*weights[k]) for k in weights)
for lo,hi in [(20,90),(30,100)]:
    pay=[.5+j*(v-p)/140 for j,v,p in it.product([0,1],[30,90],range(lo,hi+1))]
    assert min(pay)>=0 and max(pay)<=1

checks=dict(nature='design calculations without human data',
    gamma_price_identity_max_error=maxerr,
    signal_order_invariance=True,
    posterior_range_new=[min(x['posterior'] for x in paths),max(x['posterior'] for x in paths)],
    gain_in_old_report_information=oldnew[1]['effective_S_old_three_windows']/oldnew[0]['effective_S_old_three_windows']-1,
    ratio_old_report_SE=np.sqrt(oldnew[0]['effective_S_old_three_windows']/oldnew[1]['effective_S_old_three_windows']),
    five_point_interval_example=dict(true_U=u0,true_S=float(s0),true_chi=.25,
        interval_U=u_bounds,interval_S=s_bounds,chi_range=[float(chi_possible.min()),float(chi_possible.max())]),
    pull_identity_max_error=pull_error,
    dampening_strong_belief_0_4=dict(excess_at_degree_plus_0_15=float(dampening_plus),excess_at_degree_minus_0_15=float(dampening_minus)),
    averaging_probability_negative_below_degree=float(negative_below),
    averaging_excess_limit_seller_never_sells_90=.5*float(unconditional(.4)-30),
    apparent_mean_degree_zero_mean_dampening_sd_0_15=float(dampening_bias_zero_mean),
    mixture_information_ratio_degree_0_25=mixture_information_ratio,
    mean_gap_final_decision=dict(mean_gap_final,all_joint_trials=mean_gap_joint_trials),
    margin_3_over_mean_gap=3/mean_gap_joint_trials,
    outcome_shift_mean_neglect_0_15=.15*mean_gap_joint_trials,
    information_share_by_intensity=information_share,
    risk_aversion_without_neglect=risk,
    incentive_near_optimum=incentive,
    sigma_limit_80pct_equivalence_n100=sigma80,
    sigma_limit_80pct_equivalence_n100_margin_2=sigma80_margin2,
    payment_weights=weights,
    prize_probability='0.5 + points/140',
    final_decision_weight_if_inactive_slots_redirected=dict(F=weights['final_decision']+2*weights['first_intermediate_window'],
        S=weights['final_decision']+weights['first_intermediate_window'],R=weights['final_decision']),
    chosen_empty_slot_probability=.5,number_X=len(templates),
    number_X_short_variant=sum(row['short_variant']=='yes' for row in templates))
(DATA/'checks.json').write_text(json.dumps(checks,indent=2,ensure_ascii=False)+'\n')

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,2,figsize=(10.7,4.1))
x=np.linspace(0,1,101)
for label,name,col in [('weak','Weak selection','#b86d27'),('strong','Strong selection','#1b6079'),('very_strong','Very strong selection','#56815a')]:
    a,b=RULES[label]
    ax[0].plot(x,30+60*averaging(.4,x,a,b),label=name,color=col,lw=2.4)
    ax[0].plot(x,30+60*dampening(.4,x,a,b),color=col,lw=1.2,ls=':')
ax[0].axhline(54,color='#666666',ls='--',label='Always available')
ax[0].set(xlabel='Degree of selection neglect',ylabel='Reservation price in points',title='Belief 0.4, averaging (solid) and dampening (dotted)')
ax[0].legend(frameon=False,fontsize=8)
for n,col in [(100,'#1b6079'),(160,'#b86d27'),(200,'#56815a')]:
    xx=np.linspace(4,10,25)
    ax[1].plot(xx,[eq_power(sd,n) for sd in xx],label=f'{3*n} subjects in total',color=col,lw=2)
ax[1].axhline(.8,color='#666666',ls='--',lw=.8)
ax[1].set(xlabel='Individual SD of the adjusted mean price',ylabel='Power in the scenario',ylim=(0,1),title='Equivalence within 3 points')
ax[1].legend(frameon=False,fontsize=8)
fig.text(.5,.015,'Theoretical calculations. TOST: alpha 0.025 per side; ICC 0.2; true difference zero.',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.055,1,1));fig.savefig(FIG/'prices_and_power.png',dpi=170)
print(json.dumps(checks,ensure_ascii=False,indent=2))

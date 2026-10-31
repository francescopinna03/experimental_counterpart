from pathlib import Path
import csv
import sys
import os
import re
import json
import numpy as np
from multiprocessing import Pool
from scipy.special import ndtr, logsumexp
from scipy.optimize import minimize
from scipy.stats import t as tdist, chi2, norm
from scipy.integrate import quad
from numpy.polynomial.hermite_e import hermegauss
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA, FIG = ROOT/'design_data', ROOT/'figures'
DATA.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)

SEED = 20261104
PRIORS = (.4, .6)
ACCURACIES = (.6, .7)
INTENSITIES = ((.2, .8), (.35, .65))
GRIDS = ((20, 90, 55), (30, 100, 65))
MARGIN = 3
ALPHA = .025
NODES_EFFECTS = 7
NODES_ERROR = 5
TRUE_ERROR_RHO = .3
REPLICATIONS_H1 = 2000
REPLICATIONS_H2 = 2000
REPLICATIONS_PILOT = 2000
BOOTSTRAP_REPLICATIONS = 1999
SAMPLE_SIZES = (300, 360, 420, 480, 540, 600)
SD_THRESHOLD = 5.92
PROCESSES = int(os.environ.get('PROCESSES', os.cpu_count() or 1))

def csv_out(name, rows):
    with (DATA/name).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def logit(p): return np.log(p/(1-p))
def expit(x): return 1/(1+np.exp(-x))
def unconditional(p): return 30+60*p
def conditional(p, a, b): return 30+60*a*p/(a*p+b*(1-p))
def gap(p, a, b): return unconditional(p)-conditional(p, a, b)

def generate_trials(rng, n, intermediate_window):
    T = 8
    prior = np.zeros((n, T)); a = np.zeros((n, T)); b = np.zeros((n, T))
    llr_seen = np.zeros((n, T)); llr_all = np.zeros((n, T))
    lo = np.zeros((n, T)); hi = np.zeros((n, T)); center = np.zeros((n, T))
    for i in range(n):
        scheme = [(p, ab) for p in PRIORS for ab in INTENSITIES for r in (0, 1)]
        rng.shuffle(scheme)
        fmt = rng.permutation([0, 1]*4)
        moment = rng.permutation([0, 1]*4)
        for k, (p, (aa, bb)) in enumerate(scheme):
            prior[i, k], a[i, k], b[i, k] = p, aa, bb
            high_value = rng.random() < p
            order = rng.permutation(2)
            llr = []
            for q in np.array(ACCURACIES)[order]:
                correct = rng.random() < q
                says_high = correct if high_value else not correct
                llr.append(np.log(q/(1-q)) if says_high else np.log((1-q)/q))
            llr_all[i, k] = llr[0]+llr[1]
            llr_seen[i, k] = (llr[0] if moment[k] == 1 else 0.0) if intermediate_window else llr_all[i, k]
            lo[i, k], hi[i, k], center[i, k] = GRIDS[fmt[k]]
    return dict(prior=prior, a=a, b=b, llr=llr_seen, llr_final=llr_all, lo=lo, hi=hi, center=center)

def latent_prices(prove, alpha, psi, w0, w1):
    eta = alpha[:, None]+w0*logit(prove['prior'])+w1*prove['llr']
    pt = expit(eta)
    u = unconditional(pt)
    s = conditional(pt, prove['a'], prove['b'])+psi[:, None]*gap(pt, prove['a'], prove['b'])
    return u, s

def observe(rng, prove, u, s, z, sigma, rho, delta_s=0.0):
    m = np.stack([(1-z)*u+z*prove['center'], (1-z)*s+z*prove['center']+delta_s], axis=-1)
    common = rng.standard_normal(m.shape[:-1]+(1,))
    own = rng.standard_normal(m.shape)
    threshold = m+sigma*(np.sqrt(rho)*common+np.sqrt(1-rho)*own)
    lo = prove['lo'][..., None]; hi = prove['hi'][..., None]
    k = np.floor(threshold)
    L = np.where(threshold < lo, -np.inf, np.where(threshold >= hi, hi, k))
    R = np.where(threshold < lo, lo, np.where(threshold >= hi, np.inf, k+1))
    return L, R, threshold

def quadrature_nodes():
    xe, we = hermegauss(NODES_EFFECTS); xr, wr = hermegauss(NODES_ERROR)
    we = we/we.sum(); wr = wr/wr.sum()
    g1, g2, g3 = np.meshgrid(xe, xe, xr, indexing='ij')
    lw = np.log(np.einsum('i,j,k->ijk', we, we, wr)).ravel()
    return g1.ravel(), g2.ravel(), g3.ravel(), lw

G1, G2, G3, GW = quadrature_nodes()

def unpack(theta):
    mu_psi, lsg_psi, mu_a, lsg_a, arho, w0, w1, z, lsg_e, arho_e = theta
    return mu_psi, np.exp(lsg_psi), mu_a, np.exp(lsg_a), np.tanh(arho), w0, w1, z, np.exp(lsg_e), expit(arho_e)

def neg_loglik(theta, prove, L, R, constrain_zero=False):
    mu_psi, sg_psi, mu_a, sg_a, rho, w0, w1, z, sg_e, rho_e = unpack(theta)
    if constrain_zero: mu_psi = 0.0
    alpha = mu_a+sg_a*G1
    psi = mu_psi+sg_psi*(rho*G1+np.sqrt(1-rho**2)*G2)
    eta = alpha[:, None, None]+w0*logit(prove['prior'])[None]+w1*prove['llr'][None]
    pt = expit(eta)
    u = unconditional(pt)
    s = conditional(pt, prove['a'][None], prove['b'][None])+psi[:, None, None]*gap(pt, prove['a'][None], prove['b'][None])
    m = np.stack([(1-z)*u+z*prove['center'][None], (1-z)*s+z*prove['center'][None]], axis=-1)+(sg_e*np.sqrt(rho_e)*G3)[:, None, None, None]
    sd = sg_e*np.sqrt(1-rho_e)
    pr = ndtr((R[None]-m)/sd)-ndtr((L[None]-m)/sd)
    lp = np.log(np.clip(pr, 1e-300, None)).sum(axis=(2, 3))
    return -logsumexp(lp+GW[:, None], axis=0).sum()

START = np.array([.1, np.log(.1), 0., np.log(.3), 0., 1., 1., .05, np.log(4.), 0.])
BOUNDS = [(-.5, 1.5), (np.log(.01), np.log(1.)), (-2, 2), (np.log(.01), np.log(2.)), (-2, 2), (.2, 2.5), (.2, 2.5), (-.3, .8), (np.log(.5), np.log(15.)), (-4, 4)]

def estimate(prove, L, R, start=None):
    ris = minimize(neg_loglik, START if start is None else start, args=(prove, L, R), method='L-BFGS-B', bounds=BOUNDS)
    ris0 = minimize(neg_loglik, ris.x, args=(prove, L, R, True), method='L-BFGS-B', bounds=BOUNDS)
    return ris.x, 2*(ris0.fun-ris.fun)

def test_h1(theta, lr):
    return bool((theta[0] > 0) and (lr > 3.841459))

def replicate_h1(arg):
    seed, n, mu_psi, z, sigma_e, sigma_psi = arg
    rng = np.random.default_rng(seed)
    prove = generate_trials(rng, n, True)
    alpha = rng.normal(0, .3, n)
    psi = mu_psi+sigma_psi*rng.standard_normal(n)
    u, s = latent_prices(prove, alpha, psi, 1., 1.)
    L, R, _ = observe(rng, prove, u, s, z, sigma_e, TRUE_ERROR_RHO)
    theta, lr = estimate(prove, L, R)
    return test_h1(theta, lr), theta[0], theta[7], expit(theta[9]), lr

def slug(name):
    return re.sub('[^A-Za-z0-9]+', '_', name).strip('_')

def scenario_h1(name, n, mu_psi, z, sigma_e, sigma_psi, reps, seed):
    seeds = np.random.SeedSequence(seed).spawn(reps)
    args = [(sq, n, mu_psi, z, sigma_e, sigma_psi) for sq in seeds]
    with Pool(PROCESSES) as pool: out = pool.map(replicate_h1, args, chunksize=1)
    rej = np.array([o[0] for o in out], float); estimates = np.array([o[1] for o in out])
    csv_out(f'replications_H1_{slug(name)}.csv', [dict(replication=i, rejection=int(o[0]), estimate=round(o[1], 6), anchoring_z=round(o[2], 6), error_rho=round(o[3], 6), lr=round(o[4], 6)) for i, o in enumerate(out)])
    p = rej.mean(); se = np.sqrt(p*(1-p)/reps)
    return dict(scenario=name, subjects_S=n, true_contraction=mu_psi, sd_contraction=sigma_psi, anchoring_z=z, sigma_error=sigma_e,
                true_error_rho=TRUE_ERROR_RHO, replications=reps, rejection_rate=round(p, 4), mc_lower=round(max(0, p-1.96*se), 4), mc_upper=round(min(1, p+1.96*se), 4),
                mean_estimate=round(estimates.mean(), 4), bias=round(estimates.mean()-mu_psi, 4), rmse=round(np.sqrt(((estimates-mu_psi)**2).mean()), 4),
                mean_estimated_z=round(float(np.mean([o[2] for o in out])), 4), mean_estimated_error_rho=round(float(np.mean([o[3] for o in out])), 4))

BOOT_DATA = {}

def init_boot(prove, L, R):
    BOOT_DATA.update(prove=prove, L=L, R=R)

def replicate_boot(arg):
    seed, theta = arg
    rng = np.random.default_rng(seed)
    prove, L, R = BOOT_DATA['prove'], BOOT_DATA['L'], BOOT_DATA['R']
    dyads = np.arange(len(L)).reshape(-1, 2)
    idx = dyads[rng.integers(0, len(dyads), len(dyads))].ravel()
    sub = {k: v[idx] for k, v in prove.items()}
    ris = minimize(neg_loglik, theta, args=(sub, L[idx], R[idx]), method='L-BFGS-B', bounds=BOUNDS)
    return ris.x[0]

def dyad_bootstrap(n, mu_psi, z, sigma_e, sigma_psi, seed):
    rng = np.random.default_rng(seed)
    prove = generate_trials(rng, n, True)
    alpha = rng.normal(0, .3, n); psi = mu_psi+sigma_psi*rng.standard_normal(n)
    u, s = latent_prices(prove, alpha, psi, 1., 1.)
    L, R, _ = observe(rng, prove, u, s, z, sigma_e, TRUE_ERROR_RHO)
    theta, lr = estimate(prove, L, R)
    seeds = np.random.SeedSequence(seed+1).spawn(BOOTSTRAP_REPLICATIONS)
    with Pool(PROCESSES, initializer=init_boot, initargs=(prove, L, R)) as pool: estimates = np.array(pool.map(replicate_boot, [(sq, theta) for sq in seeds], chunksize=1))
    return dict(true_contraction=mu_psi, point_estimate=round(theta[0], 4), lr=round(lr, 3), lr_rejection=test_h1(theta, lr),
                bootstrap_replications=BOOTSTRAP_REPLICATIONS, sd_bootstrap=round(estimates.std(ddof=1), 4),
                basic_lower_bound=round(float(np.quantile(2*theta[0]-estimates, .025)), 4),
                percentile_lower_bound=round(float(np.quantile(estimates, .025)), 4))

def statistic_h2(rng, n_subjects, delta, z, sigma_e, sigma_psi, mu_psi, sigma_dyad, protocol_r):
    prove = generate_trials(rng, n_subjects, False)
    alpha = rng.normal(0, .3, n_subjects)
    psi = mu_psi+sigma_psi*rng.standard_normal(n_subjects)
    u, s = latent_prices(prove, alpha, psi, 1., 1.)
    dyad_effect = np.repeat(rng.normal(0, sigma_dyad, n_subjects//2), 2)
    L, R, threshold = observe(rng, prove, u+dyad_effect[:, None], s+dyad_effect[:, None], z, sigma_e, TRUE_ERROR_RHO, delta if protocol_r else 0.0)
    pobs = np.clip(np.floor(threshold[..., 1]), 30, 90)
    p_obj = expit(logit(prove['prior'])+prove['llr'])
    return (pobs-conditional(p_obj, prove['a'], prove['b'])).mean(axis=1)

def replicate_h2(arg):
    seed, delta, N, z, sigma_e, sigma_psi, mu_psi, sigma_dyad = arg
    rng = np.random.default_rng(seed)
    n_arm = N//3; n_dyads = n_arm//2; n_sessions = N//30
    yF = statistic_h2(rng, n_arm, delta, z, sigma_e, sigma_psi, mu_psi, sigma_dyad, False)
    yR = statistic_h2(rng, n_arm, delta, z, sigma_e, sigma_psi, mu_psi, sigma_dyad, True)
    dF = yF.reshape(-1, 2).mean(axis=1); dR = yR.reshape(-1, 2).mean(axis=1)
    sess = np.tile(np.arange(n_sessions), n_dyads//n_sessions+1)[:n_dyads]
    eff_s = rng.normal(0, 1, n_sessions)
    y = np.concatenate([dF+eff_s[sess], dR+eff_s[sess]])
    g = np.concatenate([np.zeros(n_dyads), np.ones(n_dyads)])
    X = np.column_stack([g]+[np.concatenate([sess == j, sess == j]).astype(float) for j in range(n_sessions)])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    resid = y-X@beta; df = len(y)-X.shape[1]
    se = np.sqrt(resid@resid/df*np.linalg.inv(X.T@X)[0, 0])
    crit = tdist.ppf(1-ALPHA, df)
    rej = ((beta[0]+MARGIN)/se > crit) and ((MARGIN-beta[0])/se > crit)
    yy = np.concatenate([yF, yR])
    return bool(rej), float(yy.std(ddof=1)), float(np.corrcoef(yy.reshape(-1, 2)[:, 0], yy.reshape(-1, 2)[:, 1])[0, 1])

def scenario_h2(delta, N, reps, seed, z=.1, sigma_e=4., sigma_psi=.15, mu_psi=.15, sigma_dyad=2.):
    seeds = np.random.SeedSequence(seed).spawn(reps)
    with Pool(PROCESSES) as pool: out = pool.map(replicate_h2, [(sq, delta, N, z, sigma_e, sigma_psi, mu_psi, sigma_dyad) for sq in seeds], chunksize=20)
    p = np.mean([o[0] for o in out]); se_mc = np.sqrt(p*(1-p)/reps)
    return dict(true_difference=delta, N=N, subjects_per_protocol=N//3, replications=reps, power=round(p, 4),
                mc_lower=round(max(0, p-1.96*se_mc), 4), mc_upper=round(min(1, p+1.96*se_mc), 4),
                implied_individual_sd=round(float(np.mean([o[1] for o in out])), 3), implied_dyad_icc=round(float(np.mean([o[2] for o in out])), 3))

def analytic_tost_power(sd, n, icc=.2, delta=0.):
    df = n-2; se = sd*np.sqrt(2*(1+icc)/n); crit = tdist.ppf(1-ALPHA, df)
    def f(v):
        half = crit*np.sqrt(v/df)
        return max(0., norm.cdf((MARGIN-delta)/se-half)-norm.cdf((-MARGIN-delta)/se+half))*chi2.pdf(v, df)
    return quad(f, chi2.ppf(1e-10, df), chi2.ppf(1-1e-10, df), epsabs=1e-9)[0]

def pilot_rule(reps, seed, z=.1, sigma_e=4., sigma_psi=.15, mu_psi=.15, sigma_dyad=2.):
    rng = np.random.default_rng(seed)
    large = np.concatenate([statistic_h2(rng, 2000, 0., z, sigma_e, sigma_psi, mu_psi, sigma_dyad, False) for _ in range(3)])
    true_sd = large.std(ddof=1)
    choices = []; powers = []
    for r in range(reps):
        pilot = np.concatenate([statistic_h2(rng, 12, 0., z, sigma_e, sigma_psi, mu_psi, sigma_dyad, k == 2) for k in range(3)])
        sd_hat = pilot.std(ddof=1)
        N = next((c for c in SAMPLE_SIZES if analytic_tost_power(sd_hat, c//3) >= .8), None)
        choices.append(N if N else 0)
        powers.append(analytic_tost_power(true_sd, (N if N else 600)//3))
    choices = np.array(choices); powers = np.array(powers)
    rows = [dict(chosen_N=int(c), frequency=round(float((choices == c).mean()), 4), mean_realized_power=round(float(powers[choices == c].mean()) if (choices == c).any() else 0., 4)) for c in list(SAMPLE_SIZES)+[0]]
    return dict(true_sd=round(float(true_sd), 3), replications=reps, rule=rows, mean_realized_power=round(float(powers.mean()), 4))

def figure(h1, h2, pilot):
    fig, ax = plt.subplots(1, 3, figsize=(13, 4))
    names = [r['scenario'] for r in h1]; p = [r['rejection_rate'] for r in h1]
    err = [[r['rejection_rate']-r['mc_lower'] for r in h1], [r['mc_upper']-r['rejection_rate'] for r in h1]]
    x = np.arange(len(h1)); cal = calibrated_threshold(); width = .4 if cal is not None else .8
    ax[0].bar(x-(width/2 if cal is not None else 0), p, width, yerr=err, color='#9ac', capsize=3, label='asymptotic threshold 3.841')
    for xi, v in zip(x, p): ax[0].text(xi-(width/2 if cal is not None else 0), v+.03, f'{v:.3f}', ha='center', fontsize=6)
    if cal is not None:
        c, rows = cal
        by = {r['scenario']: r for r in rows}
        q = [by[slug(n)] for n in names]
        pc = [r['rejection_rate'] for r in q]
        errc = [[r['rejection_rate']-r['mc_lower'] for r in q], [r['mc_upper']-r['rejection_rate'] for r in q]]
        ax[0].bar(x+width/2, pc, width, yerr=errc, color='#36a', capsize=3, label=f'calibrated threshold {c:.3f}')
        for xi, v in zip(x, pc): ax[0].text(xi+width/2, v+.03, f'{v:.3f}', ha='center', fontsize=6)
        ax[0].legend(fontsize=7, loc='center left')
    ax[0].axhline(.025, color='k', lw=.8, ls='--'); ax[0].axhline(.8, color='k', lw=.8, ls=':')
    ax[0].set_xticks(x); ax[0].set_xticklabels(names, rotation=25, ha='right', fontsize=8)
    ax[0].set_ylabel('H1 rejection rate'); ax[0].set_ylim(0, 1)
    for d, col in ((0., '#36a'), (1., '#a63')):
        xs = [r['N'] for r in h2 if r['true_difference'] == d and r['scenario'] == 'baseline']; ys = [r['power'] for r in h2 if r['true_difference'] == d and r['scenario'] == 'baseline']
        ax[1].plot(xs, ys, 'o-', color=col, label=f'true difference {d:.0f}')
    ax[1].axhline(.8, color='k', lw=.8, ls=':'); ax[1].axhline(.6, color='k', lw=.8, ls='-.')
    ax[1].set_xlabel('total N'); ax[1].set_ylabel('H2 TOST power'); ax[1].set_ylim(0, 1); ax[1].legend(fontsize=8)
    xs = [str(r['chosen_N']) if r['chosen_N'] else 'redesign' for r in pilot['rule']]; ys = [r['frequency'] for r in pilot['rule']]
    ax[2].bar(xs, ys, color='#8a8'); ax[2].set_ylabel('frequency of the pilot choice'); ax[2].set_xlabel('N set by the rule')
    fig.text(.5, .01, 'Simulation of the analysis procedure. No experimental data.', ha='center', fontsize=8)
    fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(FIG/'full_simulation.png', dpi=160); plt.close(fig)

def read_h1():
    h1 = list(csv.DictReader((DATA/'simulation_H1.csv').open()))
    for r in h1:
        for k in ('rejection_rate', 'mc_lower', 'mc_upper', 'true_contraction', 'anchoring_z'): r[k] = float(r[k])
    return h1

def read_h2():
    h2 = list(csv.DictReader((DATA/'simulation_H2.csv').open()))
    for r in h2:
        r['N'] = int(r['N'])
        for k in ('power', 'mc_lower', 'mc_upper', 'true_difference'): r[k] = float(r[k])
    return h2

def calibrated_threshold():
    files = {f.name[len('replications_H1_'):-4]: f for f in DATA.glob('replications_H1_*.csv')}
    if 'null_no_anchoring' not in files: return None
    def load(f):
        rows = list(csv.DictReader(f.open()))
        return np.array([float(r['estimate']) for r in rows]), np.array([float(r['lr']) for r in rows])
    est0, lr0 = load(files['null_no_anchoring'])
    share = np.mean(est0 > 0)
    c = float(np.quantile(lr0[est0 > 0], 1-ALPHA/share)) if share > ALPHA else 0.0
    rows = []
    for key, f in sorted(files.items()):
        est, lr = load(f)
        rej = (est > 0) & (lr > c); p = rej.mean(); se = np.sqrt(p*(1-p)/len(rej))
        rows.append(dict(scenario=key, replications=len(rej), calibrated_threshold=round(c, 4), rejection_rate=round(p, 4), mc_lower=round(max(0, p-1.96*se), 4), mc_upper=round(min(1, p+1.96*se), 4)))
    csv_out('calibrated_H1.csv', rows)
    return c, rows

def criteria():
    h1 = read_h1(); h2 = read_h2()
    outcomes = []
    for r in h1:
        if r['true_contraction'] == 0.:
            outcomes.append(dict(criterion=f"type-one error at the asymptotic threshold, {r['scenario']}", value=r['mc_upper'], threshold=.035, direction='maximum', passed=r['mc_upper'] <= .035))
        if abs(r['true_contraction']-.15) < 1e-9:
            outcomes.append(dict(criterion=f"H1 power at 0.15 at the asymptotic threshold, {r['scenario']}", value=r['mc_lower'], threshold=.8, direction='minimum', passed=r['mc_lower'] >= .8))
    for sc in sorted(set(r['scenario'] for r in h2)):
        for N in SAMPLE_SIZES:
            r0 = [r for r in h2 if r['scenario'] == sc and r['N'] == N and r['true_difference'] == 0.]
            r1 = [r for r in h2 if r['scenario'] == sc and r['N'] == N and r['true_difference'] == 1.]
            if r0 and r1:
                ok = r0[0]['mc_lower'] >= .8 and r1[0]['mc_lower'] >= .6
                outcomes.append(dict(criterion=f"H2 {sc}, N={N}: zero {r0[0]['mc_lower']:.3f} and one point {r1[0]['mc_lower']:.3f}", value=min(r0[0]['mc_lower']/.8, r1[0]['mc_lower']/.6), threshold=1., direction='minimum', passed=ok))
    cal = calibrated_threshold()
    if cal is not None:
        c, rows = cal
        for r in rows:
            if r['scenario'].startswith('null'):
                outcomes.append(dict(criterion=f"type-one error at calibrated threshold {c:.3f}, {r['scenario']}", value=r['mc_upper'], threshold=.035, direction='maximum', passed=r['mc_upper'] <= .035))
            elif r['scenario'].startswith('contraction_0_15'):
                outcomes.append(dict(criterion=f"H1 power at 0.15 at calibrated threshold {c:.3f}, {r['scenario']}", value=r['mc_lower'], threshold=.8, direction='minimum', passed=r['mc_lower'] >= .8))
    csv_out('criteria_12_3.csv', outcomes)
    for e in outcomes: print(('PASSED ' if e['passed'] else 'NOT PASSED ')+e['criterion'])
    minimum = {sc: next((N for N in SAMPLE_SIZES if any(e['passed'] and e['criterion'].startswith(f'H2 {sc}, N={N}:') for e in outcomes)), None) for sc in sorted(set(r['scenario'] for r in h2))}
    print('Smallest N passing H2 by scenario:', minimum)

if __name__ == '__main__':
    part = sys.argv[1] if len(sys.argv) > 1 else 'all'
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else None
    if part in ('h1', 'all'):
        scen = [('null, no anchoring', 0., 0., 4., .15, SEED+1), ('null, anchoring 0.10', 0., .1, 4., .15, SEED+2),
                ('contraction 0.15, anchoring 0.10', .15, .1, 4., .15, SEED+3), ('contraction 0.25, anchoring 0.10', .25, .1, 4., .15, SEED+4),
                ('contraction 0.15, error 6', .15, .1, 6., .15, SEED+5)]
        if len(sys.argv) > 3: scen = [scen[int(sys.argv[3])]]
        rows = [scenario_h1(nm, 100, mu, z, se, sp, reps or REPLICATIONS_H1, sm) for nm, mu, z, se, sp, sm in scen]
        name = 'simulation_H1.csv' if len(sys.argv) <= 3 else f'simulation_H1_{sys.argv[3]}.csv'
        csv_out(name, rows); print(json.dumps(rows, indent=1, ensure_ascii=False))
    if part in ('boot', 'all'):
        if reps: BOOTSTRAP_REPLICATIONS = reps
        b = dyad_bootstrap(100, .15, .1, 4., .15, SEED+9)
        csv_out('bootstrap_H1_example.csv', [b]); print(json.dumps(b, indent=1))
    if part in ('h2', 'all'):
        rows = []
        for name, se, sdd in (('baseline', 4., 2.), ('high dispersion', 6., 3.)):
            for d in (0., 1.):
                for N in SAMPLE_SIZES:
                    r = scenario_h2(d, N, reps or REPLICATIONS_H2, SEED+100+int(10*d)+N+int(se), sigma_e=se, sigma_dyad=sdd)
                    rows.append(dict(scenario=name, sigma_error=se, sigma_dyad=sdd, **r))
        csv_out('simulation_H2.csv', rows); print(json.dumps(rows, indent=1))
        pilot = pilot_rule(reps or REPLICATIONS_PILOT, SEED+200)
        csv_out('simulation_pilot.csv', pilot['rule'])
        with (DATA/'simulation_pilot_summary.json').open('w') as f: json.dump(pilot, f, indent=1)
        print(json.dumps(pilot, indent=1))
    if part in ('figure', 'all'):
        figure(read_h1(), read_h2(), json.load((DATA/'simulation_pilot_summary.json').open()))
    if part in ('criteria', 'all'):
        criteria()

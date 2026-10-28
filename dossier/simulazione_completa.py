from pathlib import Path
import csv
import sys
import os
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
DATA, FIG = ROOT/'dati_disegno', ROOT/'figure'
DATA.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)

SEME = 20261104
PRIOR = (.4, .6)
ACCURATEZZE = (.6, .7)
INTENSITA = ((.2, .8), (.35, .65))
GRIGLIE = ((20, 90, 55), (30, 100, 65))
MARGINE = 3
ALFA = .025
NODI_EFFETTI = 7
NODI_ERRORE = 5
RHO_ERRORE_VERO = .3
RIPETIZIONI_H1 = 2000
RIPETIZIONI_H2 = 2000
RIPETIZIONI_PILOTA = 2000
REPLICHE_BOOTSTRAP = 1999
CAMPIONI = (300, 360, 420, 480, 540, 600)
SOGLIA_SD = 5.92
PROCESSI = int(os.environ.get('PROCESSI', os.cpu_count() or 1))

def csvout(name, rows):
    with (DATA/name).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def logit(p): return np.log(p/(1-p))
def espit(x): return 1/(1+np.exp(-x))
def incondizionato(p): return 30+60*p
def condizionato(p, a, b): return 30+60*a*p/(a*p+b*(1-p))
def divario(p, a, b): return incondizionato(p)-condizionato(p, a, b)

def genera_prove(rng, n, finestra_intermedia):
    T = 8
    prior = np.zeros((n, T)); a = np.zeros((n, T)); b = np.zeros((n, T))
    llr_vista = np.zeros((n, T)); llr_tutta = np.zeros((n, T))
    lo = np.zeros((n, T)); hi = np.zeros((n, T)); centro = np.zeros((n, T))
    for i in range(n):
        schema = [(p, ab) for p in PRIOR for ab in INTENSITA for r in (0, 1)]
        rng.shuffle(schema)
        formato = rng.permutation([0, 1]*4)
        momento = rng.permutation([0, 1]*4)
        for k, (p, (aa, bb)) in enumerate(schema):
            prior[i, k], a[i, k], b[i, k] = p, aa, bb
            valore_alto = rng.random() < p
            ordine = rng.permutation(2)
            llr = []
            for q in np.array(ACCURATEZZE)[ordine]:
                corretto = rng.random() < q
                dice_alto = corretto if valore_alto else not corretto
                llr.append(np.log(q/(1-q)) if dice_alto else np.log((1-q)/q))
            llr_tutta[i, k] = llr[0]+llr[1]
            llr_vista[i, k] = (llr[0] if momento[k] == 1 else 0.0) if finestra_intermedia else llr_tutta[i, k]
            lo[i, k], hi[i, k], centro[i, k] = GRIGLIE[formato[k]]
    return dict(prior=prior, a=a, b=b, llr=llr_vista, llr_finale=llr_tutta, lo=lo, hi=hi, centro=centro)

def prezzi_latenti(prove, alpha, psi, w0, w1):
    eta = alpha[:, None]+w0*logit(prove['prior'])+w1*prove['llr']
    pt = espit(eta)
    u = incondizionato(pt)
    s = condizionato(pt, prove['a'], prove['b'])+psi[:, None]*divario(pt, prove['a'], prove['b'])
    return u, s

def osserva(rng, prove, u, s, z, sigma, rho, delta_s=0.0):
    m = np.stack([(1-z)*u+z*prove['centro'], (1-z)*s+z*prove['centro']+delta_s], axis=-1)
    comune = rng.standard_normal(m.shape[:-1]+(1,))
    proprio = rng.standard_normal(m.shape)
    soglia = m+sigma*(np.sqrt(rho)*comune+np.sqrt(1-rho)*proprio)
    lo = prove['lo'][..., None]; hi = prove['hi'][..., None]
    k = np.floor(soglia)
    L = np.where(soglia < lo, -np.inf, np.where(soglia >= hi, hi, k))
    R = np.where(soglia < lo, lo, np.where(soglia >= hi, np.inf, k+1))
    return L, R, soglia

def nodi_quadratura():
    xe, we = hermegauss(NODI_EFFETTI); xr, wr = hermegauss(NODI_ERRORE)
    we = we/we.sum(); wr = wr/wr.sum()
    g1, g2, g3 = np.meshgrid(xe, xe, xr, indexing='ij')
    lw = np.log(np.einsum('i,j,k->ijk', we, we, wr)).ravel()
    return g1.ravel(), g2.ravel(), g3.ravel(), lw

G1, G2, G3, GW = nodi_quadratura()

def spacchetta(theta):
    mu_psi, lsg_psi, mu_a, lsg_a, arho, w0, w1, z, lsg_e, arho_e = theta
    return mu_psi, np.exp(lsg_psi), mu_a, np.exp(lsg_a), np.tanh(arho), w0, w1, z, np.exp(lsg_e), espit(arho_e)

def neg_loglik(theta, prove, L, R, vincola_zero=False):
    mu_psi, sg_psi, mu_a, sg_a, rho, w0, w1, z, sg_e, rho_e = spacchetta(theta)
    if vincola_zero: mu_psi = 0.0
    alpha = mu_a+sg_a*G1
    psi = mu_psi+sg_psi*(rho*G1+np.sqrt(1-rho**2)*G2)
    eta = alpha[:, None, None]+w0*logit(prove['prior'])[None]+w1*prove['llr'][None]
    pt = espit(eta)
    u = incondizionato(pt)
    s = condizionato(pt, prove['a'][None], prove['b'][None])+psi[:, None, None]*divario(pt, prove['a'][None], prove['b'][None])
    m = np.stack([(1-z)*u+z*prove['centro'][None], (1-z)*s+z*prove['centro'][None]], axis=-1)+(sg_e*np.sqrt(rho_e)*G3)[:, None, None, None]
    sd = sg_e*np.sqrt(1-rho_e)
    pr = ndtr((R[None]-m)/sd)-ndtr((L[None]-m)/sd)
    lp = np.log(np.clip(pr, 1e-300, None)).sum(axis=(2, 3))
    return -logsumexp(lp+GW[:, None], axis=0).sum()

PARTENZA = np.array([.1, np.log(.1), 0., np.log(.3), 0., 1., 1., .05, np.log(4.), 0.])
LIMITI = [(-.5, 1.5), (np.log(.01), np.log(1.)), (-2, 2), (np.log(.01), np.log(2.)), (-2, 2), (.2, 2.5), (.2, 2.5), (-.3, .8), (np.log(.5), np.log(15.)), (-4, 4)]

def stima(prove, L, R, partenza=None):
    ris = minimize(neg_loglik, PARTENZA if partenza is None else partenza, args=(prove, L, R), method='L-BFGS-B', bounds=LIMITI)
    ris0 = minimize(neg_loglik, ris.x, args=(prove, L, R, True), method='L-BFGS-B', bounds=LIMITI)
    return ris.x, 2*(ris0.fun-ris.fun)

def test_h1(theta, lr):
    return bool((theta[0] > 0) and (lr > 3.841459))

def replica_h1(arg):
    seme, n, mu_psi, z, sigma_e, sigma_psi = arg
    rng = np.random.default_rng(seme)
    prove = genera_prove(rng, n, True)
    alpha = rng.normal(0, .3, n)
    psi = mu_psi+sigma_psi*rng.standard_normal(n)
    u, s = prezzi_latenti(prove, alpha, psi, 1., 1.)
    L, R, _ = osserva(rng, prove, u, s, z, sigma_e, RHO_ERRORE_VERO)
    theta, lr = stima(prove, L, R)
    return test_h1(theta, lr), theta[0], theta[7], espit(theta[9])

def scenario_h1(nome, n, mu_psi, z, sigma_e, sigma_psi, reps, seme):
    semi = np.random.SeedSequence(seme).spawn(reps)
    args = [(sq, n, mu_psi, z, sigma_e, sigma_psi) for sq in semi]
    with Pool(PROCESSI) as pool: out = pool.map(replica_h1, args, chunksize=1)
    rif = np.array([o[0] for o in out], float); stime = np.array([o[1] for o in out])
    p = rif.mean(); se = np.sqrt(p*(1-p)/reps)
    return dict(scenario=nome, persone_S=n, contrazione_vera=mu_psi, sd_contrazione=sigma_psi, ancoraggio_z=z, sigma_errore=sigma_e,
                rho_errore_vero=RHO_ERRORE_VERO, repliche=reps, tasso_rifiuto=round(p, 4), mc_inf=round(max(0, p-1.96*se), 4), mc_sup=round(min(1, p+1.96*se), 4),
                media_stima=round(stime.mean(), 4), distorsione=round(stime.mean()-mu_psi, 4), rmse=round(np.sqrt(((stime-mu_psi)**2).mean()), 4),
                media_z_stimato=round(float(np.mean([o[2] for o in out])), 4), media_rho_errore_stimato=round(float(np.mean([o[3] for o in out])), 4))

DATI_BOOT = {}

def replica_boot(arg):
    seme, theta = arg
    rng = np.random.default_rng(seme)
    prove, L, R = DATI_BOOT['prove'], DATI_BOOT['L'], DATI_BOOT['R']
    diadi = np.arange(len(L)).reshape(-1, 2)
    idx = diadi[rng.integers(0, len(diadi), len(diadi))].ravel()
    sub = {k: v[idx] for k, v in prove.items()}
    ris = minimize(neg_loglik, theta, args=(sub, L[idx], R[idx]), method='L-BFGS-B', bounds=LIMITI)
    return ris.x[0]

def bootstrap_diade(n, mu_psi, z, sigma_e, sigma_psi, seme):
    rng = np.random.default_rng(seme)
    prove = genera_prove(rng, n, True)
    alpha = rng.normal(0, .3, n); psi = mu_psi+sigma_psi*rng.standard_normal(n)
    u, s = prezzi_latenti(prove, alpha, psi, 1., 1.)
    L, R, _ = osserva(rng, prove, u, s, z, sigma_e, RHO_ERRORE_VERO)
    theta, lr = stima(prove, L, R)
    DATI_BOOT.update(prove=prove, L=L, R=R)
    semi = np.random.SeedSequence(seme+1).spawn(REPLICHE_BOOTSTRAP)
    with Pool(PROCESSI) as pool: stime = np.array(pool.map(replica_boot, [(sq, theta) for sq in semi], chunksize=1))
    return dict(contrazione_vera=mu_psi, stima_puntuale=round(theta[0], 4), lr=round(lr, 3), rifiuto_lr=test_h1(theta, lr),
                repliche_bootstrap=REPLICHE_BOOTSTRAP, sd_bootstrap=round(stime.std(ddof=1), 4),
                limite_inferiore_base=round(float(np.quantile(2*theta[0]-stime, .025)), 4),
                limite_inferiore_percentile=round(float(np.quantile(stime, .025)), 4))

def statistica_h2(rng, n_persone, delta, z, sigma_e, sigma_psi, mu_psi, sigma_diade, protocollo_r):
    prove = genera_prove(rng, n_persone, False)
    alpha = rng.normal(0, .3, n_persone)
    psi = mu_psi+sigma_psi*rng.standard_normal(n_persone)
    u, s = prezzi_latenti(prove, alpha, psi, 1., 1.)
    eff_diade = np.repeat(rng.normal(0, sigma_diade, n_persone//2), 2)
    L, R, soglia = osserva(rng, prove, u+eff_diade[:, None], s+eff_diade[:, None], z, sigma_e, RHO_ERRORE_VERO, delta if protocollo_r else 0.0)
    pobs = np.clip(np.floor(soglia[..., 1]), 30, 90)
    p_obj = espit(logit(prove['prior'])+prove['llr'])
    return (pobs-condizionato(p_obj, prove['a'], prove['b'])).mean(axis=1)

def replica_h2(arg):
    seme, delta, N, z, sigma_e, sigma_psi, mu_psi, sigma_diade = arg
    rng = np.random.default_rng(seme)
    n_arm = N//3; n_diadi = n_arm//2; n_sessioni = N//30
    yF = statistica_h2(rng, n_arm, delta, z, sigma_e, sigma_psi, mu_psi, sigma_diade, False)
    yR = statistica_h2(rng, n_arm, delta, z, sigma_e, sigma_psi, mu_psi, sigma_diade, True)
    dF = yF.reshape(-1, 2).mean(axis=1); dR = yR.reshape(-1, 2).mean(axis=1)
    sess = np.tile(np.arange(n_sessioni), n_diadi//n_sessioni+1)[:n_diadi]
    eff_s = rng.normal(0, 1, n_sessioni)
    y = np.concatenate([dF+eff_s[sess], dR+eff_s[sess]])
    g = np.concatenate([np.zeros(n_diadi), np.ones(n_diadi)])
    X = np.column_stack([g]+[np.concatenate([sess == j, sess == j]).astype(float) for j in range(n_sessioni)])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    resid = y-X@beta; df = len(y)-X.shape[1]
    se = np.sqrt(resid@resid/df*np.linalg.inv(X.T@X)[0, 0])
    crit = tdist.ppf(1-ALFA, df)
    rif = ((beta[0]+MARGINE)/se > crit) and ((MARGINE-beta[0])/se > crit)
    yy = np.concatenate([yF, yR])
    return bool(rif), float(yy.std(ddof=1)), float(np.corrcoef(yy.reshape(-1, 2)[:, 0], yy.reshape(-1, 2)[:, 1])[0, 1])

def scenario_h2(delta, N, reps, seme, z=.1, sigma_e=4., sigma_psi=.15, mu_psi=.15, sigma_diade=2.):
    semi = np.random.SeedSequence(seme).spawn(reps)
    with Pool(PROCESSI) as pool: out = pool.map(replica_h2, [(sq, delta, N, z, sigma_e, sigma_psi, mu_psi, sigma_diade) for sq in semi], chunksize=20)
    p = np.mean([o[0] for o in out]); se_mc = np.sqrt(p*(1-p)/reps)
    return dict(differenza_vera=delta, N=N, persone_per_protocollo=N//3, repliche=reps, potenza=round(p, 4),
                mc_inf=round(max(0, p-1.96*se_mc), 4), mc_sup=round(min(1, p+1.96*se_mc), 4),
                sd_individuale_implicita=round(float(np.mean([o[1] for o in out])), 3), icc_diade_implicito=round(float(np.mean([o[2] for o in out])), 3))

def potenza_tost_analitica(sd, n, icc=.2, delta=0.):
    df = n-2; se = sd*np.sqrt(2*(1+icc)/n); crit = tdist.ppf(1-ALFA, df)
    def f(v):
        half = crit*np.sqrt(v/df)
        return max(0., norm.cdf((MARGINE-delta)/se-half)-norm.cdf((-MARGINE-delta)/se+half))*chi2.pdf(v, df)
    return quad(f, chi2.ppf(1e-10, df), chi2.ppf(1-1e-10, df), epsabs=1e-9)[0]

def regola_pilota(reps, seme, z=.1, sigma_e=4., sigma_psi=.15, mu_psi=.15, sigma_diade=2.):
    rng = np.random.default_rng(seme)
    grande = np.concatenate([statistica_h2(rng, 2000, 0., z, sigma_e, sigma_psi, mu_psi, sigma_diade, False) for _ in range(3)])
    sd_vera = grande.std(ddof=1)
    scelte = []; potenze = []
    for r in range(reps):
        pil = np.concatenate([statistica_h2(rng, 12, 0., z, sigma_e, sigma_psi, mu_psi, sigma_diade, k == 2) for k in range(3)])
        sd_hat = pil.std(ddof=1)
        N = next((c for c in CAMPIONI if potenza_tost_analitica(sd_hat, c//3) >= .8), None)
        scelte.append(N if N else 0)
        potenze.append(potenza_tost_analitica(sd_vera, (N if N else 600)//3))
    scelte = np.array(scelte); potenze = np.array(potenze)
    righe = [dict(N_scelto=int(c), frequenza=round(float((scelte == c).mean()), 4), potenza_reale_media=round(float(potenze[scelte == c].mean()) if (scelte == c).any() else 0., 4)) for c in list(CAMPIONI)+[0]]
    return dict(sd_vera=round(float(sd_vera), 3), repliche=reps, regola=righe, potenza_reale_media=round(float(potenze.mean()), 4))

def figura(h1, h2, pil):
    fig, ax = plt.subplots(1, 3, figsize=(13, 4))
    nomi = [r['scenario'] for r in h1]; p = [r['tasso_rifiuto'] for r in h1]
    err = [[r['tasso_rifiuto']-r['mc_inf'] for r in h1], [r['mc_sup']-r['tasso_rifiuto'] for r in h1]]
    ax[0].bar(range(len(h1)), p, yerr=err, color='#9ac', capsize=3)
    ax[0].axhline(.025, color='k', lw=.8, ls='--'); ax[0].axhline(.8, color='k', lw=.8, ls=':')
    ax[0].set_xticks(range(len(h1))); ax[0].set_xticklabels(nomi, rotation=25, ha='right', fontsize=8)
    ax[0].set_ylabel('tasso di rifiuto H1'); ax[0].set_ylim(0, 1)
    for d, col in ((0., '#36a'), (1., '#a63')):
        xs = [r['N'] for r in h2 if r['differenza_vera'] == d and r['scenario'] == 'base']; ys = [r['potenza'] for r in h2 if r['differenza_vera'] == d and r['scenario'] == 'base']
        ax[1].plot(xs, ys, 'o-', color=col, label=f'differenza vera {d:.0f}')
    ax[1].axhline(.8, color='k', lw=.8, ls=':'); ax[1].axhline(.6, color='k', lw=.8, ls='-.')
    ax[1].set_xlabel('N totale'); ax[1].set_ylabel('potenza TOST H2'); ax[1].set_ylim(0, 1); ax[1].legend(fontsize=8)
    xs = [str(r['N_scelto']) if r['N_scelto'] else 'ridisegno' for r in pil['regola']]; ys = [r['frequenza'] for r in pil['regola']]
    ax[2].bar(xs, ys, color='#8a8'); ax[2].set_ylabel('frequenza della scelta del pilota'); ax[2].set_xlabel('N fissato dalla regola')
    fig.text(.5, .01, 'Simulazione della procedura di analisi. Nessun dato sperimentale.', ha='center', fontsize=8)
    fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(FIG/'simulazione_completa.png', dpi=160); plt.close(fig)

def leggi_h1():
    h1 = list(csv.DictReader((DATA/'simulazione_H1.csv').open()))
    for r in h1:
        for k in ('tasso_rifiuto', 'mc_inf', 'mc_sup', 'contrazione_vera', 'ancoraggio_z'): r[k] = float(r[k])
    return h1

def leggi_h2():
    h2 = list(csv.DictReader((DATA/'simulazione_H2.csv').open()))
    for r in h2:
        r['N'] = int(r['N'])
        for k in ('potenza', 'mc_inf', 'mc_sup', 'differenza_vera'): r[k] = float(r[k])
    return h2

def criteri():
    h1 = leggi_h1(); h2 = leggi_h2()
    esiti = []
    for r in h1:
        if r['contrazione_vera'] == 0.:
            esiti.append(dict(criterio=f"errore di primo tipo, {r['scenario']}", valore=r['mc_sup'], soglia=.035, verso='massimo', superato=r['mc_sup'] <= .035))
        if abs(r['contrazione_vera']-.15) < 1e-9:
            esiti.append(dict(criterio=f"potenza H1 a 0,15, {r['scenario']}", valore=r['mc_inf'], soglia=.8, verso='minimo', superato=r['mc_inf'] >= .8))
    for sc in sorted(set(r['scenario'] for r in h2)):
        for N in CAMPIONI:
            r0 = [r for r in h2 if r['scenario'] == sc and r['N'] == N and r['differenza_vera'] == 0.]
            r1 = [r for r in h2 if r['scenario'] == sc and r['N'] == N and r['differenza_vera'] == 1.]
            if r0 and r1:
                ok = r0[0]['mc_inf'] >= .8 and r1[0]['mc_inf'] >= .6
                esiti.append(dict(criterio=f"H2 {sc}, N={N}: zero {r0[0]['mc_inf']:.3f} e un punto {r1[0]['mc_inf']:.3f}", valore=min(r0[0]['mc_inf']/.8, r1[0]['mc_inf']/.6), soglia=1., verso='minimo', superato=ok))
    csvout('criteri_12_3.csv', esiti)
    for e in esiti: print(('SUPERATO ' if e['superato'] else 'NON SUPERATO ')+e['criterio'])
    minimo = {sc: next((N for N in CAMPIONI if any(e['superato'] and e['criterio'].startswith(f'H2 {sc}, N={N}:') for e in esiti)), None) for sc in sorted(set(r['scenario'] for r in h2))}
    print('N minimo che supera H2 per scenario:', minimo)

if __name__ == '__main__':
    parte = sys.argv[1] if len(sys.argv) > 1 else 'tutto'
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else None
    if parte in ('h1', 'tutto'):
        scen = [('nulla, senza ancoraggio', 0., 0., 4., .15, SEME+1), ('nulla, ancoraggio 0,10', 0., .1, 4., .15, SEME+2),
                ('contrazione 0,15, ancoraggio 0,10', .15, .1, 4., .15, SEME+3), ('contrazione 0,25, ancoraggio 0,10', .25, .1, 4., .15, SEME+4),
                ('contrazione 0,15, errore 6', .15, .1, 6., .15, SEME+5)]
        if len(sys.argv) > 3: scen = [scen[int(sys.argv[3])]]
        righe = [scenario_h1(nm, 100, mu, z, se, sp, reps or RIPETIZIONI_H1, sm) for nm, mu, z, se, sp, sm in scen]
        nome = 'simulazione_H1.csv' if len(sys.argv) <= 3 else f'simulazione_H1_{sys.argv[3]}.csv'
        csvout(nome, righe); print(json.dumps(righe, indent=1, ensure_ascii=False))
    if parte in ('boot', 'tutto'):
        if reps: REPLICHE_BOOTSTRAP = reps
        b = bootstrap_diade(100, .15, .1, 4., .15, SEME+9)
        csvout('bootstrap_H1_esempio.csv', [b]); print(json.dumps(b, indent=1))
    if parte in ('h2', 'tutto'):
        righe = []
        for nome, se, sdd in (('base', 4., 2.), ('dispersione alta', 6., 3.)):
            for d in (0., 1.):
                for N in CAMPIONI:
                    r = scenario_h2(d, N, reps or RIPETIZIONI_H2, SEME+100+int(10*d)+N+int(se), sigma_e=se, sigma_diade=sdd)
                    righe.append(dict(scenario=nome, sigma_errore=se, sigma_diade=sdd, **r))
        csvout('simulazione_H2.csv', righe); print(json.dumps(righe, indent=1))
        pil = regola_pilota(reps or RIPETIZIONI_PILOTA, SEME+200)
        csvout('simulazione_pilota.csv', pil['regola'])
        with (DATA/'simulazione_pilota_riassunto.json').open('w') as f: json.dump(pil, f, indent=1)
        print(json.dumps(pil, indent=1))
    if parte in ('figura', 'tutto'):
        figura(leggi_h1(), leggi_h2(), json.load((DATA/'simulazione_pilota_riassunto.json').open()))
    if parte in ('criteri', 'tutto'):
        criteri()

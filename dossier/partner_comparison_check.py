import csv, sys
from pathlib import Path
import numpy as np
from scipy.stats import t as tdist, binom, rankdata, norm
lg = lambda p: np.log(p/(1-p)); ex = lambda x: 1/(1+np.exp(-x))
RULES = np.array([(0.35, 0.65), (0.20, 0.80), (0.05, 0.95)])
def U(p): return 30+60*p
def C(p, a, b): return 30+60*a*p/(a*p+b*(1-p))
def fmt(rng, shape):
    f = rng.random(shape) < .5
    return np.where(f, 20., 30.), np.where(f, 90., 100.), np.where(f, 55., 65.)
def certs(rng, prior, n_seen):
    v90 = rng.random(prior.shape) < prior
    first70 = rng.random(prior.shape) < .5
    acc1 = np.where(first70, .7, .6); acc2 = np.where(first70, .6, .7)
    h1 = rng.random(prior.shape) < np.where(v90, acc1, 1-acc1)
    h2 = rng.random(prior.shape) < np.where(v90, acc2, 1-acc2)
    l1 = np.where(h1, np.log(acc1/(1-acc1)), np.log((1-acc1)/acc1))
    l2 = np.where(h2, np.log(acc2/(1-acc2)), np.log((1-acc2)/acc2))
    return np.where(n_seen >= 1, l1, 0.)+np.where(n_seen >= 2, l2, 0.)
def stated(rng, price, center, lo, hi, z, shade, e):
    return np.clip(np.floor((1-z)*price+z*center+shade+e), lo, hi)
def gen(rng, n, chi_mean, z, shade_mean, sigma_e=4., rho=.3, final=False, z_cal=None):
    z_cal = z if z_cal is None else z_cal
    alpha = rng.normal(0, .3, (n, 2)); chi = chi_mean+.15*rng.standard_normal((n, 2))
    shade = rng.normal(shade_mean, 1., (n, 2)) if shade_mean != 0 else np.zeros((n, 2))
    cells = np.array([(p, r) for p in (0.4, 0.6) for r in range(3)])
    prior = np.tile(cells[:, 0], (n, 1)); r = np.tile(cells[:, 1].astype(int), (n, 1))
    a = RULES[r, 0]; b = RULES[r, 1]
    n_seen = np.full(prior.shape, 2) if final else rng.integers(0, 2, prior.shape)
    llr = certs(rng, prior, n_seen)
    who1 = np.tile(np.array([0, 1, 0, 1, 0, 1]), (n, 1)); who1 = np.where(rng.random((n, 1)) < .5, who1, 1-who1)
    al1 = np.take_along_axis(alpha, who1, 1); al2 = np.take_along_axis(alpha, 1-who1, 1)
    ch2 = np.take_along_axis(chi, 1-who1, 1)
    sh1 = np.take_along_axis(shade, who1, 1); sh2 = np.take_along_axis(shade, 1-who1, 1)
    pa = ex(al1+lg(prior)+llr); pb = ex(al2+lg(prior)+llr)
    lo1, hi1, c1 = fmt(rng, prior.shape); lo2, hi2, c2 = fmt(rng, prior.shape)
    s = C(pb, a, b)+ch2*(U(pb)-C(pb, a, b))
    T1 = stated(rng, U(pa), c1, lo1, hi1, z, sh1, sigma_e*rng.standard_normal(prior.shape))
    T2 = stated(rng, s, c2, lo2, hi2, z, sh2, sigma_e*rng.standard_normal(prior.shape))
    pc = ex(lg(prior)+llr)
    res_s = np.concatenate([np.clip(T1, 30, 90)+.5-U(pc), np.clip(T2, 30, 90)+.5-C(pc, a, b)], 1); cen_s = np.concatenate([c1, c2], 1)
    pj = np.tile(np.repeat(cells[:, 0], 2), (n, 2, 1)); rj = np.tile(np.repeat(cells[:, 1].astype(int), 2), (n, 2, 1))
    aj = RULES[rj, 0]; bj = RULES[rj, 1]
    nsj = np.full(pj.shape, 2) if final else rng.integers(0, 2, pj.shape)
    lj = certs(rng, pj, nsj); pt = ex(alpha[:, :, None]+lg(pj)+lj)
    loj, hij, cj = fmt(rng, pj.shape)
    com = rng.standard_normal(pj.shape); e1 = sigma_e*(np.sqrt(rho)*com+np.sqrt(1-rho)*rng.standard_normal(pj.shape)); e2 = sigma_e*(np.sqrt(rho)*com+np.sqrt(1-rho)*rng.standard_normal(pj.shape))
    sj = C(pt, aj, bj)+chi[:, :, None]*(U(pt)-C(pt, aj, bj))
    J1 = stated(rng, U(pt), cj, loj, hij, z, shade[:, :, None], e1); J2 = stated(rng, sj, cj, loj, hij, z, shade[:, :, None], e2)
    pcj = ex(lg(pj)+lj)
    res_j = np.concatenate([(np.clip(J1, 30, 90)+.5-U(pcj)).reshape(n, -1), (np.clip(J2, 30, 90)+.5-C(pcj, aj, bj)).reshape(n, -1)], 1)
    cen_j = np.concatenate([cj.reshape(n, -1), cj.reshape(n, -1)], 1)
    res = np.concatenate([res_s, res_j], 1); cen = np.concatenate([cen_s, cen_j], 1)
    v = np.tile(np.array([36., 48., 66., 78., 36., 48., 66., 78.]), (n, 2, 1))
    cv = np.tile(np.array([55.]*4+[65.]*4), (n, 2, 1)); lov = cv-35; hiv = cv+35
    Tv = stated(rng, v, cv, lov, hiv, z_cal, shade[:, :, None], sigma_e*rng.standard_normal(v.shape))
    return dict(T1=T1, T2=T2, c1=c1, c2=c2, a=a, b=b, res=res, cen=cen, y=(Tv+.5-v).reshape(n, -1), x=(cv-v).reshape(n, -1))
def raw_stat(d):
    ph = np.clip((d['T1']+.5-30)/60, .005, .995)
    return (d['T2']+.5-C(ph, d['a'], d['b'])).mean(1)
def corrected(d, zh, sh, idx=None):
    T1, T2, c1, c2, a, b = (d[k] if idx is None else d[k][idx] for k in ('T1', 'T2', 'c1', 'c2', 'a', 'b'))
    zh = np.asarray(zh)[..., None, None]; sh = np.asarray(sh)[..., None, None]
    P1 = (T1+.5-zh*c1-sh)/(1-zh); P2 = (T2+.5-zh*c2-sh)/(1-zh)
    ph = np.clip((P1-30)/60, .005, .995)
    return (P2-C(ph, a, b)).mean(-1).mean(-1)
def cal_fit(x, y):
    n = x.shape[-1]*x.shape[-2] if x.ndim > 1 else x.size
    sx = x.sum((-1, -2)); sy = y.sum((-1, -2)); sxx = (x*x).sum((-1, -2)); sxy = (x*y).sum((-1, -2))
    zh = (n*sxy-sx*sy)/(n*sxx-sx*sx); sh = (sy-zh*sx)/n
    return zh, sh
def fmt_fit(res, cen, x, y):
    hi = cen == 65.
    zh = ((res*hi).sum((-1, -2))/hi.sum((-1, -2))-(res*~hi).sum((-1, -2))/(~hi).sum((-1, -2)))/10
    sh = (y-zh[..., None, None]*x).mean((-1, -2))
    return zh, sh
def one(rng, n, B, **kw):
    d = gen(rng, n, **kw)
    D = raw_stat(d); m = D.mean(); se = D.std(ddof=1)/np.sqrt(n)
    out = {'t': m/se > tdist.ppf(.975, n-1), 'raw_mean': m}
    nz = D[D != 0]; out['sign'] = binom.sf((nz > 0).sum()-1, len(nz), .5) <= .025
    rk = rankdata(np.abs(nz)); w = rk[nz > 0].sum(); mu = len(nz)*(len(nz)+1)/4; sd = np.sqrt(len(nz)*(len(nz)+1)*(2*len(nz)+1)/24)
    out['wilcoxon'] = (w-mu)/sd > 1.96
    idx = rng.integers(0, n, (B, n))
    zc, sc = cal_fit(d['x'][None], d['y'][None]); zb, sb = cal_fit(d['x'][idx], d['y'][idx])
    Dc = corrected(d, zc, sc)[0]; Db = corrected(d, zb, sb, idx)
    out['cal'] = Dc/Db.std(ddof=1) > 1.96; out['cal_mean'] = Dc; out['cal_z'] = zc[0]
    zf, sf = fmt_fit(d['res'][None], d['cen'][None], d['x'][None], d['y'][None]); zfb, sfb = fmt_fit(d['res'][idx], d['cen'][idx], d['x'][idx], d['y'][idx])
    Df = corrected(d, zf, sf)[0]; Dfb = corrected(d, zfb, sfb, idx)
    out['fmt'] = Df/Dfb.std(ddof=1) > 1.96; out['fmt_mean'] = Df; out['fmt_z'] = zf[0]
    return out
def run(label, n, reps, B=199, seed=1, **kw):
    rng = np.random.default_rng(seed)
    o = [one(rng, n, B, **kw) for _ in range(reps)]
    g = lambda k: float(np.mean([q[k] for q in o]))
    row = dict(scenario=label, pairs=n, replications=reps, uncorrected_t=g('t'), uncorrected_sign=g('sign'), uncorrected_wilcoxon=g('wilcoxon'),
        uncorrected_mean=g('raw_mean'), announced_value_correction=g('cal'), announced_value_mean=g('cal_mean'), announced_value_attraction=g('cal_z'),
        format_correction=g('fmt'), format_mean=g('fmt_mean'), format_attraction=g('fmt_z'))
    print(row, flush=True)
    return row
if __name__ == '__main__':
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    rows = [
        run('protocol S, intermediate request, no neglect, no attraction, no understatement', 50, R, seed=11, chi_mean=0., z=0., shade_mean=0.),
        run('protocol S, intermediate request, no neglect, attraction 0.02, understatement 1', 50, R, seed=12, chi_mean=0., z=.02, shade_mean=-1.),
        run('protocol S, intermediate request, no neglect, attraction 0.05, understatement 1', 50, R, seed=13, chi_mean=0., z=.05, shade_mean=-1.),
        run('protocol S, intermediate request, no neglect, attraction 0.10, understatement 1', 50, R, seed=14, chi_mean=0., z=.10, shade_mean=-1.),
        run('protocol S, intermediate request, neglect 0.15, attraction 0.10, understatement 1', 50, R, seed=15, chi_mean=.15, z=.10, shade_mean=-1.),
        run('protocol S, intermediate request, neglect 0.25, attraction 0.10, understatement 1', 50, R, seed=16, chi_mean=.25, z=.10, shade_mean=-1.),
        run('protocol S, intermediate request, no neglect, attraction 0.10 in trials and 0.05 in announced-value lists', 50, R, seed=17, chi_mean=0., z=.10, shade_mean=-1., z_cal=.05),
        run('all protocols, final decision, no neglect, attraction 0.10, understatement 1', 150, R, seed=21, chi_mean=0., z=.10, shade_mean=-1., final=True),
        run('all protocols, final decision, neglect 0.15, attraction 0.10, understatement 1', 150, R, seed=22, chi_mean=.15, z=.10, shade_mean=-1., final=True)]
    out = Path(__file__).resolve().parent/'design_data'/'partner_comparison_check.csv'
    with out.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

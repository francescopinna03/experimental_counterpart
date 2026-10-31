# Revision log

## Version 2.0, October 9, 2026

Design planned, not executed. Version 2 replaces protocol 1.1. The confirmatory core is module X in prices. Depth and bridge remain exploratory.

| Proposal | Decision | Reason |
|:--|:--|:--|
| Certificates at 60% and 70% | Adopted | The audit confirms 3.40 discriminating trials against 1.05 in the old binary task |
| Removal of the scoring rule and the calculator | Adopted | The behavioral incentive problem documented by Danz and coauthors is relevant |
| Two prices to separate posterior and selection | Adopted with explicit assumptions | The conditional benchmark must be built from the posterior implied by the first price |
| Exact individual ratio from lists in steps of five | Corrected | Lists give intervals, and the error in the two prices makes the ratio nonlinear and biased |
| Price grid | Step one, formats 20-90 and 30-100 | Same length and common economic prices, different centers to test anchoring |
| Two intensities as a sufficient check | Scaled down | A 10% attraction toward 57.5 generates apparent contractions 0.1098 and 0.1072 |
| Calibration | Eight certain-value trials in addition to the sixteen urns | The urns do not check an error specific to the price instrument |
| Inactive slot paid through the final decision | Not adopted | With three equiprobable slots the final decision weighs 1, 2/3 and 1/3 in F, S and R |
| Inactive slot | Reserve at 50% | Equivalent to an always-available policy, and keeps the payment of the common decisions |
| No monetary risk | Binary prize kept | With direct monetary payments the reservation price would depend on risk preferences |
| 11-20 in the K core with two-step separation | Excluded from the core | Adjacent levels and a mixed equilibrium do not meet the constraint |
| K battery | Three selected games, six trials with role exchange | Maximin criterion on efficient information in an explicit benchmark |
| Equivalent-probability lists | Kept with a complementarity check | They are also sensitive to preferences over the source of uncertainty |
| Sixteen urns as an upper bound on noise | Claim removed | Precision does not transfer automatically across tasks |
| Variation identity as a test on raw prices | Corrected for the measurement model | With independent noise the spurious gap equals three error variances |
| Sample of 300 | Base conditional on the pilot criterion | 80% TOST power in the central scenario requires an SD of about 5.92 or less |
| χ recovered from the thresholds | Named effective contraction ψ | It equals χ in the static restriction, not automatically in the dynamic bridge |

The two primary hypotheses are the mean effective contraction in S and the average F-R equivalence of the observable final price within three points. The specification of H1 includes censoring and the measurement model.

## Update of October 15, 2026

The course experiment is anchored to the public version of the preprint, SSRN 7251718, August 8, 2026. The bibliographic entry of the protocol replaces the file reference with the SSRN citation and gives the exact anchors: Section 4.2 with Propositions 4.2 and 4.3 for the transformation of the joint law, Theorem 9.1 for the observation of processes, equation (77) and Section 13.1 for efficient information. The motivation declares the design an implementation of the measurements requested by Sections 10.3 and 12.4 and by the conclusions of the preprint, and distinguishes it from the three-game battery of Section 12. Working references in the text were replaced by complete citations. Numbers, tables and programs are unchanged.

## Update of October 28, 2026

Section 12.4 was added with the full simulation of the analysis procedure from the declared measurement model, the program full_simulation.py and the figure full_simulation.png. The table of Section 12.2 is qualified as an analytic calculation. The simulation program reached its final form, with error correlation between the lists, parallel execution and the criteria part, and the materials were published in the repository experimental_counterpart. Programs, data files and figures were renamed in English.

## Version 2.1, October 31, 2026

The certifying run of the simulation was completed, with 2,000 replications per scenario. The asymptotic likelihood-ratio test of H1 rejects a true null in 3.2 percent of replications, above the tolerance of Section 12.3, so the critical value is calibrated by simulation at 4.279, with a level of 2.25 percent on independent null replications and power of 99.45 percent at a contraction of 0.15. Every criterion of Section 12.3 is met with the calibrated value. Section 12.4 reports the run in full.

The primary test of H1 changes, before any data. The one-sided likelihood-ratio test with a critical value calibrated by parametric bootstrap under the null becomes primary, because its level is verified by simulation, while the level of the studentized dyad bootstrap is not and cannot be certified at reasonable cost with the current estimator. The dyad bootstrap is kept as a robustness check. Two rules are declared in advance in Section 10.1: if the goodness-of-fit check or the independent-placebo check rejects the measurement model, the dyad bootstrap becomes primary, and if the checks pass and the two procedures disagree, the calibrated test decides and both results are reported.

The dossier is translated into English. The extracts (analysis plan, instructions, quiz and script, presentation outline) are generated from the corresponding sections of the protocol, so that they cannot diverge from it.

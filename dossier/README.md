# Experimental design materials

Version 2.1, October 31, 2026. It replaces version 2.0 of October 9, 2026. No experiment or pilot has been run.

- `Protocol_dynamic_identification.md` is the complete editable source.
- `Revision_log.md` records the decisions of the revision and their reasons.
- `Participant_instructions.md` contains only the instructions, to be adapted to each protocol before implementation.
- `Quiz_and_script.md` contains the solutions reserved for the experimenter.
- `Analysis_plan.md` contains the sections on hypotheses, dynamics, sample and the simulation of the analysis procedure.
- `Presentation_outline.md` contains the outline of the seven slides of the first presentation.
- `design_checks.py` verifies the identities and generates posteriors, templates, the anchoring counterexample and the TOST scenarios.
- `select_K_battery.py` selects three games and produces the Fisher diagnostics of the recursive benchmark.
- `make_facsimile.py` draws the illustrative task screen.
- `full_simulation.py` simulates the entire analysis procedure from the declared measurement model and calibrates the critical value of the first hypothesis, in parts (`h1`, `h2`, `boot`, `figure`, `criteria`, `all`).
- `design_data/` contains reproducible CSV and JSON files.
- `figures/` contains the plot of predictions and power, the figure of the simulation and a facsimile of the task.
- `word_layout.py` applies the style to the DOCX produced by Pandoc, preserving native equations, and `layout.tex` is the LaTeX header for the PDF export.

To reproduce the calculations use Python 3 with numpy, scipy and matplotlib, and run the programs in this directory. The certifying simulation takes about two hours per scenario of the first hypothesis on an eight-core laptop. The Markdown text can be converted to DOCX with Pandoc and then formatted with `word_layout.py`, or to PDF with Pandoc and `layout.tex`.

The package does not contain the course teaching materials, a ready collection app or an estimate of the SBB bridge. It contains the design and the declared checks. Before any execution, implementation, pilot and freezing according to the criterion preregistered in the dossier are required.

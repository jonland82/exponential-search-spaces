# Easy and hard inputs in a 3D representative space

[Interactive plot](input_space.html) | [PNG](input_space.png) | [PDF](input_space.pdf)

Default: 576 unscaled cases from 144 lists,
430 completed and 146 unresolved
under the frozen 8L work allowance. Circles indicate completed exact decisions;
crosses indicate unresolved runs. Colors identify exact full-list classes.

The interactive view supports rotation, zoom, type toggles, easy/hard filtering,
paired scaled encodings, and point labels/inspection. Choose among 15-feature
PCA, five-distance PCA, and directly interpretable input axes. HTML includes
Plotly and the data, so no server or internet connection is required.

Classes overlap: hover/click shows every certified type. Display ties prefer a
matching intended generator class, then coordinate order. Generator names alone
are never treated as certificates. Full-list features are extracted separately:
zero distances on an empty reduced kernel do not create spurious memberships.

Nine unscaled progression-class inputs are known easy structurally but unresolved
by the original reference portfolio. The plot preserves both facts. Other solved
inputs do not establish new polynomial-time classes; unresolved runs do not
establish intrinsic hardness.

PCA is standardized and fitted on unscaled feature rows, with no labels used.
Projection is a visualization, not a retrained completion model or a proof that
classes are separable. Paired encodings and targets from one list are dependent.

`points.csv`/`points.json` preserve per-input labels; `projection.json` records
PCA transforms, variance and counts. `manifest.json` records input/output hashes.
This adds no new solver measurements and changes no frozen evidence.

## Prediction overlays

The default Mistakes lens distinguishes correct easy, correct hard, missed hard
and false hard predictions. Shape always preserves the observed solver outcome:
circle = completed; cross = unresolved. The Predictions lens colors the model's
easy/hard estimate; Structure restores certified-type colors.

Choose a saved model and focus on all mistakes, missed hard cases, false hard
cases or correct predictions. Faint context keeps the rest of the eligible cloud
visible, without including it in focused counts or CSV exports. Legend entries
also select a category. Click a point for predicted/observed labels, probabilities,
all model estimates, empirical neighbor distances, weights and exact types.

Prediction threshold is fixed at p(easy)=0.5. Overview statistics refer to inputs
eligible under encoding, structural-type and observed-outcome filters, before
the mistake focus. Changing models or focus preserves point positions, camera
and axis ranges. The frame changes only with projection or included encodings.
The CSV export includes the selected model, probability, prediction and mistake
category. PNG exports preserve the active lens, model, focus and category legend.

These are the original prospective inputs. Neighbor models were motivated by
this sample's plot: their overlays are exploratory reuse, not the fresh follow-up
test. Only saved predictions are joined by case ID; no model is refitted or
solver rerun. `prediction_overlay.json` and `manifest.json` record provenance.
The original points, coordinates, static PNG/PDF and experimental evidence stay
byte-for-byte unchanged.

# The Story (read this before you write code)

The hints in the brief boil down to one bet: **a narrow, well-explained insight
beats a broad, shallow one.** Past winners usually don't win on complex ML —
they win on a clear story told with the data. This document is where the story
lives, and everything in `src/` exists only to serve it.

## The one sentence
> _"Across <REGION>, <VARIABLE> has been <declining/rising> at <SLOPE>/year,
> and the worst area is <HOTSPOT> — here's the data that shows it and how we
> know it's trustworthy."_

If a feature, chart, or model doesn't make that sentence more true or more
believable, cut it. That is the entire scoping rule for 48 hours.

## Presentation arc (matches the dashboard panels)
1. **Headline** — one number a judge remembers (the trend + how much data survived QC).
2. **When** — trend line + seasonality: is it getting better/worse, and when's the peak?
3. **Where** — the map + hotspot ranking: the punchline location.
4. **Honesty** — the QC audit trail. Saying "we dropped 18% cloud-contaminated
   pixels" builds more trust than a prettier chart.

## Scoping decisions (fill in on day one, then freeze)
- [ ] Dataset: _______________  (one — resist adding a second)
- [ ] Question: ______________  (copy into `config.yaml: project.one_question`)
- [ ] Deliverable: the dashboard in `app/dashboard.py` (map + trend + QC)
- [ ] Explicit non-goals: ______________  (write down what you are NOT building)

## Applying the specific hints
- **Partner data (ESA/JAXA/etc.):** before committing, check whether a Space
  Agency Partner product fits the question better than NASA's own. Swapping is
  cheap here — it only touches `src/ingest.py` + `config.yaml`.
- **Practice the pipeline early:** if pre-event sample data drops, wire
  `load_csv`/`load_netcdf` and run `python -m src.pipeline` against a small
  sample *before the clock starts*. The synthetic mode exists so the dashboard
  and tests are already green before you ever see real data.
- **Play to your strengths:** this scaffold leans on Python + data pipelines +
  visualization, not image classification/ML. If the challenge tempts you
  toward unfamiliar ML, prefer the explainable analysis in `src/analyze.py`.


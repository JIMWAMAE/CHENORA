# Chenora: Who Should We Sign First?

A data-led plan to help Chenora reach five paid Kenya contracts by 31 January 2027.

## The company

**Chenora** is a Nairobi startup building an AI account manager. It watches a business's customer accounts every day, acts when one slips or is ready to buy more, and helps the business keep and grow revenue it has already won.

- **Client:** Darren Oyoo, Founder and CEO
- **Price:** $1 per account managed per month, with a $12,000 annual minimum, plus 15% of revenue won back
- **Customers today:** Kijani (B2B logistics) and Triply (B2B travel-tech)
- **Prepared by:** Jimcollins Wamae Wanguku, MSc Data Science and Analytics (DSA 8402 capstone, Option C)

## The problem

Chenora has about 70 days, limited founder time and 100 prospects in its pipeline. It has no sales history, so it cannot tell which type of Kenyan business to approach first.

**Decision to support:** Which one or two Kenyan business segments should get Chenora's sales time first, to reach five paid contracts by 31 January 2027?

## What we did

1. **Agreed the decision** with Darren: one decision, one target, one 70-day window.
2. **Desk research** on Kenyan registers, associations and benchmarks, with each source graded A, B or C.
3. **Synthetic data** (fictional firms and a 100-prospect pipeline) used to test ideas, because Chenora has no real data yet.
4. **Simulation** of the pipeline to test whether five contracts is realistic.
5. **Segment scorecard**, with weights shaken 2,000 ways to check the ranking holds.
6. **A simple tracker app** for Darren to enter real prospects and replace our assumptions.

## Findings

- **Five contracts is possible but depends on the pipeline stage.** If the 100 prospects split 55 / 25 / 12 / 6 / 2 across the five active stages, the chance of five or more paid contracts by 31 January is about **7%** (pessimistic), **66%** (base) and **99%** (optimistic).
- **Late-stage deals matter most.** Five more prospects at "Quote sent" lift the base case from 66% to about 86%.
- **Three segments lead:** B2B software, B2B logistics and payments platforms. They stay in the top three when the weights are shaken. Logistics is the only one with a live customer (Kijani).
- **Kenya contracts are small.** A firm just above the 1,000-account gate is worth about $12,000 to $17,000 in year one, against the $84K average in the investor deck. Five contracts at gate size are worth about $60,000 a year.
- **The $500 monthly price is below the floor.** $500 a month is $6,000 a year, under the $12,000 minimum. Darren needs to confirm if the minimum applies in Kenya.

## Recommendations

1. **Close late-stage deals first.** Only prospects at Quote sent or Negotiation can still sign in time.
2. **Test three segments in parallel:** B2B software, logistics and payments platforms, using named lists from public registers.
3. **Hold the rest** (distributors, manufacturers, insurance brokers) until the first results come in. Review at day 30 and day 60.

## What we do not know yet

- The real stage of the 100 prospects (the biggest lever)
- Whether Kijani already counts as a paid contract
- Whether the $12,000 minimum applies in Kenya
- Real win rates and sales cycle times

**Read the results with care.** The data is synthetic and the stage split is an assumption. The results show what has to be true to reach five contracts. They do not forecast who will buy. Darren's real pipeline should replace the assumptions.

## The tracker app

A small Streamlit app for Darren with three tabs: **Add and edit**, **Pipeline view** and **Can we hit five?**

**App link:** https://chenora-akxww6rwnc36wehldyhjbb.streamlit.app/


## Data and privacy

- All firm-level data is synthetic. No real Chenora records are in this repository.
- Real pipeline data is git-ignored. Never commit it.
- Keep the repository private.
- AI use is described in `AI.md`.

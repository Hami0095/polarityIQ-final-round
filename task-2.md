# Task 2 — SaaS Conversion Analysis

Before I answer the question as asked, I want to flag something about the question itself, because
I think that's where the money gets wasted.

The stated goal is more MRR. The stated method is a better free-to-paid conversion rate. Those
aren't the same thing, and treating them as the same is the first mistake I'd want to avoid.

MRR moves on five things: qualified signups, conversion rate, revenue per account, expansion from
existing customers, and churn. Conversion is one of the five. For a product like this — narrow
market, high price point — it's often not the one that's binding. Say they get 400 free signups a
month. Doubling conversion from 3% to 6% wins twelve customers. At a $6,000 ACV that's real money,
but it takes months, and I'd bet a pricing correction or a churn fix produces more in the same
window with less work.

So my honest answer to "how would you improve this conversion rate" starts with: I'd want to
establish that conversion rate is the right thing to spend a quarter on. Not assume it, because
it's the number that looks bad.

I'd also want to say this out loud early — the right move might make the conversion rate go
*down*. If you replace an open free tier with a qualified demo and a paid pilot, conversion falls
and revenue rises. If the founders are tracking the percentage rather than the dollars, that's a
conversation worth having before anyone builds anything.

## 3% by itself tells you almost nothing

Two problems with the number as stated.

First, "free accounts" and "free trial" are different products, and the question uses both. A
perpetual free tier and a time-boxed trial convert at completely different rates and fail for
completely different reasons. Which one this is changes everything downstream.

Second, once you know which it is, the benchmarks are decisive. First Page Sage's data — 86 SaaS
companies, 2022 through 2025 — puts freemium free-to-paid at roughly 2.6% organic, opt-in trials
around 18%, and credit-card-required trials near 49%.

**If this is a perpetual free tier, 3% is at par.** It's basically the number the model produces.
Nobody optimizes from 2.6% to 15% inside a freemium structure — that gap is a model choice, not an
execution problem, and the founders' real issue would be an expectation benchmarked against the
wrong thing. If it's an opt-in trial sitting at 3% against an 18% benchmark, something is badly
broken and the diagnosis is urgent and completely different.

One caution I'd put in front of them before anyone anchors on a number: the benchmarks disagree
with each other by about 2x. A 2026 ChartMogul study of 200 products puts opt-in trials at 8.9%
and CC-required at 31.4%, against First Page Sage's 18.2% and 48.8%. Same metric, both credible,
very different samples. I'd use these to orient — is 3% normal or broken — and never as a target.

There's a third thing the blended number hides. In a niche B2B data product I'd expect qualified
ICP signups to convert at several multiples of the blended rate and unqualified signups — students,
job seekers, curious retail investors, competitors sizing up the data — to convert near zero. If
that's true, this isn't a conversion problem at all. It's a traffic composition problem being
reported as one.

## What I'd want to know, and what each answer would change

This is what I'd actually send back before proposing anything.

**Denominators.** Monthly free signups, current MRR, ACV, paid customer count. *Determines whether
conversion is even the right lever, and whether experimentation is statistically available at all —
see below.*

**Which model is it.** Perpetual free or time-boxed? Card required? What's gated, what's open?
*Determines whether 3% is normal or alarming.*

**The 3%, segmented** — by acquisition channel, job title, firm type, company size, geography.
*This is the cut I'd want most. It separates a targeting problem from a product problem, and I'd
bet more on this single view than on anything else on the list.*

**Activation.** What share of free accounts ever run a search that returns results, open a full
record, export anything? And what's the conversion rate of users who do versus users who don't?
*Determines whether the failure happens before or after the user experiences value.*

**Churn and expansion on existing paid accounts.** *Determines whether new conversion is worth
optimizing right now at all. Filling a leaky bucket faster is the standard way to waste a quarter.*

**The value metric.** What are customers billed on — seats, records, exports, API calls, a flat
fee? *Determines whether pricing is aligned to the value delivered, which for a data product it
frequently isn't.*

**And fifteen conversations.** What did the last fifteen non-converting ICP users say when someone
asked why? Has anyone asked? What do the customers who *did* convert say they were actually
buying? *This changes more than any dashboard. At this volume, fifteen calls beat three months of
tests, and I'd want them before touching the product.*

## What I'd bet is happening

Priors, not conclusions. I'd expect to be wrong about at least one.

**Traffic composition — high confidence.** The free tier is pulling in a lot of people who were
never going to buy. If so, the fix is qualification at the top of the funnel, not a better
onboarding flow.

**The free tier is giving away the product — high confidence, and structural.** This is the part
generic conversion advice can't see, because it isn't about funnels.

For most SaaS, a free tier gives away *capability*, and the user has to keep coming back to get
value. For a data product, the value *is* the data. A free user who extracts fifty usable records
has already received the whole product and has no reason to pay. Every free tier on a data
business sits on that contradiction, and if the line is drawn wrong the tier isn't a funnel — it's
leakage that also happens to depress a metric.

The fix isn't "give away less." It's give away *proof* and withhold *volume*. Full search, real
result counts, complete records visible for a handful of entities, verification dates and sourcing
visible everywhere — but contact fields masked and exports capped. The user can confirm the data
is real, current, and covers their universe, which is the actual purchase question, without being
able to run their outreach off the free tier.

**The purchase objection is trust, not price — medium-high confidence.** In contact and
intelligence data, buyers hesitate because they've been sold stale, padded, or wrong data before.
Anyone who has bought a list has been burned by one. If the platform doesn't make its verification
method, recency, and coverage limits visible, prospects assume the worst, and no amount of
onboarding polish moves them.

Worth stating directly: **honest visible coverage limits convert better than implied completeness
in this category.** A page showing per-record verification dates, an explicit "we could not verify
this" state, and a truthful coverage summary by segment does more for conversion here than a
testimonial carousel. Confidence only converts when it's falsifiable.

*I'd add that this isn't abstract to me after Task 1.* Building that dataset, the thing that took
the most work was exactly this — verification chains per cell, honest blanks where a value couldn't
be confirmed, a contact-actionability label so a buyer can see at a glance which records they can
act on today, and an explicit "insufficient evidence" state in the interface rather than a silent
omission. I built those as data-quality controls. They're also conversion assets, and the same
work does both jobs. A prospect evaluating a data product is asking "can I trust this," and the
honest answer, shown rather than claimed, is the most persuasive thing you have.

**Value metric misalignment — medium confidence.** If pricing is per seat, it's mispriced. A
two-person coverage team pulling 3,000 records gets far more value than a ten-person team pulling
200. Seat pricing on a data product under-monetizes heavy users and overcharges light ones, which
suppresses conversion at the bottom and leaves expansion revenue uncollected at the top.

## The constraint nobody mentions: they probably can't A/B test this

This changes the whole plan, so I want to be explicit about it.

Detecting a 3% → 4.5% lift at conventional significance takes on the order of a thousand-plus
users per variant. At a few hundred signups a month, one test runs for many months. Running several
at once is worse than useless, because they contaminate each other.

Which means the standard playbook — iterate onboarding, test paywall copy, optimize the email
sequence — **isn't statistically available to them.** Anyone handing these founders a testing
roadmap either hasn't checked the volume or is planning to read noise as signal.

What is available: qualitative research, segment-level analysis where effect sizes are large enough
to see without formal testing, and structural changes big enough that they don't need a test to
detect. That's what I'd plan around.

## What I'd actually do

**Days 1–10 — diagnose. No product changes.** Instrument the funnel, produce the segmentation cut,
run fifteen calls with ICP users who signed up and didn't buy plus five with recent customers about
what they thought they were buying. Establish churn. Costs almost nothing and determines everything
after it.

**Days 10–14 — decide which problem this is.** Three branches. I'd commit to one rather than
hedging across all three.

*Traffic composition* → qualify at the top. Work email and firm name required, ask role and use
case, route unqualified signups to a limited tier and qualified ones to a sales-assisted path.
Conversion rises partly because the denominator gets honest, which is fine as long as everyone
understands that's what happened.

*Activation* → attack time-to-first-value. The strongest version for this product: ask for the
user's mandate or thesis at signup and populate their first session with the twenty most relevant
family offices already matched to it. An empty search box is a bad first experience for someone who
doesn't yet know what to query.

*Willingness to pay* → repackage. Move the value metric to records or exports, draw the free/paid
line at volume rather than capability, add an annual prepay discount, and test price *upward*. In
high-ACV niche data, underpricing reads as low-quality data.

**Regardless of branch, three structural bets:**

Sales-assist the top decile of free accounts. At this ACV a human reaching out to a qualified free
user is trivially economic, and pure self-serve on a considered purchase this size is fighting the
market's natural motion.

Make verification visible in-product, per the trust hypothesis.

Instrument expansion and churn, so next quarter's MRR conversation isn't only about new logos.

## What I wouldn't do

Countdown timers, manufactured scarcity, buried cancel paths, anything that converts someone
against their own interest. In a market this small — a few thousand relevant buyers who mostly know
each other — a reputation for sharp practice costs more than the MRR it wins. That's a commercial
argument as much as an ethical one, though it's both.

I also wouldn't ship a testing roadmap I know can't reach significance. I'd say so instead of
quietly running it and reporting the noise.

## How I'd know it worked, and what would prove me wrong

Success isn't the conversion percentage. It's MRR, with conversion segmented by ICP so the number
means something, plus net revenue retention.

I'd consider myself wrong if: segmentation shows conversion is roughly flat across qualified and
unqualified traffic (kills the composition hypothesis); non-converting ICP users name price rather
than trust as the main objection (weakens the trust hypothesis); or activation is already high
among qualified users who simply choose not to buy (points at competition or willingness-to-pay
rather than anything in the funnel).

The largest gap in this answer is that I have no data. Everything above is a prior with a test
attached. I'd rather hand that over honestly than a confident plan built on numbers nobody has
looked at yet.
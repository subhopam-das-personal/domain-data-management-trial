# Demo Script
Talking points for a 5-10 minute live walkthrough. Adapt to the room.

---

## Opening (30 seconds, before touching the app)

"Clinical trial enrollment delays cost about $500,000 a day in late-phase oncology. Most of that delay is patient screening — a site coordinator requesting records from multiple providers, faxing, waiting, then manually checking eligibility criteria against a protocol PDF. That takes 2-3 weeks per patient. Dropout risk isn't assessed until someone actually drops out.

PPD has data assets no other CRO has: the Clario endpoint database from 10,000+ trials, and the Datavant real-world data network linking 80,000 care sites. I built a prototype that puts those together. Let me show you what that looks like."

---

## Screen 1 — The Setup (60 seconds)

*[Point to trial criteria on the left]*

"This is the actual eligibility criteria from NCT04736745, a Phase III pembrolizumab trial. The critical exclusion: QTc interval greater than 470ms. Cardiac safety is the reason most patients fail screening in oncology immunotherapy trials.

*[Point to patient selector on the right]*

"We have three patients. Let's start with Maria Santos — Stage III esophageal adenocarcinoma, good functional status, prior chemotherapy completed."

*[Select Patient A]*

---

## Screen 2 — The Wow Moment (2-3 minutes)

*[Click "Analyze with PPD Intelligence Layer"]*

*[While it streams]* "This is running against the Clario and Datavant signal libraries in real time."

*[After output appears, point to QTc line]* "QTc 418ms — below the 470ms threshold. Eligible. Low retention risk. This took 90 seconds.

Now let's look at a harder case."

*[Switch to Patient B — James Okafor]*

*[Click Analyze again]*

*[After output streams, point to the highlighted yellow line]*

"That sentence. 'Cardiac endpoint signal from Clario trial database — not available to generic AI tools.' That's the whole demo. ChatGPT can check eligibility criteria. Any AI can do that. But only PPD can say that a patient with this cardiac profile has a 2.3x elevated dropout rate because we've seen it in 10,000 actual trials. That's what Clario gives us."

---

## Screen 3 — The Differentiator Lands (60 seconds)

*[Scroll down to site matching]*

"Memorial Cancer Center in Houston scores 94 — the treating oncologist is on record via Datavant linkage across four care sites. Without Datavant, that connection is invisible to the site coordinator. It shows up as a blank in the chart.

Chicago scores 45 — geographic mismatch, limited cardiac trial experience. You wouldn't place this patient there.

This matching took 90 seconds. Manual chart review: 3 weeks."

---

## Closing (30 seconds)

**If job interview:**
"I built this in 2 hours. Here's what I'd build in 2 weeks with your data and your infrastructure: a production-connected version with real Datavant tokenization on PPD's actual trial referrals, validated against Clario's dropout outcome data. The prototype is the seed of that product."

**If internal pitch:**
"Here's what this becomes with the Datavant partnership we just signed and Clario's endpoint data already in house: an active screening intelligence layer embedded in eTMF at the point of referral — not a batch report three weeks later. The infrastructure cost is marginal. The competitive differentiation is not."

---

## Hard Q&A

**Q: The data is synthetic. How do we know this works on real patients?**

"The protocol criteria are real — NCT04736745. The FHIR schema is FHIR R4 standard, the same format Datavant delivers. What makes this real is connecting it to actual Clario endpoint outcomes for the retention risk signal. That's the first engineering sprint after proof of concept."

**Q: How is this different from what IQVIA offers?**

"IQVIA has 1.2 billion records and a strong site network. They don't have Clario's cardiac endpoint depth from 10,000 actual trials. That's the specific signal that predicts QTc-related dropout — and that's the reason pembrolizumab combination trials specifically lose patients. Volume doesn't substitute for that signal."

**Q: What would production actually require?**

"Three things: Datavant tokenization integration for real patient data linkage (their API, a few weeks), a trained retention risk model validated against Clario's outcome data (that's the 6-month project), and eTMF embed for delivery at the referral point rather than as a standalone tool. The demo is proof the reasoning layer works. The data plumbing is solvable."

**Q: Is this compliant for real patient data?**

"The demo uses synthetic data — no real patients, no PHI. A production version would run on Datavant's tokenized linkage, which is specifically designed for privacy-protected cross-site matching. That's one of the reasons the Datavant partnership matters."

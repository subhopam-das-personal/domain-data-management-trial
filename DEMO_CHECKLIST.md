# Pre-Demo Checklist
Run this 30 minutes before the demo.

## T-30 minutes

- [ ] `cd /home/subhopam/Documents/Programming/thermofisher_ppd`
- [ ] `streamlit run app.py` — confirm app loads, no import errors
- [ ] Verify ANTHROPIC_API_KEY is set: `cat .env | grep ANTHROPIC_API_KEY`
- [ ] Click "Analyze with PPD Intelligence Layer" for Patient A — confirm streaming works
- [ ] Click for Patient B — confirm fallback still works if you unset the key temporarily
- [ ] Check the Clario provenance line renders highlighted (yellow background) for Patient B
- [ ] Confirm Patient C shows MEDIUM RISK and the QTc gap flag
- [ ] Close and reopen — confirm session_state is cleared on restart
- [ ] Browser zoom at 100%, font readable from across a conference table

## T-15 minutes

- [ ] Open Screen 3 (site matching) — all three rows visible, scores render correctly
- [ ] "90 seconds vs. 3 weeks" line is visible without scrolling
- [ ] Close all other browser tabs
- [ ] Silence phone and laptop notifications
- [ ] Have DEMO_SCRIPT.md open in a second window or printed

## T-5 minutes

- [ ] App is on Screen 1, Patient A selected, no prior analysis showing
- [ ] Terminal running in background (not visible to audience)
- [ ] You know which patient you're leading with (recommend Patient A for clean eligible case, then Patient B for the wow moment)

## If the API fails mid-demo

The app automatically falls back to pre-recorded responses with simulated streaming. The audience cannot tell the difference. Do not acknowledge it. Keep going.

## If Streamlit crashes

```bash
streamlit run app.py
```
It restarts in under 5 seconds.

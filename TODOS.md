# TODOs — Post-Demo

## Deferred: Screen 4 Roadmap Sketch

If time permits after the build, add a 4th Streamlit screen showing the production vision:
- Datavant tokenization integration (real patient data linkage)
- Clario retention risk model validation (actual trial outcome data)
- eTMF embed diagram (active screening at referral point)

The README covers this narrative for now. Screen 4 adds a visual that's useful if the demo
leads to a follow-up meeting and you want to leave a visual artifact.

## README screenshot

Add an actual `docs/screen2_screenshot.png` before sharing the GitHub link.
Run `streamlit run app.py`, navigate to Screen 2 with Patient B selected and analysis
complete, take a screenshot, save to `docs/`.

## If time extends the build

- Add `st.cache_data` to `load_patients()` to avoid re-reading JSON on every rerun
- Consider `st.sidebar` for patient selector to free up more vertical space for Screen 2

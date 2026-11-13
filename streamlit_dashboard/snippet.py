# --- paste this inside:  if _sel == 5:  (Session Performance), right after the st.subheader line ---
    st.markdown("### 📷 Live AI Trainer (laptop webcam or phone camera)")
    st.caption("Press Start camera, allow the camera, and do bicep curls. The trainer counts your reps, "
               "checks your elbow and speaks to you. Press Finish and analyze to get your score.")
    live = pose_trainer(key="live_trainer")
    if live and live.get("finished") and st.session_state.get("last_live_id") != live["id"]:
        st.session_state["last_live_id"] = live["id"]
        _reps = int(live["reps"]); _dur = max(1, int(live["duration"]))
        _good = int(live["good"]); _total = max(1, int(live["total"]))
        _fb = ["Good rep!"] * _good + ["Adjust form"] * max(0, _total - _good)
        _res = requests.post(f"{API_URL}/api/analyze-session",
                             json={"reps": _reps, "duration_seconds": _dur, "form_feedback_list": _fb})
        st.session_state["last_live_result"] = (_reps, _dur, _res.json() if _res.status_code == 200 else None, _res.text)
    if st.session_state.get("last_live_result"):
        _reps, _dur, _data, _txt = st.session_state["last_live_result"]
        if _data:
            st.success(f"Last live session: {_reps} reps in {_dur} s")
            _c1, _c2, _c3 = st.columns(3)
            _c1.metric("Performance Score", _data["performance_score"])
            _c2.metric("Form Quality", f"{_data['form_quality_pct']}%")
            _c3.metric("Rating", _data["rating"])
        else:
            st.error(f"Error: {_txt}")
    st.markdown("---")
    st.markdown("**Or enter a session manually**")

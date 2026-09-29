import streamlit as st
from dataclasses import dataclass, field
from datetime import datetime

st.set_page_config(page_title="MasteryFlow", page_icon="🧠", layout="wide")

CONCEPTS = {
    "Fractions": [],
    "Ratios": ["Fractions"],
    "Percentages": ["Fractions"],
    "Linear Equations": ["Ratios", "Percentages"],
    "Graphs": ["Linear Equations"],
    "Quadratic Equations": ["Linear Equations"],
    "Probability": ["Fractions", "Percentages"],
    "Statistics": ["Percentages", "Probability"],
}

QUESTIONS = {
    "Fractions": ("Which is larger: 3/4 or 2/3?", "3/4"),
    "Ratios": ("A recipe uses 2 cups flour for 3 cups water. What is the ratio flour:water?", "2:3"),
    "Percentages": ("What is 20% of 150?", "30"),
    "Linear Equations": ("Solve: 2x + 6 = 14. What is x?", "4"),
    "Graphs": ("In y = 2x + 3, what is the slope?", "2"),
    "Quadratic Equations": ("What is the degree of x² + 3x + 1?", "2"),
    "Probability": ("A fair coin is tossed once. Probability of heads?", "1/2"),
    "Statistics": ("What is the mean of 2, 4 and 6?", "4"),
}

def init():
    if "learners" not in st.session_state:
        st.session_state.learners = {
            "Aarav": {"mastery": {c: 0.0 for c in CONCEPTS}, "attempts": [], "overrides": []},
            "Diya": {"mastery": {c: 0.0 for c in CONCEPTS}, "attempts": [], "overrides": []},
        }
        # Different histories make the adaptive paths visibly diverge.
        for c,v in {"Fractions":.92,"Ratios":.82,"Percentages":.76,"Linear Equations":.68}.items():
            st.session_state.learners["Aarav"]["mastery"][c]=v
        for c,v in {"Fractions":.45,"Ratios":.38,"Percentages":.30,"Linear Equations":.22}.items():
            st.session_state.learners["Diya"]["mastery"][c]=v

def decide(learner, concept):
    m=learner["mastery"][concept]
    prereqs=CONCEPTS[concept]
    weak=[p for p in prereqs if learner["mastery"][p] < .55]
    recent=[a for a in learner["attempts"] if a["concept"]==concept][-3:]
    hints=sum(a["hint"] for a in recent)
    if weak:
        return "Remediate Prerequisite", f"Prerequisite {weak[0]} is at {learner['mastery'][weak[0]]*100:.0f}% mastery."
    if m < .45:
        return "Practice", f"Mastery is {m*100:.0f}%; more guided practice is needed."
    if m < .70 or hints >= 2:
        return "Review", f"Mastery is {m*100:.0f}% and recent support usage is {hints} hint(s)."
    if m < .85:
        return "Challenge", f"Mastery is {m*100:.0f}%; a harder transfer task can test deeper understanding."
    return "Advance", f"Mastery is {m*100:.0f}% with prerequisites sufficiently strong."

def update_mastery(old, correct, confidence, difficulty, hint, response_time):
    # Explainable heuristic: correctness is primary; confidence, difficulty, hints and speed adjust evidence.
    score = (1 if correct else 0) * .65 + (confidence/5)*.15 + difficulty*.10 + (0 if hint else .10)
    if response_time > 90: score -= .05
    score=max(0,min(1,score))
    return round(.75*old + .25*score, 3)

init()
st.title("🧠 MasteryFlow")
st.caption("Explainable Adaptive Learning & Intervention Engine")

with st.sidebar:
    st.header("Student")
    learner_name=st.selectbox("Select learner", list(st.session_state.learners))
    learner=st.session_state.learners[learner_name]
    st.divider()
    st.write("**Adaptive actions:** Advance · Practice · Review · Remediate · Challenge")
    st.write("Every recommendation is backed by learner evidence.")

tab1,tab2,tab3=st.tabs(["🎯 Student Path","📊 Teacher Dashboard","🧪 Simulation"])

with tab1:
    c1,c2=st.columns([1.4,1])
    with c1:
        st.subheader("Cold-start / practice")
        concept=st.selectbox("Concept", list(CONCEPTS))
        st.info(QUESTIONS[concept][0])
        answer=st.text_input("Your answer")
        confidence=st.slider("Confidence",1,5,3)
        difficulty=st.slider("Question difficulty",0.0,1.0,0.5)
        hint=st.checkbox("Used a hint")
        response_time=st.number_input("Response time (seconds)", min_value=1, value=35)
        if st.button("Submit attempt", type="primary"):
            correct=answer.strip().lower()==QUESTIONS[concept][1].lower()
            old=learner["mastery"][concept]
            new=update_mastery(old,correct,confidence,difficulty,hint,response_time)
            learner["mastery"][concept]=new
            learner["attempts"].append({"concept":concept,"correct":correct,"confidence":confidence,
                                        "difficulty":difficulty,"hint":int(hint),"response_time":response_time,
                                        "time":datetime.now().isoformat()})
            action,reason=decide(learner,concept)
            st.success("Correct" if correct else f"Recorded as incorrect. Expected answer: {QUESTIONS[concept][1]}")
            st.metric("Updated mastery", f"{new*100:.0f}%")
            st.write("### Next action")
            st.warning(f"**{action}** — {reason}")
    with c2:
        st.subheader("Why this next?")
        for c in CONCEPTS:
            action,reason=decide(learner,c)
            st.write(f"**{c}** · {learner['mastery'][c]*100:.0f}%")
            st.progress(learner["mastery"][c])
            st.caption(f"{action}: {reason}")

with tab2:
    st.subheader("Teacher view")
    rows=[]
    for name,data in st.session_state.learners.items():
        for c,m in data["mastery"].items():
            action,reason=decide(data,c)
            rows.append({"Learner":name,"Concept":c,"Mastery":f"{m*100:.0f}%","Next action":action,"Reason":reason})
    st.dataframe(rows,use_container_width=True)
    st.markdown("### Teacher override")
    target=st.selectbox("Learner", list(st.session_state.learners), key="override_learner")
    target_concept=st.selectbox("Concept", list(CONCEPTS), key="override_concept")
    override=st.selectbox("Override action", ["Advance","Practice","Review","Remediate Prerequisite","Challenge","Teacher Intervention"])
    if st.button("Save override"):
        st.session_state.learners[target]["overrides"].append({
            "concept":target_concept,"action":override,"time":datetime.now().isoformat()
        })
        st.success("Override logged and persisted for this session.")
    for name,data in st.session_state.learners.items():
        if data["overrides"]:
            st.write(f"**{name} override history:**")
            st.json(data["overrides"])

with tab3:
    st.subheader("Two learners, same curriculum, different paths")
    for name in ["Aarav","Diya"]:
        data=st.session_state.learners[name]
        st.write(f"### {name}")
        cols=st.columns(4)
        for i,c in enumerate(list(CONCEPTS)[:4]):
            with cols[i]:
                st.metric(c, f"{data['mastery'][c]*100:.0f}%")
                action,reason=decide(data,c)
                st.caption(action)
    st.success("The engine uses learner history, prerequisites and evidence signals rather than a fixed sequence.")

st.divider()
st.caption("Prototype note: mastery uses an explainable weighted heuristic. Replace with Bayesian Knowledge Tracing / IRT if time permits.")

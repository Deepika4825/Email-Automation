import sys, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
from pipeline import run
from modules.db_store import (
    get_all, get, update_status, count,
    filter_by, to_context_string, init_db,
)
from modules.llm_engine import answer_query

init_db()

st.set_page_config(page_title="SmartMail AI", page_icon="✉️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.main{background:#f0f2f6;}
.block-container{padding:1.2rem 1.8rem;}
.card{background:white;border-radius:14px;padding:18px 22px;
      margin-bottom:12px;box-shadow:0 1px 6px rgba(0,0,0,0.07);}
.badge{display:inline-block;padding:3px 11px;border-radius:20px;
       font-size:12px;font-weight:600;color:white;margin-right:4px;}
.label{font-size:11px;font-weight:700;color:#999;
       text-transform:uppercase;letter-spacing:.8px;margin-bottom:3px;}
div[data-testid="stButton"]>button{
    border-radius:9px;font-weight:600;
    color:#fff !important;background:#2980b9 !important;
    border:none !important;min-height:40px;}
div[data-testid="stButton"]>button:hover{background:#1a6fa0 !important;}
</style>
""", unsafe_allow_html=True)

PC = {"high":"#e74c3c","medium":"#f39c12","low":"#27ae60"}
PI = {"high":"🔴","medium":"🟡","low":"🟢"}
CC = {"HR":"#8e44ad","spam":"#95a5a6","complaint":"#c0392b","inquiry":"#2980b9","sales":"#16a085"}
SC = {"POSITIVE":"#27ae60","NEGATIVE":"#e74c3c","NEUTRAL":"#7f8c8d"}
AC = {"reply":"#2980b9","escalate":"#e74c3c","ignore":"#95a5a6"}
AL = {"reply":"💬 Reply","escalate":"🚨 Escalate","ignore":"🔕 Ignore"}
STATUSES = ["Open","In Progress","Resolved"]

SAMPLES = {
    "HR — Leave Request": (
        "Subject: Annual Leave Request\nFrom: michael@company.com\n\n"
        "Hi Sarah, I would like to request annual leave from July 10 to July 20. "
        "I have completed all pending tasks and briefed John Smith at Acme Corp. "
        "Kindly confirm at your earliest convenience.\n\nBest regards, Michael"
    ),
    "Complaint — Urgent": (
        "Subject: Unacceptable Service - Order #45231\nFrom: jane.doe@gmail.com\n\n"
        "I am extremely disappointed. My order placed on June 1st has still not arrived. "
        "I paid $250 for express delivery. This is urgent — please escalate immediately "
        "and issue a refund.\n\nAngry customer, Jane Doe"
    ),
    "Sales Inquiry": (
        "Subject: Enterprise Pricing Inquiry\nFrom: david.chen@techventures.com\n\n"
        "Hello, I am reaching out on behalf of TechVentures Inc. We are interested in your "
        "enterprise package. Could you send a quote for 500 licenses? Budget is $50,000. "
        "Please follow up with our procurement team.\n\nDavid Chen, VP Sales"
    ),
    "Spam": (
        "Subject: You've Won a Prize!\nFrom: noreply@promo.xyz\n\n"
        "Congratulations! You have been selected as our lucky winner. "
        "Click here to claim your free offer worth $1000. Unsubscribe anytime."
    ),
}

for k, v in [("view","inbox"),("selected",None),("ai_answer","")]:
    if k not in st.session_state:
        st.session_state[k] = v

def go(view):
    st.session_state.view = view

def sel(eid):
    st.session_state.selected = eid
    st.session_state.view = "inbox"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ✉️ SmartMail AI")
    st.markdown("---")
    st.button("📥 Inbox",        use_container_width=True, on_click=go, args=("inbox",))
    st.button("➕ Add Email",    use_container_width=True, on_click=go, args=("add",))
    st.button("🤖 AI Assistant", use_container_width=True, on_click=go, args=("assistant",))
    st.button("📊 Analytics",   use_container_width=True, on_click=go, args=("analytics",))
    st.markdown("---")
    st.metric("Total Emails", count())
    all_e = get_all()
    if all_e:
        highs = sum(1 for e in all_e if e.get("priority",{}).get("priority") == "high")
        st.metric("🔴 High Priority", highs)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## ✉️ SmartMail AI")
st.caption("Offline AI email assistant — paste emails, get instant intelligence.")
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# VIEW: ADD EMAIL
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.view == "add":
    st.markdown("### ➕ Add New Email")
    s1, s2 = st.columns([3, 1])
    with s2:
        pick = st.selectbox("Sample", ["— paste your own —"] + list(SAMPLES.keys()),
                            label_visibility="collapsed")
    default = SAMPLES.get(pick, "")
    with s1:
        st.caption("Paste email text (include Subject: and From: for best results)")

    uploaded = st.file_uploader("Or upload a .txt file", type=["txt"])
    if uploaded:
        default = uploaded.read().decode("utf-8", errors="ignore")

    email_txt = st.text_area("Email", value=default, height=220,
                              label_visibility="collapsed",
                              placeholder="Subject: ...\nFrom: ...\n\nEmail body...")
    a1, a2 = st.columns(2)
    with a1:
        analyze = st.button("🔍 Analyze & Add to Inbox", type="primary", use_container_width=True)
    with a2:
        st.button("✕ Cancel", use_container_width=True, on_click=go, args=("inbox",))

    if analyze:
        if email_txt.strip():
            with st.spinner("Running AI pipeline…"):
                result = run(email_txt)
            st.session_state.selected = result["id"]
            st.session_state.view = "inbox"
            st.rerun()
        else:
            st.warning("Please paste or upload an email.")

# ══════════════════════════════════════════════════════════════════════════════
# VIEW: AI ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.view == "assistant":
    st.markdown("### 🤖 AI Email Assistant")
    st.caption("Ask questions about your inbox")

    suggestions = ["Show urgent emails","Summarize all complaints",
                   "Which emails need action?","Find emails needing escalation"]
    s1, s2 = st.columns([3, 1])
    with s2:
        sugg = st.selectbox("Suggestion", ["— type your own —"] + suggestions,
                            label_visibility="collapsed")
    with s1:
        query = st.text_input("Question",
                              value="" if sugg == "— type your own —" else sugg,
                              placeholder="e.g. Show urgent emails",
                              label_visibility="collapsed")

    ask = st.button("Ask AI", type="primary")
    if ask and query.strip():
        if count() == 0:
            st.warning("Your inbox is empty. Add some emails first.")
        else:
            with st.spinner("Thinking…"):
                st.session_state.ai_answer = answer_query(query, to_context_string())

    if st.session_state.ai_answer:
        st.markdown(
            f"<div class='card'><div class='label'>AI Response</div>"
            f"{st.session_state.ai_answer}</div>",
            unsafe_allow_html=True)

    st.button("← Back to Inbox", on_click=go, args=("inbox",))

# ══════════════════════════════════════════════════════════════════════════════
# VIEW: ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.view == "analytics":
    st.markdown("### 📊 Inbox Analytics")
    inbox = get_all()
    if not inbox:
        st.info("No emails yet. Add some emails to see analytics.")
    else:
        cats  = [e["category"] for e in inbox]
        pris  = [e["priority"]["priority"] for e in inbox]
        acts  = [e["priority"]["action"] for e in inbox]
        stats = [e["status"] for e in inbox]

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total",      len(inbox))
        m2.metric("🔴 High",    pris.count("high"))
        m3.metric("🟡 Medium",  pris.count("medium"))
        m4.metric("🟢 Low",     pris.count("low"))
        m5.metric("✅ Resolved", stats.count("Resolved"))

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**By Category**")
            st.bar_chart(pd.Series(cats).value_counts()
                         .rename_axis("Category").reset_index(name="Count").set_index("Category"))
        with c2:
            st.markdown("**By Priority**")
            st.bar_chart(pd.Series(pris).value_counts()
                         .rename_axis("Priority").reset_index(name="Count").set_index("Priority"))
        with c3:
            st.markdown("**Suggested Actions**")
            st.bar_chart(pd.Series(acts).value_counts()
                         .rename_axis("Action").reset_index(name="Count").set_index("Action"))

    st.button("← Back to Inbox", on_click=go, args=("inbox",))

# ══════════════════════════════════════════════════════════════════════════════
# VIEW: INBOX
# ══════════════════════════════════════════════════════════════════════════════
else:
    inbox = get_all()

    if not inbox:
        c1, c2, c3, c4 = st.columns(4)
        for col, icon, title, desc in [
            (c1, "📋", "Paste Email",   "Paste any email text"),
            (c2, "🧠", "AI Analysis",   "Classify, summarize & score"),
            (c3, "💬", "Smart Replies", "Auto-generated replies"),
            (c4, "🗄️", "RAG Memory",   "Find similar past emails"),
        ]:
            with col:
                st.markdown(
                    f"<div class='card' style='text-align:center'>"
                    f"<div style='font-size:2rem'>{icon}</div>"
                    f"<div style='font-weight:700;margin:6px 0'>{title}</div>"
                    f"<div style='font-size:13px;color:#888'>{desc}</div>"
                    f"</div>", unsafe_allow_html=True)
        st.info("👆 Click **➕ Add Email** in the sidebar to get started.")

    else:
        left, right = st.columns([1, 2], gap="large")

        with left:
            fc1, fc2 = st.columns(2)
            with fc1:
                f_cat = st.selectbox("Cat", ["All","HR","spam","complaint","inquiry","sales"],
                                     label_visibility="collapsed")
            with fc2:
                f_pri = st.selectbox("Pri", ["All","high","medium","low"],
                                     label_visibility="collapsed")

            filtered = filter_by(
                category=None if f_cat == "All" else f_cat,
                priority=None if f_pri == "All" else f_pri,
            )
            st.markdown(f"**{len(filtered)} email{'s' if len(filtered)!=1 else ''}**")

            for e in filtered:
                pri  = e["priority"]["priority"]
                subj = (e.get("subject") or "(no subject)")[:38]
                sndr = (e.get("sender") or "")[:32]
                stat = e.get("status","Open")
                s_ic = "✅" if stat=="Resolved" else ("🔄" if stat=="In Progress" else "📬")
                is_sel = st.session_state.selected == e["id"]
                st.button(
                    f"{PI[pri]} {s_ic} {subj}",
                    key=f"em_{e['id']}",
                    use_container_width=True,
                    type="primary" if is_sel else "secondary",
                    on_click=sel, args=(e["id"],),
                )
                st.caption(sndr)

        with right:
            e = get(st.session_state.selected) if st.session_state.selected else None
            if e is None and inbox:
                e = inbox[0]
                st.session_state.selected = e["id"]

            if e:
                pri  = e["priority"]["priority"]
                cat  = e["category"]
                sent = e["priority"]["sentiment"]
                act  = e["priority"]["action"]

                tc1, tc2 = st.columns([3, 1])
                with tc1:
                    st.markdown(f"### {e.get('subject') or '(no subject)'}")
                    if e.get("sender"):
                        st.caption(f"From: {e['sender']}   ·   Added: {e.get('added_at','')}")
                with tc2:
                    cur = e.get("status","Open")
                    new_s = st.selectbox("Status", STATUSES,
                                         index=STATUSES.index(cur),
                                         key=f"stat_{e['id']}")
                    if new_s != cur:
                        update_status(e["id"], new_s)
                        st.rerun()

                sent_ic = "😊" if sent=="POSITIVE" else ("😟" if sent=="NEGATIVE" else "😐")
                cat_bg  = CC.get(cat,"#555")
                sent_bg = SC.get(sent,"#888")
                act_bg  = AC.get(act,"#555")
                act_lbl = AL.get(act, act)
                st.markdown(
                    f"<span class='badge' style='background:{PC[pri]}'>{PI[pri]} {pri.upper()}</span>"
                    f"<span class='badge' style='background:{cat_bg}'>{cat.upper()}</span>"
                    f"<span class='badge' style='background:{sent_bg}'>{sent_ic} {sent}</span>"
                    f"<span class='badge' style='background:{act_bg}'>{act_lbl}</span>",
                    unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

                all_ids = [x["id"] for x in inbox]
                cur_pos = all_ids.index(e["id"]) if e["id"] in all_ids else 0
                nav1, nav2, _ = st.columns([1, 1, 4])
                with nav1:
                    if st.button("◀ Prev", disabled=cur_pos <= 0):
                        st.session_state.selected = all_ids[cur_pos - 1]
                        st.rerun()
                with nav2:
                    if st.button("Next ▶", disabled=cur_pos >= len(all_ids) - 1):
                        st.session_state.selected = all_ids[cur_pos + 1]
                        st.rerun()

                st.markdown("---")
                tab1, tab2, tab3, tab4 = st.tabs(["📝 Summary","🔍 Entities","💬 Reply","🗄️ Similar"])

                with tab1:
                    st.markdown(
                        f"<div class='card'><div class='label'>AI Summary</div>"
                        f"<div style='font-size:15px;color:#222;line-height:1.6'>{e['summary']}</div>"
                        f"</div>", unsafe_allow_html=True)
                    kws = e["priority"].get("matched_keywords",[])
                    if kws:
                        st.caption("⚠️ Urgency: " + " · ".join(kws))
                    if e["priority"].get("sender_vip"):
                        st.caption("⭐ VIP sender")
                    tone = e.get("tone",{})
                    if tone.get("dominant_tone"):
                        st.caption(f"🎭 Tone: {tone['dominant_tone'].upper()}")
                    scores = e.get("cat_scores",{})
                    if scores:
                        df = pd.DataFrame({
                            "Category": list(scores.keys()),
                            "Score": [round(v,3) for v in scores.values()]
                        }).sort_values("Score", ascending=False)
                        st.markdown("<div class='label'>Classification Confidence</div>",
                                    unsafe_allow_html=True)
                        st.bar_chart(df.set_index("Category"), height=160)

                with tab2:
                    ents = e.get("entities",{})
                    def fmt(lst): return ", ".join(lst) if lst else "—"
                    action_html = (
                        "<div style='margin-top:10px;font-size:14px'>✅ <b>Action items:</b> "
                        + " · ".join(ents.get("action_items",[])) + "</div>"
                        if ents.get("action_items") else ""
                    )
                    st.markdown(
                        f"<div class='card'>"
                        f"<table style='width:100%;font-size:14px;color:#333;border-collapse:collapse'>"
                        f"<tr><td style='padding:5px 0;width:50%'>👤 <b>People</b>: {fmt(ents.get('names',[]))}</td>"
                        f"<td style='padding:5px 0'>📅 <b>Dates</b>: {fmt(ents.get('dates',[]))}</td></tr>"
                        f"<tr><td style='padding:5px 0'>🏢 <b>Orgs</b>: {fmt(ents.get('organizations',[]))}</td>"
                        f"<td style='padding:5px 0'>💰 <b>Amounts</b>: {fmt(ents.get('amounts',[]))}</td></tr>"
                        f"</table>{action_html}</div>",
                        unsafe_allow_html=True)

                with tab3:
                    reply_edit = st.text_area("Edit reply", value=e.get("reply",""),
                                              height=150, label_visibility="collapsed",
                                              key=f"rep_{e['id']}")
                    if st.button("📋 Copy", key=f"cp_{e['id']}"):
                        st.code(reply_edit, language=None)

                with tab4:
                    similar = e.get("similar",[])
                    if similar:
                        for j, s in enumerate(similar, 1):
                            with st.expander(
                                f"#{j} {s.get('subject','—')} · "
                                f"{s.get('category','')} · similarity {s.get('similarity','')}"
                            ):
                                st.write(f"**Priority:** {s.get('priority','—')}")
                                st.write(f"**Action:** {s.get('action','—')}")
                                st.write(f"**Summary:** {s.get('summary','—')}")
                    else:
                        st.info("No similar emails yet. Add more emails to build RAG memory.")

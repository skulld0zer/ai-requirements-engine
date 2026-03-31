import streamlit as st
import json
import re
import uuid
from llm import generate_requirements
from linear import create_issue, get_existing_issues, find_duplicates

st.set_page_config(layout="wide")

# STATE
if "structured" not in st.session_state:
    st.session_state["structured"] = None

if "is_generating" not in st.session_state:
    st.session_state["is_generating"] = False

if "released" not in st.session_state:
    st.session_state["released"] = False


st.title("AI Requirements Engine")

user_input = st.text_area("Enter requirements:")


# STYLE (only custom button styling, no theme override!)
st.markdown("""
<style>

/* Primary button */
div[data-testid="stButton"] button[kind="primary"] {
    background-color: #d32f2f !important;
    color: white !important;
    border-radius: 6px !important;
}

/* Optional subtle input rounding */
textarea, input {
    border-radius: 6px !important;
}

</style>
""", unsafe_allow_html=True)


# BUTTONS
col1, col2 = st.columns(2)

with col1:
    generate_clicked = st.button("Generate", disabled=st.session_state["is_generating"])

with col2:
    release_clicked = st.button(
        "Release on Linear",
        disabled=(
            st.session_state["structured"] is None or
            st.session_state["is_generating"] or
            st.session_state["released"]
        )
    )


# GENERATE
if generate_clicked:
    st.session_state["is_generating"] = True

    with st.spinner("Generating requirements via LLM..."):
        raw = generate_requirements(user_input)

    match = re.search(r"\{.*\}", raw, re.DOTALL)

    if not match:
        st.error("Invalid output from LLM")
        st.stop()

    flat = json.loads(match.group(0))
    existing = get_existing_issues()

    structured = []

    reqs = flat.get("requirements", [])[:3]
    us_list = flat.get("user_stories", [])[:6]
    tc_list = flat.get("test_cases", [])[:6]

    for i, r in enumerate(reqs):

        r["uid"] = str(uuid.uuid4())
        r["duplicates"] = find_duplicates(r["title"], existing)
        r["decision"] = "create"

        block = {
            "requirement": r,
            "user_stories": [],
            "test_cases": []
        }

        for j in range(2):
            idx = i * 2 + j
            if idx < len(us_list):
                us = us_list[idx].copy()
                us["uid"] = str(uuid.uuid4())
                us["duplicates"] = find_duplicates(us["title"], existing)
                us["decision"] = "keep"

                block["user_stories"].append({"user_story": us})

        for k in range(2):
            idx = i * 2 + k
            if idx < len(tc_list):
                tc = tc_list[idx].copy()
                tc["uid"] = str(uuid.uuid4())
                tc["duplicates"] = find_duplicates(tc["title"], existing)
                tc["decision"] = "create"

                block["test_cases"].append(tc)

        structured.append(block)

    st.session_state["structured"] = structured
    st.session_state["is_generating"] = False
    st.session_state["released"] = False

    st.rerun()


# RELEASE
if release_clicked:
    st.session_state["released"] = True

    with st.spinner("Releasing your items to Linear..."):

        for block in st.session_state["structured"]:
            r = block["requirement"]

            if r["decision"] == "discard":
                continue

            if r["decision"] == "merge" and r["duplicates"]:
                req_id = r["duplicates"][0]["id"]
            else:
                req_id = create_issue(
                    f"REQ: {r['title']}",
                    r["description"],
                    r["priority"],
                    "requirement"
                )

            if not req_id:
                st.error("Failed to create requirement")
                st.stop()

            for tc in block["test_cases"]:
                if tc["decision"] in ["skip", "merge"]:
                    continue

                steps_text = "\n".join(tc["steps"]) if isinstance(tc["steps"], list) else tc["steps"]

                desc = f"""Precondition:
{tc['precondition']}

Steps:
{steps_text}

Expected:
{tc.get('expected', '')}
"""

                create_issue(
                    f"TC: {tc['title']}",
                    desc,
                    tc["priority"],
                    "test_case",
                    parent_id=req_id
                )

            for us_block in block["user_stories"]:
                us = us_block["user_story"]

                if us["decision"] in ["discard", "merge"]:
                    continue

                create_issue(
                    f"US: {us['title']}",
                    us["description"],
                    us["priority"],
                    "user_story",
                    parent_id=req_id
                )

    st.success("Items successfully released to Linear")


# UI
if st.session_state["structured"]:
    structured = st.session_state["structured"]

    st.markdown(f"""
### Summary
- Requirements: {len(structured)}
- User Stories: {sum(len(b["user_stories"]) for b in structured)}
- Test Cases: {sum(len(b["test_cases"]) for b in structured)}
""")

    for i, block in enumerate(structured):

        r = block["requirement"]

        st.markdown("---")

        col1, col2 = st.columns([10,1])

        with col1:
            r["title"] = st.text_input("Requirement Title", r["title"], key=f"req_t_{i}_{r['uid']}")
            r["description"] = st.text_area("Description", r["description"], key=f"req_d_{i}_{r['uid']}")

        with col2:
            if st.button("Delete", key=f"del_req_{i}_{r['uid']}", type="primary"):
                structured.pop(i)
                st.rerun()

        duplicates = r.get("duplicates", [])

        if duplicates:
            with st.expander("Duplicates detected"):
                for d in duplicates:
                    ref = d.get("identifier") or d.get("id")
                    score = d.get("score", 1.0)
                    url = f"https://linear.app/issue/{ref}"

                    st.markdown(
                        f"""
                        <div style="display:flex; justify-content:space-between;">
                            <span><b>{d['type'].upper()} ({score})</b> — {d['title']}</span>
                            <a href="{url}" target="_blank">View ↗</a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            if any(d["type"] == "identical" for d in duplicates):
                r["decision"] = st.radio("Action", ["merge", "discard", "create"], key=f"req_dec_{i}_{r['uid']}")
            else:
                r["decision"] = st.radio("Action", ["create", "merge", "discard"], key=f"req_dec_{i}_{r['uid']}")

        for j, us_block in enumerate(block["user_stories"]):
            us = us_block["user_story"]

            st.markdown("#### User Story")

            col1, col2 = st.columns([10,1])

            with col1:
                us["title"] = st.text_input("Title", us["title"], key=f"us_t_{i}_{j}_{us['uid']}")
                us["description"] = st.text_area("Description", us["description"], key=f"us_d_{i}_{j}_{us['uid']}")

            with col2:
                if st.button("Delete", key=f"del_us_{i}_{j}_{us['uid']}", type="primary"):
                    block["user_stories"].pop(j)
                    st.rerun()

        for k, tc in enumerate(block["test_cases"]):

            st.markdown("#### Test Case")

            col1, col2 = st.columns([10,1])

            with col1:
                tc["title"] = st.text_input("Title", tc["title"], key=f"tc_t_{i}_{k}_{tc['uid']}")
                tc["precondition"] = st.text_input("Precondition", tc["precondition"], key=f"tc_p_{i}_{k}_{tc['uid']}")

                steps = "\n".join(tc["steps"]) if isinstance(tc["steps"], list) else tc["steps"]
                updated = st.text_area("Steps", steps, key=f"tc_s_{i}_{k}_{tc['uid']}")
                tc["steps"] = updated.split("\n")

            with col2:
                if st.button("Delete", key=f"del_tc_{i}_{k}_{tc['uid']}", type="primary"):
                    block["test_cases"].pop(k)
                    st.rerun()

    st.session_state["structured"] = structured
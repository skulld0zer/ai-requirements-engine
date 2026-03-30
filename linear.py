import os
import requests
import re
from dotenv import load_dotenv
from difflib import SequenceMatcher
import streamlit as st
import os

def get_env(key):
    return st.secrets.get(key) or os.getenv(key)

load_dotenv()

API_KEY = get_env("API_KEY")
LINEAR_API_KEY = get_env("LINEAR_API_KEY")
URL = "https://api.linear.app/graphql"
TEAM_ID = "195c1904-01e4-44ce-9c74-1bc5825c1770"


# ------------------------
# PRIORITY MAPPING
# ------------------------
def map_priority(priority):
    if not priority:
        return 2

    p = priority.strip().lower()

    if p == "high":
        return 3
    elif p == "medium":
        return 2
    elif p == "low":
        return 1
    else:
        return 2


# ------------------------
# TEXT HELPERS (🔥 FIX)
# ------------------------
def clean_title(text):
    text = text.lower().strip()

    # remove prefixes like "REQ:", "US:", "TC:"
    text = re.sub(r"^(req|us|tc)\s*:\s*", "", text)

    # remove special chars (optional but strong)
    text = re.sub(r"[^a-z0-9 ]", "", text)

    # normalize spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize(text):
    return clean_title(text)


def similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


# ------------------------
# GET EXISTING ISSUES
# ------------------------
def get_existing_issues():
    query = """
    {
      issues(first: 100) {
        nodes {
          id
          identifier
          title
        }
      }
    }
    """

    res = requests.post(
        URL,
        json={"query": query},
        headers={"Authorization": API_KEY}
    )

    data = res.json()

    if "errors" in data:
        print("Linear Error:", data["errors"])
        return []

    return data["data"]["issues"]["nodes"]


# ------------------------
# DUPLICATE DETECTION (🔥 FIXED)
# ------------------------
def find_duplicates(new_title, existing):
    results = []

    new_norm = normalize(new_title)

    for issue in existing:
        title = issue.get("title", "")
        title_norm = normalize(title)

        # 🔴 IDENTICAL (now really correct)
        if new_norm == title_norm:
            results.append({
                "type": "identical",
                "id": issue.get("id"),
                "identifier": issue.get("identifier"),
                "title": title
            })
            continue

        # 🟡 SIMILAR
        score = similarity(new_norm, title_norm)

        if score > 0.75:
            results.append({
                "type": "similar",
                "id": issue.get("id"),
                "identifier": issue.get("identifier"),
                "title": title,
                "score": round(score, 2)
            })

    return results


# ------------------------
# GET PROJECT + LABELS
# ------------------------
def get_linear_meta():
    query = """
    {
      projects {
        nodes {
          id
          name
        }
      }
      issueLabels {
        nodes {
          id
          name
        }
      }
    }
    """

    res = requests.post(
        URL,
        json={"query": query},
        headers={"Authorization": API_KEY}
    )

    data = res.json()

    if "errors" in data:
        print("Meta Fetch Error:", data["errors"])
        return None, {}

    project_id = None
    labels = {}

    for p in data["data"]["projects"]["nodes"]:
        if "requirements-engine-showcase01" in p["name"].lower():
            project_id = p["id"]

    for l in data["data"]["issueLabels"]["nodes"]:
        name = l["name"].lower()

        if "requirement" in name:
            labels["requirement"] = l["id"]
        elif "user story" in name:
            labels["user_story"] = l["id"]
        elif "test case" in name:
            labels["test_case"] = l["id"]

    return project_id, labels


PROJECT_ID, LABELS = get_linear_meta()


# ------------------------
# CREATE ISSUE
# ------------------------
def create_issue(title, description, priority, label_key, parent_id=None):
    query = """
    mutation ($title: String!, $description: String!, $teamId: String!, $parentId: String, $priority: Int, $labelIds: [String!], $projectId: String) {
      issueCreate(input: {
        teamId: $teamId,
        title: $title,
        description: $description,
        parentId: $parentId,
        priority: $priority,
        labelIds: $labelIds,
        projectId: $projectId
      }) {
        issue { id }
      }
    }
    """

    variables = {
        "title": title,
        "description": description,
        "teamId": TEAM_ID,
        "parentId": parent_id,
        "priority": map_priority(priority),
        "labelIds": [LABELS.get(label_key)] if LABELS.get(label_key) else [],
        "projectId": PROJECT_ID
    }

    res = requests.post(
        URL,
        json={"query": query, "variables": variables},
        headers={"Authorization": API_KEY}
    )

    data = res.json()

    if "errors" in data:
        print("Create Issue Error:", data["errors"])
        return None

    return data["data"]["issueCreate"]["issue"]["id"]
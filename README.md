# AI Requirements Engine

AI-powered tool that transforms raw requirements into structured requirements, user stories, and test cases, with integrated duplicate detection and seamless Linear issue creation.

---

## Overview

This project automates the process of requirements engineering by converting unstructured input into standardized artifacts. It also detects existing items in Linear to prevent duplication and supports decision-based workflows (merge, create, discard).

---

## Features

- Generate structured requirements from raw input
- Automatic creation of:
  - Requirements
  - User Stories
  - Test Cases
- Duplicate detection using semantic similarity
- Merge vs. create decision logic
- Integration with Linear via GraphQL API
- Hierarchical issue creation

---

## Use Case

The tool is designed to support product managers, developers, and QA engineers by reducing manual effort and improving consistency in requirement definition and tracking.

---

## Tech Stack

- Python
- Streamlit (UI layer)
- LLM integration
- Linear GraphQL API

---

## Setup

Clone the repository:

```bash
git clone https://github.com/skulld0zer/ai-requirements-engine.git
cd ai-requirements-engine

Install dependencies:
pip install -r requirements.txt

Create a .env file:
API_KEY= *LLM API*
LINEAR_API_KEY= *LINEAR API*
LINEAR_TEAM_KEY= *TEAM KEY*

Run the application:
streamlit run app.py
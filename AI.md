# AI Use Disclosure & Project Rules

This file records how AI was used to build the Chenora pipeline tracker and outlines the ground rules for any AI assistant working on this repository.

## 1. How AI Was Used

I used **Claude Opus 5.5** as a development and data generation assistant while building this project:

* **What it helped with:** Structuring and writing the Streamlit application (`app.py`), drafting documentation, and generating the synthetic sample dataset (`data/sample_pipeline.csv`) calibrated to our research parameters.
* **What was kept strictly offline:** Real client and prospect records. No confidential business data or actual contact details were shared with any AI tool.
* **Human review and ownership:** I personally reviewed, tested, and verified all code, pricing logic, and outputs before use. All business assumptions—including stage splits, win rates, signing timelines, and target segment decisions—remain completely human-owned.

### Limitations to Keep in Mind
* **Synthetic data only:** The sample dataset is fictional and designed solely to demonstrate how the tracker functions, not to represent actual market behavior.
* **Assumption-driven outputs:** The *"Can we hit five?"* projections are decision-support estimates based strictly on the assumptions entered into the model.

---

## 2. Ground Rules for AI Assistants

**Project Context:** A lightweight Streamlit sales pipeline tracker built for Chenora, used by Darren and the research team.

### Keep the Setup Simple
* Keep all application logic inside a single file (`app.py`). Do not split the app into multiple modules or add unnecessary boilerplate like Docker or external test suites unless explicitly requested.
* Preserve the three core tabs: **Add and edit**, **Pipeline view**, and **Can we hit five?**.

### Protect Data and Credentials
* **Never commit `pipeline.csv`** or any real prospect names, phone numbers, or contact details to this repository.
* **Never hard-code passwords.** Always read `APP_PASSWORD` from environment variables or Streamlit secrets.

### Maintain Analytical Honesty
* Label every assumption clearly inside both the app interface and `README.md`.
* Present simulation results as scenario estimates, never as guaranteed forecasts.
* Whenever a code update affects the underlying calculations, explicitly state which figures changed and why.

### Style and Pre-Commit Checklist
* Use clear, direct, jargon-free English across UI labels, help text, and commit messages.
* Before concluding any change:
  1. Run the app locally (`streamlit run app.py`).
  2. Load the sample data, add a test prospect, verify duplicate-code handling, and inspect all three tabs.
  3. Update `README.md` if setup steps or data fields changed.


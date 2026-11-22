# Chenora pipeline tracker

One small web app. Darren logs prospects, the app checks the ICP gates (1,000+ accounts, digital records,
decision-maker access), values each prospect at the new pricing, and shows whether **five paid Kenya contracts by
31 January 2027** is realistic.

Files: `app.py` (the whole app), `requirements.txt`, `sample_pipeline.csv` (100 fictional prospects), this README.
Your data saves to `pipeline.csv` next to the app. That file is git-ignored, so it is never uploaded to GitHub.

## Run it on a Mac
```bash
cd chenora-tracker
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Open the address it prints (http://localhost:8501). Click **Load sample data** to look around, then **Clear everything** and add real prospects.
To lock it with a password: `APP_PASSWORD="choose-one" python -m streamlit run app.py`

## Put it online for Darren (free)
1. Create a **private** GitHub repository and upload these files.
2. Go to share.streamlit.io, sign in with GitHub, click **Create app**, pick the repository, set the main file to `app.py`.
3. In **Advanced settings > Secrets** add: `APP_PASSWORD = "choose-one"`
4. Deploy. You get a link.

**Free hosting forgets saved data when the app restarts.** Use **Download pipeline CSV** (sidebar) after each session and
**Upload** it next time. If Darren will use this daily, run it on a company laptop or server instead (option above) so `pipeline.csv` stays on disk.

## Rules
- Use prospect **codes** (KE-014), never people's names or contact details.
- Keep the repository private.
- Win rates and signing times at the top of `app.py` are **assumptions**. Edit them when real outcomes arrive.

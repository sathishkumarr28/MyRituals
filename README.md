# ✨ MyRitual

A personalised **habit tracker + 5-minute journal + micro-learning** web app.
Users sign in, tell the app which habits they want to build, what they want to
journal about, and what topics they're curious about. The app then uses an LLM
(Azure OpenAI `gpt-5.4-mini-1`) to build a per-user *skill profile* and generate
a fresh, non-repetitive deck of ~22 swipeable cards every day:

- **Habit check-ins** — yes/no & 1–5 scale, tied to the user's real habits
- **Journaling** — mood (smiley) pickers and quick free-text prompts
- **Micro-learning** — fact cards with surprising snippets about the user's interests

Everything is stored per-user in **Azure Cosmos DB**.

---

## 🧱 Architecture

```
habit_journal_app/
├── app.py                 # Streamlit entry point + routing
├── requirements.txt
├── .streamlit/
│   ├── config.toml        # dark theme
│   └── secrets.toml.example  # Google/Apple OAuth config template
└── src/
    ├── config.py          # env + credentials (reads workspace .env)
    ├── db.py              # Cosmos DB data layer (+ in-memory fallback)
    ├── llm.py             # skill profile + dynamic card generation
    ├── auth.py            # Google/Apple (OIDC) + demo email login
    ├── interests.py       # predefined interest / habit / journal catalogues
    ├── onboarding.py      # first-run wizard (habits → journal → interests)
    ├── questions.py       # swipeable daily card deck
    ├── home.py            # dashboard (streak, stats, history)
    └── styles.py          # custom CSS
```

**Data model (Cosmos DB, database `myritual`)**

| Container   | Partition key | Contents |
|-------------|---------------|----------|
| `users`     | `/id`         | profile, habits, journalFocus, interests, LLM `skill` |
| `responses` | `/userId`     | one document per completed daily session |

Credentials are read from the **workspace `.env`** (one folder up) — the same
`OPENAI_*` and `COSMOS_*` values already in this repo. No secrets are hard-coded.

---

## ▶️ Run locally

```powershell
cd habit_journal_app
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501. Without OAuth configured it uses a **demo email
sign-in**; without Cosmos/OpenAI reachable it falls back to an in-memory store
and hand-written cards, so it always runs.

---

## 🔐 Enabling Google / Apple sign-in

Streamlit has native OpenID Connect auth. Copy the template and fill it in:

```powershell
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
```

- **Google:** create an OAuth client in Google Cloud Console → add
  `https://<your-app>/oauth2callback` as an authorized redirect URI → paste the
  client id/secret.
- **Apple:** create a Services ID in the Apple Developer portal, enable
  *Sign in with Apple*, and generate the client-secret JWT (Apple requires a
  short-lived signed JWT rather than a static secret).

Once `[auth]` exists in `secrets.toml`, the login screen automatically shows the
**Continue with Google / Apple** buttons instead of the demo form.

---

## ☁️ Deploy to Azure Web App

1. Push this folder to your repo.
2. Create an Azure Web App (Linux, Python 3.11+).
3. **Startup command:**
   ```bash
   python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0
   ```
4. Set application settings for `OPENAI_API_KEY`, `OPENAI_BASE_URL`,
   `CHAT_DEPLOYMENT`, `COSMOS_ENDPOINT`, `COSMOS_KEY` (instead of the `.env`).
5. Add `secrets.toml` (with the production `redirect_uri`) via the Web App's
   mounted storage or the `STREAMLIT` secrets mechanism, and register the
   production redirect URI with Google/Apple.

---

## 🎛️ Configuration knobs

| Env var                | Default            | Purpose |
|------------------------|--------------------|---------|
| `CHAT_DEPLOYMENT`      | `gpt-5.4-mini-1`   | Azure OpenAI chat deployment |
| `COSMOS_DATABASE`      | `myritual`         | Cosmos database name |
| `DAILY_QUESTION_COUNT` | `22`               | Cards generated per day |

---

*Built with Streamlit, LangChain + Azure OpenAI, and Azure Cosmos DB.*

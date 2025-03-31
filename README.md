# League Match Analyzer 🎮📊

This is a lightweight Flask web app that analyzes recent **League of Legends** matches using the **Riot Games API**.  
It provides performance insights like Kill Participation, Ability Uses, Scuttle Crabs, First Tower timings, and more.

---

## 🚀 Features

- 🔍 Analyze recent matches for any summoner (via Riot ID)
- 📈 Stats include:
  - Minions @10
  - Kill Participation %
  - First Tower time
  - Assists
  - Crabs
  - Abilities used
  - Total Damage to Champions
- 💾 Match data cached in SQLite for speed
- 🌐 Simple web UI with sortable, searchable DataTables

---

## 🔧 Setup

### 1. Clone the repo

```bash
git clone https://github.com/iksyomaz/lol-match-analyzer.git
cd lol-match-analyzer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your Riot API key

Create a `.env` file:

```env
RIOT_API_KEY="PASTE_YOUR_API_KEY_HERE"
```

---

## ▶️ Run the App

```bash
python flask_app.py
```

Then open: [http://localhost:5000](http://localhost:5000)

---

## 📂 File Structure

```plaintext
.
├── flask_app.py               # Web interface with Flask
├── main.py                    # CLI match analyzer
├── config.py                  # API setup & constants
├── custom_summoners.json      # Stored summoners
├── templates/
│   └── index.html             # Web UI template
├── .env                       # Riot API key (excluded in public)
├── .gitignore
├── requirements.txt
```

---

## 🛡️ Notes

- For personal use, clone or fork privately and store API keys safely.

---

## 📦 Coming soon

- Visual charts (damage over time, map heatmaps).
- Export to CSV.
- Hosting on Render.com

---

## 🧙‍♂️ Made with ❤️ by [iksyomaz](https://github.com/iksyomaz)
```

---

## 📦 `requirements.txt`

```txt
flask
requests
python-dotenv
pandas
gunicorn
```

✅ Works for both local dev and Render hosting.

---
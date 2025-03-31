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
```

### 2. Navigate to the project directory

```bash
cd lol-match-analyzer
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Riot API key

You can inject your Riot API key into the `.env` file directly from the terminal. Replace `PASTE_YOUR_API_KEY_HERE` with your actual API key:

```bash
echo 'RIOT_API_KEY="PASTE_YOUR_API_KEY_HERE"' > .env
```

Alternatively, you can manually open the `.env` file and edit it to include your API key:

```env
RIOT_API_KEY="PASTE_YOUR_API_KEY_HERE"
```

---

## ▶️ Run the App

```bash
python app.py
```

Then open:
```bash
http://localhost:5000
```

---

## 📂 File Structure

```plaintext
.
├── app.py                    # Flask app entry point
├── cli.py                    # CLI tool for analyzing matches
├── config.py                 # API setup & constants
├── summoners.json            # Stored summoners
├── templates/
│   └── index.html            # Web UI template
├── .env                      # Riot API key (excluded in public)
├── .gitignore
├── requirements.txt
├── README.md
```

---

## 🛡️ Notes

- For personal use, clone or fork privately and store API keys safely!

---

## 📦 Coming soon

- Visual charts (damage over time, map heatmaps).
- Hosting on Render.com
# Faktura → Excel

AI aplikace pro extrakci položek z PDF faktur do Excelu.

## Deploy na Railway (doporučeno, free tier)

### 1. Vytvoř GitHub repozitář
- Jdi na github.com/new
- Název: faktura-excel
- Klikni Create repository

### 2. Nahraj soubory přes web GitHub
Na stránce nového repozitáře klikni "uploading an existing file" a nahraj všechny soubory.
POZOR: templates/index.html musí být ve složce templates/ !

Nebo přes git příkazový řádek:
  git init
  git add .
  git commit -m "init"
  git branch -M main
  git remote add origin https://github.com/TVOJE_JMENO/faktura-excel.git
  git push -u origin main

### 3. Deploy na Railway
1. Jdi na railway.app → Login with GitHub
2. New Project → Deploy from GitHub repo
3. Vyber repozitář faktura-excel
4. Railway automaticky nasadí aplikaci

### 4. Nastav API klíč
1. V Railway: klikni na službu → Variables → New Variable
2. Název: ANTHROPIC_API_KEY
3. Hodnota: sk-ant-api03-... (z console.anthropic.com)
4. Aplikace se automaticky restartuje

### 5. Otevři aplikaci
Settings → Domains → Generate Domain
URL bude např.: faktura-excel-production.up.railway.app

## Lokální spuštění
  pip install -r requirements.txt
  export ANTHROPIC_API_KEY=sk-ant-...
  python app.py
  → http://localhost:5000

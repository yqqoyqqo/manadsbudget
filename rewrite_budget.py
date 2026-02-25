import re

html_content = """<!DOCTYPE html>
<html lang="sv">

<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover"/>
  <title>Månadsbudget</title>

  <!-- PWA -->
  <link rel="manifest" href="manifest.json" />
  <meta name="theme-color" content="#1e293b" />

  <!-- iOS PWA -->
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <meta name="apple-mobile-web-app-title" content="Budget" />
  <link rel="apple-touch-icon" href="icon-192.png" />

  <!-- Firebase Compat Libraries -->
  <script src="https://www.gstatic.com/firebasejs/10.9.0/firebase-app-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/10.9.0/firebase-auth-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/10.9.0/firebase-firestore-compat.js"></script>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #f5f6fa;
      --card: #ffffff;
      --border: #e2e6ea;
      --text: #1a1d23;
      --muted: #6b7280;
      --income-color: #16a34a;
      --income-light: #f0fdf4;
      --income-border: #bbf7d0;
      --fixed-color: #dc2626;
      --fixed-light: #fef2f2;
      --fixed-border: #fecaca;
      --variable-color: #d97706;
      --variable-light: #fffbeb;
      --variable-border: #fde68a;
      --saving-color: #7c3aed;
      --saving-light: #f5f3ff;
      --saving-border: #ddd6fe;
      --radius: 10px;
      --shadow: 0 1px 4px rgba(0,0,0,0.07);
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 24px 16px 48px;
    }
    header {
      text-align: center;
      margin-bottom: 28px;
      position: relative;
    }
    header h1 {
      font-size: 1.7rem;
      font-weight: 700;
      letter-spacing: -0.5px;
      color: #15803d;
    }
    header p.sub {
      color: var(--muted);
      font-size: 0.88rem;
      margin-top: 4px;
    }

    /* Auth & Share UI */
    .top-bar {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }
    .btn-sm {
      background: #fff;
      border: 1.5px solid var(--border);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text);
      cursor: pointer;
      transition: background 0.15s;
    }
    .btn-sm:hover { background: #f1f5f9; }
    .btn-sm.primary {
      background: #0369a1;
      color: #fff;
      border: none;
    }
    .btn-sm.primary:hover { background: #075985; }
    .user-info {
      font-size: 0.85rem;
      font-weight: 500;
      display: flex;
      align-items: center;
      color: var(--muted);
      margin-right: auto;
    }

    .app-grid {
      max-width: 900px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
    .card {
      background: var(--card);
      border: 1.5px solid var(--border);
      border-radius: var(--radius);
      padding: 18px;
      box-shadow: var(--shadow);
    }
    .card.full { grid-column: 1 / -1; }
    .card-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 14px;
    }
    .card-header .dot {
      width: 11px; height: 11px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .card-header h2 {
      font-size: 0.95rem;
      font-weight: 600;
    }
    .income .card-header .dot { background: var(--income-color); }
    .income { border-color: var(--income-border); background: var(--income-light); }
    .income .total-row { color: var(--income-color); }
    .income .add-btn { background: var(--income-color); }
    .fixed .card-header .dot { background: var(--fixed-color); }
    .fixed { border-color: var(--fixed-border); background: var(--fixed-light); }
    .fixed .total-row { color: var(--fixed-color); }
    .fixed .add-btn { background: var(--fixed-color); }
    .variable .card-header .dot { background: var(--variable-color); }
    .variable { border-color: var(--variable-border); background: var(--variable-light); }
    .variable .total-row { color: var(--variable-color); }
    .variable .add-btn { background: var(--variable-color); }
    .saving { border-color: var(--saving-border); background: var(--saving-light); }
    .saving .card-header .dot { background: var(--saving-color); }
    .saving .total-row { color: var(--saving-color); }
    .saving .add-btn { background: var(--saving-color); }
    .row-list { display: flex; flex-direction: column; gap: 7px; }
    .entry-row {
      display: grid;
      gap: 6px;
      align-items: center;
    }
    .entry-row.normal { grid-template-columns: 1fr 110px 30px; }
    .entry-row.saving-row { grid-template-columns: 1fr 90px 90px 30px; }
    input[type="text"], input[type="number"], select {
      width: 100%;
      border: 1.5px solid var(--border);
      border-radius: 6px;
      padding: 6px 9px;
      font-size: 0.85rem;
      background: #fff;
      color: var(--text);
      outline: none;
      transition: border-color 0.15s;
    }
    input[type="text"]:focus,
    input[type="number"]:focus,
    select:focus { border-color: #94a3b8; }
    input[type="number"] { text-align: right; }
    .del-btn {
      width: 26px; height: 26px;
      border: none;
      border-radius: 5px;
      background: rgba(0,0,0,0.06);
      color: var(--muted);
      font-size: 1rem;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      transition: background 0.15s, color 0.15s;
      flex-shrink: 0;
    }
    .del-btn:hover { background: #fecaca; color: var(--fixed-color); }
    .add-btn {
      margin-top: 10px;
      border: none;
      color: #fff;
      font-size: 0.82rem;
      font-weight: 600;
      padding: 6px 14px;
      border-radius: 6px;
      cursor: pointer;
      opacity: 0.9;
      transition: opacity 0.15s;
    }
    .add-btn:hover { opacity: 1; }
    .total-row {
      display: flex;
      justify-content: space-between;
      font-weight: 700;
      font-size: 0.92rem;
      padding-top: 10px;
      margin-top: 8px;
      border-top: 1.5px solid rgba(0,0,0,0.08);
    }
    .result-card {
      text-align: center;
      padding: 28px 20px;
    }
    .result-label {
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--muted);
      margin-bottom: 6px;
    }
    .result-amount {
      font-size: 3.2rem;
      font-weight: 800;
      letter-spacing: -2px;
      line-height: 1;
    }
    .result-amount.positive { color: var(--income-color); }
    .result-amount.negative { color: var(--fixed-color); }
    .result-breakdown {
      display: flex;
      justify-content: center;
      gap: 24px;
      margin-top: 14px;
      flex-wrap: wrap;
    }
    .breakdown-item {
      font-size: 0.8rem;
      color: var(--muted);
    }
    .breakdown-item span {
      display: block;
      font-weight: 600;
      color: var(--text);
      font-size: 0.88rem;
    }
    .saving-warning {
      margin-top: 10px;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 0.82rem;
      font-weight: 600;
      display: none;
    }
    .saving-warning.over { background: #fef2f2; color: var(--fixed-color); border: 1px solid var(--fixed-border); display: block; }
    .saving-unallocated {
      margin-top: 10px;
      font-size: 0.82rem;
      color: var(--muted);
    }
    .saving-unallocated strong { color: var(--saving-color); }
    .saving-calc {
      font-size: 0.75rem;
      color: var(--muted);
      text-align: right;
      padding: 0 2px;
    }
    .export-area {
      grid-column: 1 / -1;
      display: flex;
      justify-content: center;
      gap: 12px;
      padding: 4px 0 16px;
      flex-wrap: wrap;
    }
    .export-btn {
      background: #1e293b;
      color: #fff;
      border: none;
      padding: 10px 28px;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s;
    }
    .export-btn:hover { background: #0f172a; }
    .newmonth-btn {
      background: #0369a1;
      color: #fff;
      border: none;
      padding: 10px 24px;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s;
    }
    .newmonth-btn:hover { background: #075985; }

    /* Modals */
    .modal-overlay {
      position: fixed; inset: 0;
      background: rgba(0,0,0,0.4);
      display: flex; align-items: center; justify-content: center;
      z-index: 100;
      display: none;
    }
    .modal-overlay.open { display: flex; }
    .modal-box {
      background: #fff;
      border-radius: 12px;
      padding: 28px 32px;
      max-width: 400px;
      width: 90%;
      box-shadow: 0 8px 32px rgba(0,0,0,0.18);
    }
    .modal-box.center { text-align: center; }
    .modal-box h3 { font-size: 1.2rem; font-weight: 700; margin-bottom: 14px; }
    .modal-box p  { font-size: 0.9rem; color: #6b7280; margin-bottom: 22px; line-height: 1.5; }
    .modal-actions { display: flex; gap: 10px; justify-content: center; margin-top:20px;}
    .modal-cancel {
      padding: 9px 22px; border: 1.5px solid #e2e6ea;
      border-radius: 7px; background: #fff; cursor: pointer;
      font-size: 0.88rem; font-weight: 600; color: #374151;
      transition: background 0.15s;
    }
    .modal-cancel:hover { background: #f3f4f6; }
    .modal-confirm {
      padding: 9px 22px; border: none;
      border-radius: 7px; background: #0369a1; color: #fff;
      cursor: pointer; font-size: 0.88rem; font-weight: 600;
      transition: background 0.15s;
    }
    .modal-confirm:hover { background: #075985; }

    .form-group { margin-bottom: 14px; text-align: left; }
    .form-group label { display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 4px; }
    .form-group input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; }
    
    .google-btn {
      width: 100%;
      background: #fff;
      border: 1px solid #ccc;
      padding: 10px;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center; gap: 10px;
      margin-top: 10px;
    }
    .google-btn:hover { background: #f9f9f9; }

    #toast {
      position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%) translateY(20px);
      background: #1e293b; color: #fff; padding: 10px 22px; border-radius: 8px;
      font-size: 0.85rem; font-weight: 500; opacity: 0; pointer-events: none;
      transition: opacity 0.25s, transform 0.25s; z-index: 999;
    }
    #toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

    /* Hidden export canvas template */
    #export-template { position: fixed; left: -9999px; top: 0; width: 680px; background: #ffffff; padding: 40px 48px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1a1d23; }
    #export-template h1 { font-size: 1.4rem; font-weight: 700; margin-bottom: 4px; }
    #export-template .exp-date { font-size: 0.82rem; color: #6b7280; margin-bottom: 30px; }
    #export-template .exp-section { margin-bottom: 22px; }
    #export-template .exp-section h2 { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 1px; color: #6b7280; margin-bottom: 10px; }
    #export-template .exp-row { display: flex; justify-content: space-between; font-size: 0.9rem; padding: 5px 0; border-bottom: 1px solid #f1f5f9; }
    #export-template .exp-total { display: flex; justify-content: space-between; font-weight: 700; font-size: 0.95rem; padding-top: 8px; margin-top: 4px; border-top: 2px solid #e2e6ea; }
    #export-template .exp-result { border-top: 2px solid #e2e6ea; margin-top: 20px; padding-top: 20px; text-align: center; }
    #export-template .exp-result-label { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 1px; color: #6b7280; margin-bottom: 6px; }
    #export-template .exp-result-amount { font-size: 2.6rem; font-weight: 800; letter-spacing: -1.5px; }
    #export-template .exp-result-amount.positive { color: #16a34a; }
    #export-template .exp-result-amount.negative { color: #dc2626; }
    #export-template .exp-saving-section { margin-top: 22px; }
    #export-template .exp-saving-section h2 { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 1px; color: #6b7280; margin-bottom: 10px; }

    @media (max-width: 640px) {
      .app-grid { grid-template-columns: 1fr; }
      .card.full { grid-column: 1; }
      .export-area { grid-column: 1; }
    }
  </style>
</head>
<body>

<div style="max-width: 900px; margin: 0 auto;">
  <div class="top-bar">
    <div class="user-info" id="user-info">
      <!-- Fylls i av JS -->
    </div>
    <button class="btn-sm" id="btn-login" onclick="openAuthModal()">Logga in</button>
    <button class="btn-sm primary" id="btn-share" onclick="openShareModal()" style="display:none;">Dela budget</button>
    <button class="btn-sm" id="btn-logout" onclick="logout()" style="display:none;">Logga ut</button>
  </div>
</div>

<header>
  <h1>📊 Månadsbudget</h1>
  <p class="sub" id="header-date"></p>
  <p class="sub" id="header-sync" style="color:#0369a1; font-weight:600; display:none;">☁️ Sparas i molnet</p>
</header>

<div class="app-grid">

  <!-- INCOME -->
  <div class="card income" id="income-card">
    <div class="card-header">
      <div class="dot"></div>
      <h2>🟢 Inkomster</h2>
    </div>
    <div class="row-list" id="income-list"></div>
    <button class="add-btn" onclick="addRow('income')">+ Lägg till inkomst</button>
    <div class="total-row">
      <span>Total inkomst</span>
      <span id="income-total">0 kr</span>
    </div>
  </div>

  <!-- FIXED EXPENSES -->
  <div class="card fixed" id="fixed-card">
    <div class="card-header">
      <div class="dot"></div>
      <h2>🔴 Fasta utgifter</h2>
    </div>
    <div class="row-list" id="fixed-list"></div>
    <button class="add-btn" onclick="addRow('fixed')">+ Lägg till fast utgift</button>
    <div class="total-row">
      <span>Total fasta</span>
      <span id="fixed-total">0 kr</span>
    </div>
  </div>

  <!-- VARIABLE EXPENSES -->
  <div class="card variable" id="variable-card">
    <div class="card-header">
      <div class="dot"></div>
      <h2>🟠 Rörliga utgifter</h2>
    </div>
    <div class="row-list" id="variable-list"></div>
    <button class="add-btn" onclick="addRow('variable')">+ Lägg till rörlig utgift</button>
    <div class="total-row">
      <span>Total rörliga</span>
      <span id="variable-total">0 kr</span>
    </div>
  </div>

  <!-- RESULT -->
  <div class="card result-card full">
    <div class="result-label">🟣 Kvar att fördela</div>
    <div class="result-amount" id="result-amount">0 kr</div>
    <div class="result-breakdown">
      <div class="breakdown-item">Inkomst<span id="bd-income">0 kr</span></div>
      <div class="breakdown-item">− Fasta<span id="bd-fixed">0 kr</span></div>
      <div class="breakdown-item">− Rörliga<span id="bd-variable">0 kr</span></div>
    </div>
  </div>

  <!-- SAVINGS -->
  <div class="card saving full" id="saving-card">
    <div class="card-header">
      <div class="dot"></div>
      <h2>🔵 Sparande</h2>
    </div>
    <div class="row-list" id="saving-list"></div>
    <button class="add-btn" onclick="addSavingRow()">+ Lägg till sparmål</button>
    <div class="total-row">
      <span>Totalt sparande</span>
      <span id="saving-total">0 kr</span>
    </div>
    <div class="saving-unallocated" id="saving-unallocated"></div>
    <div class="saving-warning" id="saving-warning">⚠️ Du överskrider tillgängligt belopp!</div>
  </div>

  <!-- EXPORT / NEW MONTH -->
  <div class="export-area full">
    <button class="newmonth-btn" onclick="openNewMonthModal()">📅 Ny månad</button>
    <button class="export-btn" onclick="exportImage()">📸 Spara som bild</button>
  </div>

</div>

<!-- Toast -->
<div id="toast"></div>

<!-- New month confirmation modal -->
<div class="modal-overlay" id="newmonth-modal">
  <div class="modal-box center">
    <h3>📅 Starta ny månad?</h3>
    <p>Inkomster, rörliga utgifter och sparande nollställs.<br>
    <strong>Fasta utgifter behålls.</strong></p>
    <div class="modal-actions">
      <button class="modal-cancel" onclick="closeNewMonthModal()">Avbryt</button>
      <button class="modal-confirm" onclick="confirmNewMonth()">Starta ny månad</button>
    </div>
  </div>
</div>

<!-- Auth Modal -->
<div class="modal-overlay" id="auth-modal">
  <div class="modal-box">
    <h3>Logga in / Skapa konto</h3>
    <p>Logga in för att spara din budget i molnet och dela med andra i realtid.</p>
    
    <div class="form-group">
      <label>E-post</label>
      <input type="email" id="auth-email" placeholder="namn@exempel.se">
    </div>
    <div class="form-group">
      <label>Lösenord</label>
      <input type="password" id="auth-password" placeholder="Minst 6 tecken">
    </div>
    <div class="modal-actions" style="margin-top:10px;">
      <button class="modal-cancel" onclick="closeAuthModal()">Avbryt</button>
      <button class="modal-confirm" onclick="handleEmailAuth('login')">Logga in</button>
      <button class="modal-confirm" style="background:#4b5563" onclick="handleEmailAuth('register')">Skapa konto</button>
    </div>
    
    <hr style="margin:20px 0; border:0; border-top:1px solid #e2e6ea;">
    <button class="google-btn" onclick="handleGoogleAuth()">
      <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
      Fortsätt med Google
    </button>
  </div>
</div>

<!-- Share Modal -->
<div class="modal-overlay" id="share-modal">
  <div class="modal-box">
    <h3>Dela Budget</h3>
    <p>Andra kan gå med i denna budget genom att skriva in din budgetkod nedan.</p>
    
    <div class="form-group">
      <label>Din Budgetkod (Ge denna till andra)</label>
      <input type="text" id="share-my-id" readonly style="background:#f1f5f9; font-family:monospace; font-weight:bold; letter-spacing:1px; cursor:copy;" onclick="this.select(); document.execCommand('copy'); showToast('Budgets-ID kopierat!');">
    </div>
    
    <hr style="margin:20px 0; border:0; border-top:1px solid #e2e6ea;">
    
    <div class="form-group">
      <label>Gå med i någon annans budget</label>
      <input type="text" id="share-join-id" placeholder="Klistra in kod här...">
    </div>
    <div class="modal-actions">
      <button class="modal-cancel" onclick="closeShareModal()">Stäng</button>
      <button class="modal-confirm" onclick="joinBudget()">Gå med</button>
    </div>
  </div>
</div>

<!-- Hidden export template -->
<div id="export-template">
  <h1>Månadsbudget – Sammanfattning</h1>
  <div class="exp-date" id="exp-date-text"></div>
  <div class="exp-section">
    <h2>Inkomster</h2><div id="exp-income-rows"></div>
    <div class="exp-total"><span>Total inkomst</span><span id="exp-income-total"></span></div>
  </div>
  <div class="exp-section">
    <h2>Fasta utgifter</h2><div id="exp-fixed-rows"></div>
    <div class="exp-total"><span>Total fasta</span><span id="exp-fixed-total"></span></div>
  </div>
  <div class="exp-section">
    <h2>Rörliga utgifter</h2><div id="exp-variable-rows"></div>
    <div class="exp-total"><span>Total rörliga</span><span id="exp-variable-total"></span></div>
  </div>
  <div class="exp-result">
    <div class="exp-result-label">KVAR ATT FÖRDELA</div>
    <div class="exp-result-amount" id="exp-result-amount"></div>
  </div>
  <div class="exp-saving-section" id="exp-saving-section">
    <h2>Sparande</h2><div id="exp-saving-rows"></div>
    <div class="exp-total"><span>Totalt sparande</span><span id="exp-saving-total"></span></div>
  </div>
</div>

<script>
  // ── Firebase Init ──────────────────────────────────────────────
  const firebaseConfig = {
    apiKey: "AIzaSyAE9i9wKC3I5KN0-Wk4EZrG-kx19YQ_brQ",
    authDomain: "manadsbudget-app.firebaseapp.com",
    projectId: "manadsbudget-app",
    storageBucket: "manadsbudget-app.firebasestorage.app",
    messagingSenderId: "910633634669",
    appId: "1:910633634669:web:5b40984799065bc51c2864",
    measurementId: "G-W84R57X1RV"
  };

  firebase.initializeApp(firebaseConfig);
  const auth = firebase.auth();
  const db = firebase.firestore();

  // ── State ──────────────────────────────────────────────────────
  let state = { income: [], fixed: [], variable: [], saving: [] };
  let nextId = 1;
  
  let currentUser = null;
  let activeBudgetId = null; // Either user's UID or a shared budget ID
  let unsubscribeSnapshot = null;
  let isSyncing = false;     // Prevent local input from triggering save loops

  // ── Setup & Auth Observers ─────────────────────────────────────
  auth.onAuthStateChanged(user => {
    currentUser = user;
    if (user) {
      document.getElementById('btn-login').style.display = 'none';
      document.getElementById('btn-logout').style.display = 'block';
      document.getElementById('btn-share').style.display = 'block';
      document.getElementById('user-info').innerHTML = `Inloggad som: <b>${user.email || 'Google User'}</b>`;
      document.getElementById('header-sync').style.display = 'block';
      
      // Determine which budget to load. Check users collection.
      db.collection('users').doc(user.uid).get().then(doc => {
        if (doc.exists && doc.data().activeBudgetId) {
          listenToBudget(doc.data().activeBudgetId);
        } else {
          // Default to own budget
          db.collection('users').doc(user.uid).set({ activeBudgetId: user.uid }, { merge: true });
          listenToBudget(user.uid);
        }
      });
    } else {
      document.getElementById('btn-login').style.display = 'block';
      document.getElementById('btn-logout').style.display = 'none';
      document.getElementById('btn-share').style.display = 'none';
      document.getElementById('user-info').innerHTML = '';
      document.getElementById('header-sync').style.display = 'none';
      activeBudgetId = null;
      if (unsubscribeSnapshot) unsubscribeSnapshot();
      
      // Load from local storage
      if (!loadState()) {
        prefillDummy();
      }
    }
  });

  function listenToBudget(budgetId) {
    if (unsubscribeSnapshot) unsubscribeSnapshot();
    activeBudgetId = budgetId;
    
    unsubscribeSnapshot = db.collection('budgets').doc(budgetId).onSnapshot(doc => {
      isSyncing = true;
      if (doc.exists) {
        const data = doc.data();
        state = {
          income: data.income || [],
          fixed: data.fixed || [],
          variable: data.variable || [],
          saving: data.saving || []
        };
        nextId = data.nextId || 1;
      } else {
        // First time cloud creation, push current local state if any, else empty
        if (state.income.length === 0 && state.fixed.length === 0) prefillDummy();
        saveToCloud();
      }
      renderAll();
      isSyncing = false;
    });
  }

  function saveState() {
    if (isSyncing) return; // Don't trigger saves from incoming cloud updates

    if (currentUser && activeBudgetId) {
      saveToCloud();
    } else {
      localStorage.setItem('manadsbudget_v2', JSON.stringify({ state, nextId }));
    }
  }

  function saveToCloud() {
    if(!activeBudgetId) return;
    db.collection('budgets').doc(activeBudgetId).set({
      income: state.income,
      fixed: state.fixed,
      variable: state.variable,
      saving: state.saving,
      nextId: nextId,
      updatedAt: firebase.firestore.FieldValue.serverTimestamp()
    });
  }

  function loadState() {
    try {
      const raw = localStorage.getItem('manadsbudget_v2');
      if (!raw) return false;
      const saved = JSON.parse(raw);
      state  = saved.state;
      nextId = saved.nextId || 1;
      renderAll();
      return true;
    } catch(e) { return false; }
  }

  function prefillDummy() {
    state = { income: [], fixed: [], variable: [], saving: [] };
    addRow('income',   { name:'Lön',          amount: 35000 }, true);
    addRow('fixed',    { name:'Hyra',          amount: 9500  }, true);
    addRow('fixed',    { name:'Hemförsäkring', amount: 250   }, true);
    addRow('variable', { name:'Mat',           amount: 3500  }, true);
    addRow('variable', { name:'Nöje',          amount: 1000  }, true);
    addSavingRow({ name:'Buffert', type:'percent', value: 10 }, true);
    saveState();
  }

  function init() {
    updateDateDisplay();
  }

  function updateDateDisplay() {
    const now = new Date();
    document.getElementById('header-date').textContent = now.toLocaleDateString('sv-SE', { year:'numeric', month:'long' });
    document.getElementById('exp-date-text').textContent = now.toLocaleDateString('sv-SE', { weekday:'long', year:'numeric', month:'long', day:'numeric' });
  }

  // ── Auth & Share Functions ─────────────────────────────────────
  function openAuthModal()  { document.getElementById('auth-modal').classList.add('open'); }
  function closeAuthModal() { document.getElementById('auth-modal').classList.remove('open'); }
  
  async function handleEmailAuth(mode) {
    const email = document.getElementById('auth-email').value;
    const pass = document.getElementById('auth-password').value;
    if(!email || !pass) return showToast('Fyll i mejl och lösenord');
    try {
      if(mode === 'login') {
        await auth.signInWithEmailAndPassword(email, pass);
        showToast('Inloggad!');
      } else {
        await auth.createUserWithEmailAndPassword(email, pass);
        showToast('Konto skapat!');
      }
      closeAuthModal();
    } catch(e) { showToast('Fel: ' + e.message); }
  }

  async function handleGoogleAuth() {
    try {
      const provider = new firebase.auth.GoogleAuthProvider();
      await auth.signInWithPopup(provider);
      closeAuthModal();
      showToast('Inloggad med Google!');
    } catch(e) { showToast('Inloggning avbröts'); }
  }

  function logout() {
    auth.signOut();
    showToast('Utloggad');
  }

  function openShareModal() {
    document.getElementById('share-my-id').value = activeBudgetId || 'Ingen budget vald';
    document.getElementById('share-join-id').value = '';
    document.getElementById('share-modal').classList.add('open');
  }
  function closeShareModal() { document.getElementById('share-modal').classList.remove('open'); }

  function joinBudget() {
    const newId = document.getElementById('share-join-id').value.trim();
    if(!newId) return;
    if(!currentUser) return showToast('Du måste vara inloggad');
    
    // Check if budget exists
    db.collection('budgets').doc(newId).get().then(doc => {
      if(doc.exists) {
        // Point user to new budget
        db.collection('users').doc(currentUser.uid).set({ activeBudgetId: newId }, { merge: true });
        closeShareModal();
        showToast('Gick med i delad budget!');
      } else {
        showToast('Hittade ingen budget med den koden');
      }
    });
  }

  // ── Core Logistics ─────────────────────────────────────────────
  function addRow(section, prefill = {}, skipSave = false) {
    const id = nextId++;
    const item = { id, name: prefill.name || '', amount: prefill.amount || '' };
    state[section].push(item);
    if(!skipSave) { renderAll(); saveState(); }
  }
  function addSavingRow(prefill = {}, skipSave = false) {
    const id = nextId++;
    const item = { id, name: prefill.name || '', type: prefill.type || 'percent', value: prefill.value || '' };
    state.saving.push(item);
    if(!skipSave) { renderAll(); saveState(); }
  }
  function removeRow(section, id) {
    state[section] = state[section].filter(r => r.id !== id);
    renderAll(); saveState();
  }
  window.triggerUpdateField = function(section, id, field, value) {
    const item = state[section].find(r => r.id === id);
    if (item) item[field] = value;
    recalc();
    saveState();
  }

  function renderAll() {
    ['income','fixed','variable'].forEach(s => renderSection(s));
    renderSaving();
    recalc();
  }

  function renderSection(section) {
    const list = document.getElementById(section + '-list');
    list.innerHTML = '';
    state[section].forEach(item => {
      const row = document.createElement('div');
      row.className = 'entry-row normal';
      row.innerHTML = `
        <input type="text" placeholder="Namn" value="${escH(item.name)}" oninput="triggerUpdateField('${section}', ${item.id}, 'name', this.value)" />
        <input type="number" placeholder="0" min="0" value="${item.amount}" oninput="triggerUpdateField('${section}', ${item.id}, 'amount', this.value)" />
        <button class="del-btn" onclick="removeRow('${section}', ${item.id})">✕</button>
      `;
      list.appendChild(row);
    });
  }

  function renderSaving() {
    const list = document.getElementById('saving-list');
    list.innerHTML = '';
    const available = getAvailable();
    state.saving.forEach(item => {
      const calculated = calcSaving(item, available);
      const row = document.createElement('div');
      row.className = 'entry-row saving-row';
      row.innerHTML = `
        <input type="text" placeholder="Sparmål" value="${escH(item.name)}" oninput="triggerUpdateField('saving', ${item.id}, 'name', this.value)" />
        <select onchange="triggerUpdateField('saving', ${item.id}, 'type', this.value)">
          <option value="percent" ${item.type === 'percent' ? 'selected' : ''}>%</option>
          <option value="fixed"   ${item.type === 'fixed'   ? 'selected' : ''}>kr</option>
        </select>
        <input type="number" placeholder="0" min="0" value="${item.value}" oninput="triggerUpdateField('saving', ${item.id}, 'value', this.value)" />
        <button class="del-btn" onclick="removeRow('saving', ${item.id})">✕</button>
      `;
      const calc = document.createElement('div');
      calc.className = 'saving-calc';
      if (available > 0 && (parseFloat(item.value) || 0) > 0) {
        calc.textContent = '= ' + fmt(calculated);
      }
      list.appendChild(row);
      list.appendChild(calc);
    });
  }

  function fmt(n) { return new Intl.NumberFormat('sv-SE', { style:'currency', currency:'SEK', maximumFractionDigits: 0 }).format(n); }
  function sumSection(arr) { return arr.reduce((s, r) => s + (parseFloat(r.amount) || 0), 0); }
  function getAvailable() { return sumSection(state.income) - sumSection(state.fixed) - sumSection(state.variable); }
  function calcSaving(item, available) {
    const v = parseFloat(item.value) || 0;
    if (item.type === 'percent') return Math.max(0, available) * v / 100;
    return v;
  }
  function escH(s) { return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

  function recalc() {
    const income   = sumSection(state.income);
    const fixed    = sumSection(state.fixed);
    const variable = sumSection(state.variable);
    const available = income - fixed - variable;
    const available_pos = Math.max(0, available);

    document.getElementById('income-total').textContent   = fmt(income);
    document.getElementById('fixed-total').textContent    = fmt(fixed);
    document.getElementById('variable-total').textContent = fmt(variable);

    const resEl = document.getElementById('result-amount');
    resEl.textContent = fmt(available);
    resEl.className = 'result-amount ' + (available >= 0 ? 'positive' : 'negative');

    document.getElementById('bd-income').textContent   = fmt(income);
    document.getElementById('bd-fixed').textContent    = fmt(fixed);
    document.getElementById('bd-variable').textContent = fmt(variable);

    let savingTotal = 0;
    state.saving.forEach(item => { savingTotal += calcSaving(item, available_pos); });
    document.getElementById('saving-total').textContent = fmt(savingTotal);

    const unalloc = available_pos - savingTotal;
    const unallocEl = document.getElementById('saving-unallocated');
    const warnEl    = document.getElementById('saving-warning');

    if (available_pos > 0) unallocEl.innerHTML = `Ofördelat: <strong>${fmt(Math.max(0, unalloc))}</strong>`;
    else unallocEl.innerHTML = '';

    if (savingTotal > available_pos && available_pos > 0) warnEl.classList.add('over');
    else warnEl.classList.remove('over');
    
    // Update live calculations in DOM without losing focus on inputs
    const calcEls = document.querySelectorAll('.saving-calc');
    state.saving.forEach((item, i) => {
      if(calcEls[i]) {
        const calculated = calcSaving(item, available_pos);
        if (available_pos > 0 && (parseFloat(item.value) || 0) > 0) {
          calcEls[i].textContent = '= ' + fmt(calculated);
        } else {
          calcEls[i].textContent = '';
        }
      }
    });
  }

  // ── New month ─────────────────────────────────────────────────
  function openNewMonthModal()  { document.getElementById('newmonth-modal').classList.add('open'); }
  function closeNewMonthModal() { document.getElementById('newmonth-modal').classList.remove('open'); }

  function confirmNewMonth() {
    closeNewMonthModal();
    state.income   = [];
    state.variable = [];
    state.saving   = [];
    state.fixed = state.fixed.map(r => ({ ...r }));
    renderAll();
    saveState();
    updateDateDisplay();
    showToast('✅ Ny månad startad – fasta utgifter behållna!');
  }

  function showToast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2800);
  }

  // ── Export as PNG ──────────────────────────────────────────────
  async function exportImage() {
    const available = getAvailable();
    const available_pos = Math.max(0, available);

    fillExpRows('exp-income-rows', state.income);
    fillExpRows('exp-fixed-rows', state.fixed);
    fillExpRows('exp-variable-rows', state.variable);

    document.getElementById('exp-income-total').textContent   = fmt(sumSection(state.income));
    document.getElementById('exp-fixed-total').textContent    = fmt(sumSection(state.fixed));
    document.getElementById('exp-variable-total').textContent = fmt(sumSection(state.variable));

    const resEl = document.getElementById('exp-result-amount');
    resEl.textContent = fmt(available);
    resEl.className = 'exp-result-amount ' + (available >= 0 ? 'positive' : 'negative');

    const savRows = document.getElementById('exp-saving-rows');
    savRows.innerHTML = '';
    let savTotal = 0;
    state.saving.forEach(item => {
      const calc = calcSaving(item, available_pos);
      savTotal += calc;
      const row = document.createElement('div');
      row.className = 'exp-row';
      const typeLabel = item.type === 'percent' ? `${item.value}%` : '';
      row.innerHTML = `<span>${escH(item.name)} ${typeLabel}</span><span>${fmt(calc)}</span>`;
      savRows.appendChild(row);
    });
    document.getElementById('exp-saving-total').textContent = fmt(savTotal);

    const tpl = document.getElementById('export-template');
    tpl.style.left = '-9999px';

    const canvas = await html2canvas(tpl, { scale: 2, backgroundColor: '#ffffff', useCORS: true });
    const link = document.createElement('a');
    const now  = new Date();
    const dateStr = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`;
    link.download = `manadsbudget-${dateStr}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  }

  function fillExpRows(containerId, arr) {
    const el = document.getElementById(containerId);
    el.innerHTML = '';
    arr.forEach(item => {
      const row = document.createElement('div');
      row.className = 'exp-row';
      row.innerHTML = `<span>${escH(item.name) || '–'}</span><span>${fmt(parseFloat(item.amount)||0)}</span>`;
      el.appendChild(row);
    });
    if (arr.length === 0) el.innerHTML = '<div class="exp-row" style="color:#9ca3af"><span>–</span><span>0 kr</span></div>';
  }

  init();

  // ── Service Worker ─────────────────────────────────────────────
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('./sw.js').catch(() => {});
    });
  }
</script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

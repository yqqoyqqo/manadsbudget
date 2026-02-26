import re

with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Add CSS
css_add = """
    .budget-meta-header {
      margin-top: 15px;
      display: flex;
      justify-content: center;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }
    .budget-select, .budget-name-input {
      padding: 8px 12px;
      border: 1.5px solid var(--border);
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 600;
      outline: none;
      color: var(--text);
    }
    .budget-select { cursor: pointer; background: #fff; min-width: 150px; }
    .budget-name-input { width: 220px; }
    .budget-name-input:focus { border-color: #0369a1; }

    .status-options {
      display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap;
    }
    .status-btn {
      flex: 1;
      padding: 10px;
      border: 1.5px solid var(--border);
      background: #fff;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.9rem;
      cursor: pointer;
      color: var(--muted);
      transition: all 0.2s;
    }
    .status-btn.active.none { background: #f1f5f9; border-color: #cbd5e1; color: var(--text); }
    .status-btn.active.success { background: #f0fdf4; border-color: #bbf7d0; color: #16a34a; }
    .status-btn.active.failed { background: #fef2f2; border-color: #fecaca; color: #dc2626; }
    .budget-comment {
      width: 100%;
      min-height: 80px;
      border: 1.5px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      font-family: inherit;
      font-size: 0.85rem;
      color: var(--text);
      resize: vertical;
      outline: none;
      transition: border-color 0.2s;
    }
    .budget-comment:focus { border-color: #94a3b8; }
"""
content = content.replace("/* Auth & Share UI */", css_add + "\n    /* Auth & Share UI */")

# Add HTML Header
html_head = """<header>
  <h1>📊 Månadsbudget</h1>
  <div class="budget-meta-header" id="meta-header" style="display:none;">
    <select id="budget-selector" onchange="switchBudgetSelector(this.value)" class="budget-select"></select>
    <input type="text" id="budget-name-input" oninput="updateBudgetMeta('name', this.value)" placeholder="Budgetens namn" class="budget-name-input" />
  </div>
  <p class="sub" id="header-date"></p>
  <p class="sub" id="header-sync" style="color:#0369a1; font-weight:600; display:none;">☁️ Sparas i molnet</p>
</header>"""
content = re.sub(r"<header>.*?</header>", html_head, content, flags=re.DOTALL)

# Add Evaluation HTML
html_eval = """  <!-- EVALUATION -->
  <div class="card meta-card full" id="meta-card">
    <div class="card-header">
      <div class="dot" style="background:#6b7280"></div>
      <h2>Utvärdering & Anteckningar</h2>
    </div>
    <div class="status-options">
      <button class="status-btn none active" id="btn-status-none" onclick="updateBudgetMeta('status', 'none')">➖ Pågående</button>
      <button class="status-btn success" id="btn-status-success" onclick="updateBudgetMeta('status', 'success')">✅ Lyckad</button>
      <button class="status-btn failed" id="btn-status-failed" onclick="updateBudgetMeta('status', 'failed')">❌ Misslyckad</button>
    </div>
    <textarea id="budget-comment" class="budget-comment" placeholder="Skriv dina reflektioner här (t.ex. 'Oväntad bilreparation spräckte budgeten')..." oninput="debounceUpdateComment(this.value)"></textarea>
  </div>

  <!-- EXPORT / NEW MONTH -->"""
content = content.replace("<!-- EXPORT / NEW MONTH -->", html_eval)

# Replace JS state & Auth block
js_state = """  // ── State ──────────────────────────────────────────────────────
  let state = { income: [], fixed: [], variable: [], saving: [] };
  let nextId = 1;
  let budgetMeta = { name: '', status: 'none', comment: '' };
  let userBudgets = [];
  
  let currentUser = null;
  let activeBudgetId = null; 
  let unsubscribeSnapshot = null;
  let unsubscribeBudgetsList = null;
  let isSyncing = false;     

  // ── Setup & Auth Observers ─────────────────────────────────────
  auth.onAuthStateChanged(user => {
    currentUser = user;
    if (user) {
      document.getElementById('btn-login').style.display = 'none';
      document.getElementById('btn-logout').style.display = 'block';
      document.getElementById('btn-share').style.display = 'block';
      document.getElementById('user-info').innerHTML = `Inloggad som: <b>${user.email || 'Google User'}</b>`;
      document.getElementById('header-sync').style.display = 'block';
      
      document.getElementById('meta-header').style.display = 'flex';

      // Migrate legacy budget
      db.collection('budgets').doc(user.uid).get().then(doc => {
        if(doc.exists && !doc.data().collaborators) {
          db.collection('budgets').doc(user.uid).update({
            collaborators: [user.uid],
            name: 'Min Budget',
            status: 'none',
            comment: '',
            createdAt: firebase.firestore.FieldValue.serverTimestamp()
          });
        }
      });

      // Listen to all budgets where user is a collaborator
      unsubscribeBudgetsList = db.collection('budgets')
        .where('collaborators', 'array-contains', user.uid)
        .onSnapshot(snapshot => {
          let list = [];
          snapshot.forEach(doc => list.push({ id: doc.id, ...doc.data() }));
          
          list.sort((a,b) => (b.createdAt?.toMillis() || 0) - (a.createdAt?.toMillis() || 0));
          userBudgets = list;
          renderBudgetSelector();
          
          if (list.length === 0) {
            createNewBudget("Min första budget");
          } else {
            db.collection('users').doc(user.uid).get().then(uDoc => {
              let targetId = list[0].id;
              if (uDoc.exists && uDoc.data().activeBudgetId && list.find(b => b.id === uDoc.data().activeBudgetId)) {
                targetId = uDoc.data().activeBudgetId;
              } else {
                db.collection('users').doc(user.uid).set({ activeBudgetId: targetId }, {merge:true});
              }
              if(activeBudgetId !== targetId) {
                switchBudget(targetId);
              } else {
                renderBudgetSelector(); // Keep dropdown in sync
              }
            });
          }
        });
    } else {
      document.getElementById('btn-login').style.display = 'block';
      document.getElementById('btn-logout').style.display = 'none';
      document.getElementById('btn-share').style.display = 'none';
      document.getElementById('user-info').innerHTML = '';
      document.getElementById('header-sync').style.display = 'none';
      document.getElementById('meta-header').style.display = 'none';
      activeBudgetId = null;
      if (unsubscribeSnapshot) unsubscribeSnapshot();
      if (unsubscribeBudgetsList) unsubscribeBudgetsList();
      
      if (!loadState()) prefillDummy();
    }
  });

  function createNewBudget(name, fixedToCarry = []) {
    if(!currentUser) return;
    const newBudgetRef = db.collection('budgets').doc();
    newBudgetRef.set({
      name: name || 'Ny Budget',
      status: 'none',
      comment: '',
      income: [],
      fixed: fixedToCarry,
      variable: [],
      saving: [],
      nextId: fixedToCarry.length > 0 ? getNextMaxId(fixedToCarry) : 1,
      collaborators: [currentUser.uid],
      createdAt: firebase.firestore.FieldValue.serverTimestamp(),
      updatedAt: firebase.firestore.FieldValue.serverTimestamp()
    }).then(() => {
      switchBudget(newBudgetRef.id);
    });
  }

  function getNextMaxId(arr) {
    let max = 0;
    arr.forEach(i => { if(i.id > max) max = i.id; });
    return max + 1;
  }

  window.switchBudgetSelector = function(val) {
     if(val !== activeBudgetId) switchBudget(val);
  }

  function switchBudget(budgetId) {
    activeBudgetId = budgetId;
    db.collection('users').doc(currentUser.uid).set({ activeBudgetId: budgetId }, { merge: true });
    
    if (unsubscribeSnapshot) unsubscribeSnapshot();
    
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
        budgetMeta = {
          name: data.name || '',
          status: data.status || 'none',
          comment: data.comment || ''
        };
        updateMetaUI();
        renderAll();
      }
      isSyncing = false;
    });
  }

  function renderBudgetSelector() {
    const sel = document.getElementById('budget-selector');
    sel.innerHTML = '';
    userBudgets.forEach(b => {
      const opt = document.createElement('option');
      opt.value = b.id;
      opt.textContent = b.name || 'Namnlös budget';
      if(b.id === activeBudgetId) opt.selected = true;
      sel.appendChild(opt);
    });
  }

  function updateMetaUI() {
    const nameInput = document.getElementById('budget-name-input');
    const commentInput = document.getElementById('budget-comment');
    
    if (document.activeElement !== nameInput) nameInput.value = budgetMeta.name;
    if (document.activeElement !== commentInput) commentInput.value = budgetMeta.comment;
    
    ['none', 'success', 'failed'].forEach(s => {
      const btn = document.getElementById('btn-status-' + s);
      if(btn) btn.classList.remove('active', 'none', 'success', 'failed');
    });
    const activeBtn = document.getElementById('btn-status-' + budgetMeta.status);
    if(activeBtn) activeBtn.classList.add('active', budgetMeta.status);
  }
  
  window.updateBudgetMeta = function(field, value, skipCloud = false) {
    budgetMeta[field] = value;
    updateMetaUI();
    if(!skipCloud) {
       if (currentUser && activeBudgetId) {
         db.collection('budgets').doc(activeBudgetId).update({
           [field]: value,
           updatedAt: firebase.firestore.FieldValue.serverTimestamp()
         });
       } else {
         saveState();
       }
    }
  }

  let commentTimeout;
  window.debounceUpdateComment = function(val) {
    clearTimeout(commentTimeout);
    commentTimeout = setTimeout(() => { updateBudgetMeta('comment', val); }, 700);
  }

  function saveState() {
    if (isSyncing) return;
    if (currentUser && activeBudgetId) {
      saveToCloud();
    } else {
      localStorage.setItem('manadsbudget_v4', JSON.stringify({ state, nextId, budgetMeta }));
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
      name: budgetMeta.name || '',
      status: budgetMeta.status || 'none',
      comment: budgetMeta.comment || '',
      updatedAt: firebase.firestore.FieldValue.serverTimestamp()
    }, {merge:true});
  }

  function loadState() {
    try {
      const raw = localStorage.getItem('manadsbudget_v4');
      if (!raw) return false;
      const saved = JSON.parse(raw);
      state  = saved.state;
      nextId = saved.nextId || 1;
      budgetMeta = saved.budgetMeta || { name: 'Lokal Budget', status: 'none', comment: '' };
      updateMetaUI();
      renderAll();
      return true;
    } catch(e) { return false; }
  }

  function prefillDummy() {
    state = { income: [], fixed: [], variable: [], saving: [] };
    const now = new Date();
    const name = now.toLocaleDateString('sv-SE', { month: 'long', year: 'numeric' });
    budgetMeta = { name: name.charAt(0).toUpperCase() + name.slice(1), status: 'none', comment: '' };
    addRow('income',   { name:'Lön',          amount: 35000 }, true);
    addRow('fixed',    { name:'Hyra',          amount: 9500  }, true);
    addRow('fixed',    { name:'Hemförsäkring', amount: 250   }, true);
    addRow('variable', { name:'Mat',           amount: 3500  }, true);
    addRow('variable', { name:'Nöje',          amount: 1000  }, true);
    addSavingRow({ name:'Buffert', type:'percent', value: 10 }, true);
    updateMetaUI();
    saveState();
  }
"""

content = re.sub(r"// ── State ─+.*?(?=  function init\(\))", js_state, content, flags=re.DOTALL)

# Replace "Ny månad" logic
js_new_month = """  function confirmNewMonth() {
    closeNewMonthModal();
    const fixedToKeep = state.fixed.map(r => ({ ...r }));
    
    if (currentUser) {
      const now = new Date();
      now.setMonth(now.getMonth() + 1);
      const name = now.toLocaleDateString('sv-SE', { month: 'long', year: 'numeric' });
      const capName = name.charAt(0).toUpperCase() + name.slice(1);
      
      createNewBudget(capName, fixedToKeep);
      showToast('✅ Ny budget skapad ("' + capName + '")!');
    } else {
      state.income   = [];
      state.variable = [];
      state.saving   = [];
      state.fixed = fixedToKeep;
      
      const now = new Date();
      now.setMonth(now.getMonth() + 1);
      const name = now.toLocaleDateString('sv-SE', { month: 'long', year: 'numeric' });
      budgetMeta.name = name.charAt(0).toUpperCase() + name.slice(1);
      budgetMeta.status = 'none';
      budgetMeta.comment = '';
      
      renderAll();
      updateMetaUI();
      saveState();
      updateDateDisplay();
      showToast('✅ Ny månad startad lokalt!');
    }
  }"""
  
content = re.sub(r"function confirmNewMonth\(\) \{.*?(?=  function showToast\()", js_new_month + "\n\n", content, flags=re.DOTALL)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated index.html successfully.")

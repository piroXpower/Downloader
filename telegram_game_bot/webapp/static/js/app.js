// Telegram Game Hub - WebApp Frontend Engine
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  if (tg.enableClosingConfirmation) tg.enableClosingConfirmation();
}

// User state
const currentUser = {
  id: tg?.initDataUnsafe?.user?.id || 10001,
  first_name: tg?.initDataUnsafe?.user?.first_name || 'Player',
  username: tg?.initDataUnsafe?.user?.username || 'player_one',
  totalScore: 0,
  rank: 1,
  gamesPlayed: 0
};

// State variables
let allGames = [];
let filteredGames = [];
let currentCategory = 'all';
let searchQuery = '';
let renderedCount = 0;
const BATCH_SIZE = 36;
let favorites = JSON.parse(localStorage.getItem('game_favorites') || '[]');
let activeGame = null;

// Category Emojis
const categoryIcons = {
  'Arcade': '🕹️',
  'Puzzle': '🧩',
  'Action': '⚔️',
  'Racing': '🏎️',
  'Sports': '⚽',
  'Retro': '👾',
  'Cards & Board': '🃏',
  'Casual': '🎯'
};

// Initialize UI
document.addEventListener('DOMContentLoaded', async () => {
  setupHeader();
  setupEventListeners();
  await loadGames();
  await loadUserProfile();
});

function setupHeader() {
  document.getElementById('header-user-name').innerText = currentUser.first_name;
  document.getElementById('prof-user-name').innerText = currentUser.first_name;
  document.getElementById('prof-user-id').innerText = `ID: ${currentUser.id} (@${currentUser.username})`;
}

async function loadGames() {
  try {
    const res = await fetch('/api/games?limit=1000');
    const data = await res.json();
    allGames = data.games || [];
    filterAndRender();
  } catch (err) {
    console.error('Failed to load games:', err);
    document.getElementById('games-grid').innerHTML = '<div class="empty-state">Failed to load games. Please refresh.</div>';
  }
}

async function loadUserProfile() {
  try {
    const res = await fetch(`/api/user/${currentUser.id}/stats?first_name=${encodeURIComponent(currentUser.first_name)}&username=${encodeURIComponent(currentUser.username)}`);
    const data = await res.json();
    if (data) {
      currentUser.totalScore = data.total_score || 0;
      currentUser.rank = data.rank || 1;
      currentUser.gamesPlayed = data.total_games_played || 0;

      document.getElementById('header-user-score').innerText = currentUser.totalScore;
      document.getElementById('prof-total-score').innerText = currentUser.totalScore;
      document.getElementById('prof-rank').innerText = `#${currentUser.rank}`;
      document.getElementById('prof-played').innerText = currentUser.gamesPlayed;
    }
  } catch (e) {
    console.warn('Could not fetch user profile:', e);
  }
}

function filterAndRender() {
  filteredGames = allGames.filter(g => {
    const matchCat = currentCategory === 'all' || g.category === currentCategory;
    const matchSearch = !searchQuery || 
      g.title.toLowerCase().includes(searchQuery) || 
      g.category.toLowerCase().includes(searchQuery) ||
      (g.tags && g.tags.some(t => t.toLowerCase().includes(searchQuery)));
    return matchCat && matchSearch;
  });

  const grid = document.getElementById('games-grid');
  grid.innerHTML = '';
  renderedCount = 0;

  document.getElementById('game-counter').innerText = `${filteredGames.length.toLocaleString()} Games`;
  const secTitle = currentCategory === 'all' ? 'All Games' : `${currentCategory} Games`;
  document.getElementById('current-section-title').innerText = searchQuery ? `Search: "${searchQuery}"` : secTitle;

  renderBatch();
}

function renderBatch() {
  const grid = document.getElementById('games-grid');
  const nextSlice = filteredGames.slice(renderedCount, renderedCount + BATCH_SIZE);

  if (filteredGames.length === 0) {
    grid.innerHTML = '<div class="empty-state" style="grid-column: 1/-1;">No games found matching your search.</div>';
    document.getElementById('load-more-btn').style.display = 'none';
    return;
  }

  const fragment = document.createDocumentFragment();
  nextSlice.forEach(game => {
    const card = createGameCard(game);
    fragment.appendChild(card);
  });
  grid.appendChild(fragment);

  renderedCount += nextSlice.length;

  const loadMoreBtn = document.getElementById('load-more-btn');
  if (renderedCount < filteredGames.length) {
    loadMoreBtn.style.display = 'inline-block';
    loadMoreBtn.innerText = `Load More (${filteredGames.length - renderedCount} remaining) ⬇`;
  } else {
    loadMoreBtn.style.display = 'none';
  }
}

function createGameCard(game) {
  const card = document.createElement('div');
  card.className = 'game-card';
  card.onclick = () => openGame(game.id);

  const icon = categoryIcons[game.category] || '🎮';
  const isFav = favorites.includes(game.id);

  card.innerHTML = `
    <div class="game-thumb-box">
      <span>${icon}</span>
      ${game.badge ? `<div class="game-badge">${game.badge}</div>` : ''}
      <button class="fav-btn ${isFav ? 'active' : ''}" onclick="toggleFav(event, '${game.id}')">
        ${isFav ? '❤️' : '🤍'}
      </button>
    </div>
    <div class="game-info">
      <div class="game-title" title="${game.title}">${game.title}</div>
      <div class="game-meta">
        <span class="game-rating">★ ${game.rating}</span>
        <span>${formatNumber(game.plays)} plays</span>
      </div>
      <div class="play-action-btn">▶ PLAY</div>
    </div>
  `;
  return card;
}

function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num;
}

function toggleFav(e, gameId) {
  e.stopPropagation();
  if (favorites.includes(gameId)) {
    favorites = favorites.filter(id => id !== gameId);
  } else {
    favorites.push(gameId);
  }
  localStorage.setItem('game_favorites', JSON.stringify(favorites));
  if (tg?.HapticFeedback) tg.HapticFeedback.selectionChanged();
  
  // Re-render fav button
  filterAndRender();

  // Inform backend
  fetch('/api/favorite', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: currentUser.id, game_id: gameId })
  }).catch(() => {});
}

// Game Player
function openGame(gameId) {
  const game = allGames.find(g => g.id === gameId);
  if (!game) return;

  activeGame = game;
  const modal = document.getElementById('game-modal');
  const iframe = document.getElementById('game-iframe');
  document.getElementById('modal-game-title').innerText = game.title;

  iframe.src = game.builtin_path;
  modal.classList.add('open');

  if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');

  // Increment play count
  fetch(`/api/games/${gameId}/play`, { method: 'POST' }).catch(() => {});
}

function closeGame() {
  const modal = document.getElementById('game-modal');
  const iframe = document.getElementById('game-iframe');
  iframe.src = '';
  modal.classList.remove('open');
  activeGame = null;
  loadUserProfile(); // Refresh score
}

function shareCurrentGame() {
  if (!activeGame) return;
  const shareText = `🎮 Play ${activeGame.title} on Telegram Game Hub! Can you beat my high score?`;
  const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(window.location.origin)}&text=${encodeURIComponent(shareText)}`;

  if (tg?.openTelegramLink) {
    tg.openTelegramLink(shareUrl);
  } else {
    window.open(shareUrl, '_blank');
  }
}

// Listen for score events from embedded games
window.addEventListener('message', async (e) => {
  if (e.data && e.data.type === 'SCORE_UPDATE') {
    const { gameId, score } = e.data;
    console.log(`Received score update for ${gameId}: ${score}`);

    try {
      const res = await fetch('/api/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUser.id,
          username: currentUser.username,
          first_name: currentUser.first_name,
          game_id: gameId,
          score: score
        })
      });
      const data = await res.json();
      if (data.is_new_high_score && tg?.showAlert) {
        tg.showAlert(`🎉 NEW HIGH SCORE: ${score} in ${activeGame?.title || 'the game'}!`);
      }
      loadUserProfile();
    } catch (err) {
      console.error('Failed to submit score:', err);
    }
  }
});

// Navigation switches
function switchNav(tab) {
  document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.view-modal').forEach(m => m.classList.remove('open'));

  const navBtn = document.getElementById(`nav-${tab}`);
  if (navBtn) navBtn.classList.add('active');

  if (tab === 'games') {
    document.getElementById('main-view').style.display = 'block';
  } else {
    document.getElementById('main-view').style.display = 'none';
    const viewModal = document.getElementById(`${tab}-view`);
    if (viewModal) viewModal.classList.add('open');

    if (tab === 'leaderboard') renderLeaderboard();
    if (tab === 'favorites') renderFavorites();
    if (tab === 'profile') loadUserProfile();
  }
}

async function renderLeaderboard() {
  const container = document.getElementById('leaderboard-list');
  container.innerHTML = '<div class="empty-state">Loading top players...</div>';
  try {
    const res = await fetch('/api/leaderboard');
    const data = await res.json();
    const leaders = data.leaderboard || [];

    if (leaders.length === 0) {
      container.innerHTML = '<div class="empty-state">No scores yet. Be the first to play and rank #1!</div>';
      return;
    }

    container.innerHTML = leaders.map((u, i) => {
      let rankMedal = `#${i + 1}`;
      if (i === 0) rankMedal = '🥇 1';
      else if (i === 1) rankMedal = '🥈 2';
      else if (i === 2) rankMedal = '🥉 3';

      return `
        <div class="leader-item">
          <div class="leader-rank">${rankMedal}</div>
          <div class="leader-name">${u.first_name || u.username || 'Anonymous Player'}</div>
          <div class="leader-score">⭐ ${u.total_score.toLocaleString()}</div>
        </div>
      `;
    }).join('');
  } catch (e) {
    container.innerHTML = '<div class="empty-state">Failed to load leaderboard.</div>';
  }
}

function renderFavorites() {
  const container = document.getElementById('favorites-grid');
  const favGames = allGames.filter(g => favorites.includes(g.id));

  if (favGames.length === 0) {
    container.innerHTML = '<div class="empty-state" style="grid-column: 1/-1;">You have not favorited any games yet.<br>Tap the ❤️ icon on any game to save it here!</div>';
    return;
  }

  container.innerHTML = '';
  favGames.forEach(game => {
    container.appendChild(createGameCard(game));
  });
}

// Event Listeners
function setupEventListeners() {
  // Category tabs
  const tabs = document.querySelectorAll('.cat-tab');
  tabs.forEach(tab => {
    tab.onclick = () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentCategory = tab.dataset.cat;
      filterAndRender();
      if (tg?.HapticFeedback) tg.HapticFeedback.selectionChanged();
    };
  });

  // Search input with debounce
  const searchInput = document.getElementById('search-input');
  const searchClear = document.getElementById('search-clear');

  let debounceTimer = null;
  searchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    searchQuery = e.target.value.trim().toLowerCase();
    searchClear.style.display = searchQuery ? 'block' : 'none';

    debounceTimer = setTimeout(() => {
      filterAndRender();
    }, 200);
  });

  searchClear.onclick = () => {
    searchInput.value = '';
    searchQuery = '';
    searchClear.style.display = 'none';
    filterAndRender();
  };

  // Load more button
  document.getElementById('load-more-btn').onclick = () => {
    renderBatch();
  };

  // Infinite scroll
  window.addEventListener('scroll', () => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
      if (renderedCount < filteredGames.length) {
        renderBatch();
      }
    }
  });
}

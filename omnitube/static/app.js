/**
 * VidTube - YouTube-Style Video Player & Universal Multi-Platform Media Downloader
 * Frontend Engine
 */

document.addEventListener('DOMContentLoaded', () => {
  // --- STATE ---
  const state = {
    currentView: 'home',
    currentCategory: 'All',
    activeVideo: null,
    activeDownloadJob: null,
    pollTimer: null,
    likedVideos: new Set(),
    subscribedChannels: new Set(),
    downloads: JSON.parse(localStorage.getItem('vidtube_downloads') || '[]'),
    theme: localStorage.getItem('vidtube_theme') || 'dark',
    notifications: [
      { id: 1, text: "Welcome to VidTube All-In-One Downloader!", time: "Just now" }
    ],
    sampleVideos: []
  };

  // --- DOM ELEMENTS ---
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebar-toggle');
  const themeToggleBtn = document.getElementById('btn-theme-toggle');
  const themeIcon = document.getElementById('theme-icon');
  
  // Search inputs
  const urlSearchInput = document.getElementById('url-search-input');
  const searchForm = document.getElementById('search-download-form');
  const btnQuickPaste = document.getElementById('btn-quick-paste');
  const btnClearSearch = document.getElementById('btn-clear-search');
  
  // Hero section inputs
  const heroUrlInput = document.getElementById('hero-url-input');
  const heroPasteBtn = document.getElementById('hero-paste-btn');
  const heroFetchBtn = document.getElementById('hero-fetch-btn');

  // Views
  const views = {
    home: document.getElementById('view-home'),
    watch: document.getElementById('view-watch'),
    shorts: document.getElementById('view-shorts'),
    downloads: document.getElementById('view-downloads'),
    platforms: document.getElementById('view-platforms')
  };

  // Video Grid & Category Chips
  const videoFeedGrid = document.getElementById('video-feed-grid');
  const categoryChips = document.querySelectorAll('#category-chips .chip');

  // Watch page elements
  const videoPlayer = document.getElementById('html5-video-player');
  const watchPlatformTag = document.getElementById('watch-platform-tag');
  const watchTitle = document.getElementById('watch-title');
  const watchChannelAvatar = document.getElementById('watch-channel-avatar');
  const watchChannelName = document.getElementById('watch-channel-name');
  const watchChannelSubs = document.getElementById('watch-channel-subs');
  const btnSubscribe = document.getElementById('btn-subscribe');
  const btnLike = document.getElementById('btn-like');
  const watchLikes = document.getElementById('watch-likes');
  const btnDislike = document.getElementById('btn-dislike');
  const btnShare = document.getElementById('btn-share');
  const btnWatchDownload = document.getElementById('btn-watch-download');
  const watchViewsCount = document.getElementById('watch-views-count');
  const watchUploadDate = document.getElementById('watch-upload-date');
  const watchDescText = document.getElementById('watch-description-text');
  const descBox = document.getElementById('desc-box');
  const btnToggleDesc = document.getElementById('btn-toggle-desc');
  const commentsList = document.getElementById('comments-list');
  const commentsCountTitle = document.getElementById('comments-count-title');
  const newCommentInput = document.getElementById('new-comment-input');
  const commentActionsBar = document.getElementById('comment-actions-bar');
  const btnSubmitComment = document.getElementById('btn-submit-comment');
  const btnCancelComment = document.getElementById('btn-cancel-comment');
  const relatedVideosList = document.getElementById('related-videos-list');

  // Modal elements
  const downloadModal = document.getElementById('download-modal');
  const modalCloseBtn = document.getElementById('modal-close-btn');
  const modalLoader = document.getElementById('modal-loader');
  const modalError = document.getElementById('modal-error');
  const modalErrorMsg = document.getElementById('modal-error-msg');
  const modalDetails = document.getElementById('modal-details');
  const modalThumb = document.getElementById('modal-thumb');
  const modalDuration = document.getElementById('modal-duration');
  const modalPlatformBadge = document.getElementById('modal-platform-badge');
  const modalTitle = document.getElementById('modal-title');
  const modalUploader = document.getElementById('modal-uploader');
  const modalViews = document.getElementById('modal-views');
  const modalLikes = document.getElementById('modal-likes');
  const btnModalWatch = document.getElementById('btn-modal-watch');
  const videoFormatsList = document.getElementById('video-formats-list');
  const audioFormatsList = document.getElementById('audio-formats-list');
  const formatTabBtns = document.querySelectorAll('.format-tab-btn');
  const tabVideoFormats = document.getElementById('tab-video-formats');
  const tabAudioFormats = document.getElementById('tab-audio-formats');

  // Progress Box elements
  const progressBox = document.getElementById('download-progress-box');
  const progressStatusLabel = document.getElementById('progress-status-label');
  const progressPercent = document.getElementById('progress-percent');
  const progressBarFill = document.getElementById('progress-bar-fill');
  const progressSpeed = document.getElementById('progress-speed');
  const progressEta = document.getElementById('progress-eta');
  const progressCompleteActions = document.getElementById('progress-complete-actions');
  const btnSaveDisk = document.getElementById('btn-save-disk');

  // Notifications
  const btnNotifications = document.getElementById('btn-notifications');
  const notificationsMenu = document.getElementById('notifications-menu');
  const notiCountBadge = document.getElementById('noti-count');
  const notificationsList = document.getElementById('notifications-list');
  const btnClearNoti = document.getElementById('btn-clear-noti');

  // Downloads view
  const downloadsTasksList = document.getElementById('downloads-tasks-list');
  const downloadsEmpty = document.getElementById('downloads-empty');
  const activeDlBadge = document.getElementById('active-dl-badge');
  const platformsGrid = document.getElementById('platforms-grid');

  // --- THEME INITIALIZATION ---
  function applyTheme(t) {
    if (t === 'light') {
      document.body.classList.add('light-theme');
      document.body.classList.remove('dark-theme');
      themeIcon.className = 'ri-moon-line';
    } else {
      document.body.classList.add('dark-theme');
      document.body.classList.remove('light-theme');
      themeIcon.className = 'ri-sun-line';
    }
    localStorage.setItem('vidtube_theme', t);
    state.theme = t;
  }
  applyTheme(state.theme);

  themeToggleBtn.addEventListener('click', () => {
    applyTheme(state.theme === 'dark' ? 'light' : 'dark');
  });

  // --- SIDEBAR COLLAPSE TOGGLE ---
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    sidebar.classList.toggle('mobile-open');
  });

  // --- VIEW SWITCHING ---
  function switchView(viewName) {
    state.currentView = viewName;
    Object.keys(views).forEach(key => {
      if (views[key]) {
        views[key].classList.toggle('active', key === viewName);
      }
    });

    // Update active nav button
    document.querySelectorAll('.sidebar-item').forEach(el => {
      const targetView = el.dataset.view;
      if (targetView) {
        el.classList.toggle('active', targetView === viewName);
      }
    });

    // Pause player if leaving watch view
    if (viewName !== 'watch' && videoPlayer) {
      videoPlayer.pause();
    }

    if (viewName === 'downloads') {
      renderDownloadsManager();
    } else if (viewName === 'platforms') {
      loadPlatformsView();
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  document.querySelectorAll('.sidebar-item[data-view]').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      switchView(item.dataset.view);
    });
  });

  document.getElementById('logo-home').addEventListener('click', (e) => {
    e.preventDefault();
    switchView('home');
  });

  document.getElementById('btn-downloads-page-new').addEventListener('click', () => {
    switchView('home');
    heroUrlInput.focus();
  });

  // --- NOTIFICATIONS & TOASTS ---
  function showToast(message, icon = 'ri-information-line') {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<i class="${icon}"></i><span>${message}</span>`;
    document.getElementById('toast-container').appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function addNotification(text) {
    state.notifications.unshift({ id: Date.now(), text, time: "Just now" });
    updateNotificationsBadge();
  }

  function updateNotificationsBadge() {
    if (state.notifications.length > 0) {
      notiCountBadge.textContent = state.notifications.length;
      notiCountBadge.style.display = 'block';
    } else {
      notiCountBadge.style.display = 'none';
    }
  }

  btnNotifications.addEventListener('click', (e) => {
    e.stopPropagation();
    const isVisible = notificationsMenu.style.display === 'block';
    notificationsMenu.style.display = isVisible ? 'none' : 'block';
    renderNotificationsList();
  });

  document.addEventListener('click', (e) => {
    if (!notificationsMenu.contains(e.target) && e.target !== btnNotifications) {
      notificationsMenu.style.display = 'none';
    }
  });

  function renderNotificationsList() {
    if (state.notifications.length === 0) {
      notificationsList.innerHTML = `<div class="empty-noti">No new notifications</div>`;
      return;
    }
    notificationsList.innerHTML = state.notifications.map(n => `
      <div class="noti-item">
        <div>${n.text}</div>
        <div style="font-size: 10px; color: var(--yt-text-secondary); margin-top: 3px;">${n.time}</div>
      </div>
    `).join('');
  }

  btnClearNoti.addEventListener('click', () => {
    state.notifications = [];
    updateNotificationsBadge();
    renderNotificationsList();
  });

  // --- CLIPBOARD PASTE HELPERS ---
  async function pasteClipboardTo(inputElement) {
    try {
      if (navigator.clipboard && navigator.clipboard.readText) {
        const text = await navigator.clipboard.readText();
        if (text) {
          inputElement.value = text.trim();
          showToast("URL pasted from clipboard!", "ri-clipboard-check-line");
          return text.trim();
        }
      }
    } catch (err) {
      console.warn("Clipboard read not permitted or available:", err);
    }
    inputElement.focus();
    showToast("Please press Ctrl+V to paste link", "ri-keyboard-line");
    return "";
  }

  btnQuickPaste.addEventListener('click', async () => {
    await pasteClipboardTo(urlSearchInput);
    if (urlSearchInput.value) {
      handleExtraction(urlSearchInput.value);
    }
  });

  heroPasteBtn.addEventListener('click', async () => {
    await pasteClipboardTo(heroUrlInput);
  });

  urlSearchInput.addEventListener('input', () => {
    btnClearSearch.style.display = urlSearchInput.value ? 'flex' : 'none';
  });

  btnClearSearch.addEventListener('click', () => {
    urlSearchInput.value = '';
    btnClearSearch.style.display = 'none';
    urlSearchInput.focus();
  });

  // --- SEARCH & HERO FORM SUBMISSIONS ---
  searchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = urlSearchInput.value.trim();
    if (query) {
      handleExtraction(query);
    }
  });

  heroFetchBtn.addEventListener('click', () => {
    const url = heroUrlInput.value.trim();
    if (url) {
      handleExtraction(url);
    } else {
      showToast("Please paste a video link first", "ri-alert-line");
      heroUrlInput.focus();
    }
  });

  heroUrlInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const url = heroUrlInput.value.trim();
      if (url) handleExtraction(url);
    }
  });

  document.getElementById('btn-open-downloader-modal').addEventListener('click', () => {
    openModal();
    heroUrlInput.focus();
  });

  // Sample quick platform badges click
  document.querySelectorAll('.plat-tag').forEach(tag => {
    tag.addEventListener('click', () => {
      const sample = tag.dataset.sample;
      heroUrlInput.value = sample;
      handleExtraction(sample);
    });
  });

  // Platform Filter buttons in sidebar
  document.querySelectorAll('.platform-filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const plat = btn.dataset.platform;
      switchView('home');
      filterCategory(plat);
    });
  });

  // --- HOME FEED & CATEGORIES ---
  async function loadTrendingFeed(category = 'All') {
    videoFeedGrid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--yt-text-secondary);">
        <div class="spinner" style="margin: 0 auto 12px;"></div>
        Loading trending videos across platforms...
      </div>
    `;

    try {
      const res = await fetch(`/api/trending?category=${encodeURIComponent(category)}`);
      const data = await res.json();
      state.sampleVideos = data.items || [];
      renderVideoGrid(state.sampleVideos);
    } catch (err) {
      console.error("Failed to load trending:", err);
      videoFeedGrid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 40px;">Failed to load videos. Please try again.</div>`;
    }
  }

  function renderVideoGrid(videos) {
    if (!videos || videos.length === 0) {
      videoFeedGrid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--yt-text-secondary);">No videos found for this category.</div>`;
      return;
    }

    videoFeedGrid.innerHTML = videos.map(v => {
      const platIcon = getPlatformIconClass(v.platform_icon || v.platform);
      return `
        <div class="video-card" data-id="${v.id}" data-url="${v.url || ''}">
          <div class="thumbnail-wrap">
            <img src="${v.thumbnail}" alt="${v.title}" class="thumbnail-img" loading="lazy">
            <span class="duration-badge">${v.duration || '0:45'}</span>
            <span class="platform-badge">
              <i class="${platIcon}"></i> ${v.platform || 'Web'}
            </span>
            <div class="hover-actions-overlay">
              <button class="btn-card-action btn-card-watch" data-url="${v.url || ''}">
                <i class="ri-play-fill"></i> Watch
              </button>
              <button class="btn-card-action btn-card-dl" data-url="${v.url || ''}">
                <i class="ri-download-line"></i> Download
              </button>
            </div>
          </div>
          <div class="video-meta-row">
            <img src="${v.uploader_avatar || 'https://api.dicebear.com/7.x/identicon/svg?seed=' + v.uploader}" alt="Avatar" class="channel-thumb">
            <div class="video-details">
              <h3 class="video-title" title="${v.title}">${v.title}</h3>
              <div class="channel-name">
                <span>${v.uploader || 'Creator'}</span>
                <i class="ri-checkbox-circle-fill verified-badge" style="${v.channel_verified ? '' : 'display:none;'}"></i>
              </div>
              <div class="video-stats">${v.views || '1.2M views'} • ${v.time_ago || 'Recent'}</div>
            </div>
          </div>
        </div>
      `;
    }).join('');

    // Attach click listeners to cards
    document.querySelectorAll('.video-card').forEach(card => {
      const url = card.dataset.url;
      const id = card.dataset.id;
      const videoData = state.sampleVideos.find(x => x.id === id);

      card.querySelector('.thumbnail-wrap').addEventListener('click', (e) => {
        if (!e.target.closest('.btn-card-dl')) {
          if (videoData) {
            playInWatchView(videoData);
          } else if (url) {
            handleExtraction(url);
          }
        }
      });

      const dlBtn = card.querySelector('.btn-card-dl');
      if (dlBtn) {
        dlBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          handleExtraction(url);
        });
      }
    });
  }

  function getPlatformIconClass(plat) {
    const p = (plat || '').toLowerCase();
    if (p.includes('youtube')) return 'ri-youtube-fill';
    if (p.includes('instagram')) return 'ri-instagram-fill';
    if (p.includes('facebook')) return 'ri-facebook-circle-fill';
    if (p.includes('twitter') || p.includes('x')) return 'ri-twitter-x-fill';
    if (p.includes('pinterest')) return 'ri-pinterest-fill';
    if (p.includes('terabox')) return 'ri-cloud-fill';
    if (p.includes('tiktok')) return 'ri-tiktok-fill';
    if (p.includes('reddit')) return 'ri-reddit-fill';
    return 'ri-movie-fill';
  }

  // Filter chips click handler
  categoryChips.forEach(chip => {
    chip.addEventListener('click', () => {
      categoryChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      const cat = chip.dataset.category;
      state.currentCategory = cat;
      loadTrendingFeed(cat);
    });
  });

  function filterCategory(categoryName) {
    categoryChips.forEach(c => {
      if (c.dataset.category.toLowerCase().includes(categoryName.toLowerCase())) {
        c.classList.add('active');
      } else {
        c.classList.remove('active');
      }
    });
    loadTrendingFeed(categoryName);
  }

  // --- LINK EXTRACTION & DOWNLOAD MODAL ---
  async function handleExtraction(url) {
    if (!url) return;
    openModal();
    setModalLoading();

    try {
      const resp = await fetch('/api/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const data = await resp.json();

      if (!data.success && data.error) {
        setModalError(data.error, data.is_bot_error || false);
        return;
      }

      state.activeVideo = data;
      renderModalDetails(data);
    } catch (err) {
      console.error("Extraction error:", err);
      setModalError("Failed to communicate with video engine. Check your connection.");
    }
  }

  function openModal() {
    downloadModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    progressBox.style.display = 'none';
  }

  function closeModal() {
    downloadModal.style.display = 'none';
    document.body.style.overflow = 'auto';
    if (state.pollTimer) {
      clearInterval(state.pollTimer);
      state.pollTimer = null;
    }
  }

  modalCloseBtn.addEventListener('click', closeModal);
  downloadModal.addEventListener('click', (e) => {
    if (e.target === downloadModal) closeModal();
  });

  function setModalLoading() {
    modalLoader.style.display = 'flex';
    modalError.style.display = 'none';
    modalDetails.style.display = 'none';
  }

  function setModalError(msg, isBotError = false) {
    modalLoader.style.display = 'none';
    modalError.style.display = 'block';
    modalDetails.style.display = 'none';
    modalErrorMsg.textContent = msg;
    const btnFix = document.getElementById('btn-fix-bot-modal');
    if (btnFix) {
      btnFix.style.display = isBotError ? 'inline-flex' : 'none';
    }
  }

  const btnFixBotModal = document.getElementById('btn-fix-bot-modal');
  if (btnFixBotModal) {
    btnFixBotModal.addEventListener('click', () => {
      closeModal();
      openAntiBotModal();
    });
  }

  document.getElementById('btn-modal-retry').addEventListener('click', () => {
    if (state.activeVideo && state.activeVideo.url) {
      handleExtraction(state.activeVideo.url);
    } else if (heroUrlInput.value) {
      handleExtraction(heroUrlInput.value);
    }
  });

  function renderModalDetails(data) {
    modalLoader.style.display = 'none';
    modalError.style.display = 'none';
    modalDetails.style.display = 'block';

    modalThumb.src = data.thumbnail || 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800';
    modalDuration.textContent = data.duration_formatted || '0:00';
    modalPlatformBadge.textContent = data.platform || 'Media';
    modalTitle.textContent = data.title || 'Video';
    modalUploader.textContent = data.uploader || 'Creator';
    modalViews.textContent = (data.views || '0') + ' views';
    modalLikes.textContent = (data.likes || '--') + ' likes';

    // Render Video Formats
    const vFormats = data.video_formats || [];
    if (vFormats.length > 0) {
      videoFormatsList.innerHTML = vFormats.map(vf => `
        <div class="format-row">
          <div class="format-info-left">
            <span class="res-badge">${vf.resolution || 'HD'}</span>
            <div>
              <div class="format-title">${vf.resolution || 'MP4 Video'}</div>
              <div class="format-ext-size">MP4 • ${vf.filesize_formatted || 'High Quality'}</div>
            </div>
          </div>
          <button class="btn-download-format" data-format="${vf.format_id}" data-audio="false" data-title="${encodeURIComponent(data.title)}">
            <i class="ri-download-line"></i> Download
          </button>
        </div>
      `).join('');
    } else {
      videoFormatsList.innerHTML = `<p style="color:var(--yt-text-secondary); padding: 10px;">Best quality video will be downloaded automatically.</p>`;
    }

    // Render Audio Formats
    const aFormats = data.audio_formats || [];
    if (aFormats.length > 0) {
      audioFormatsList.innerHTML = aFormats.map(af => `
        <div class="format-row">
          <div class="format-info-left">
            <span class="res-badge" style="color: #ff9800; background: rgba(255, 152, 0, 0.15);">MP3</span>
            <div>
              <div class="format-title">${af.quality || 'MP3 Audio'}</div>
              <div class="format-ext-size">MP3 Audio • ${af.filesize_formatted || 'High Bitrate'}</div>
            </div>
          </div>
          <button class="btn-download-format" data-format="${af.format_id}" data-audio="true" data-title="${encodeURIComponent(data.title)}">
            <i class="ri-music-line"></i> Download MP3
          </button>
        </div>
      `).join('');
    }

    // Attach Download buttons event listeners
    document.querySelectorAll('.btn-download-format').forEach(btn => {
      btn.addEventListener('click', () => {
        const formatId = btn.dataset.format;
        const isAudio = btn.dataset.audio === 'true';
        const title = decodeURIComponent(btn.dataset.title);
        startDownloadTask(data.url, formatId, isAudio, title);
      });
    });

    btnModalWatch.onclick = () => {
      closeModal();
      playInWatchView(data);
    };
  }

  // Format Tabs Toggle
  formatTabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      formatTabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const tab = btn.dataset.tab;
      if (tab === 'video') {
        tabVideoFormats.classList.add('active');
        tabAudioFormats.classList.remove('active');
      } else {
        tabAudioFormats.classList.add('active');
        tabVideoFormats.classList.remove('active');
      }
    });
  });

  // --- DOWNLOAD TASK EXECUTION & LIVE PROGRESS ---
  async function startDownloadTask(url, formatId, isAudio, title) {
    progressBox.style.display = 'block';
    progressStatusLabel.textContent = `Starting ${isAudio ? 'MP3 Audio' : 'Video'} conversion...`;
    progressPercent.textContent = '0%';
    progressBarFill.style.width = '0%';
    progressSpeed.textContent = 'Speed: Connecting...';
    progressEta.textContent = 'ETA: --';
    progressCompleteActions.style.display = 'none';

    try {
      const resp = await fetch('/api/download/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          format_id: formatId,
          is_audio: isAudio,
          title
        })
      });
      const data = await resp.json();
      if (data.job_id) {
        state.activeDownloadJob = data.job_id;
        showToast("Download started in background!", "ri-download-cloud-line");
        addNotification(`Started download: ${title.substring(0, 30)}...`);
        pollJobProgress(data.job_id, isAudio, title);
      }
    } catch (err) {
      console.error("Start download task error:", err);
      progressStatusLabel.textContent = "Error initiating download.";
    }
  }

  function pollJobProgress(jobId, isAudio, title) {
    if (state.pollTimer) clearInterval(state.pollTimer);

    state.pollTimer = setInterval(async () => {
      try {
        const resp = await fetch(`/api/download/status/${jobId}`);
        if (!resp.ok) return;
        const job = await resp.json();

        if (job.status === 'downloading') {
          const p = job.progress || 0;
          progressPercent.textContent = `${p}%`;
          progressBarFill.style.width = `${p}%`;
          progressStatusLabel.textContent = `Downloading ${isAudio ? 'Audio' : 'Video'} (${job.downloaded_formatted || ''} / ${job.total_formatted || ''})...`;
          progressSpeed.textContent = `Speed: ${job.speed || '--'}`;
          progressEta.textContent = `ETA: ${job.eta || '--'}`;
        } else if (job.status === 'processing') {
          progressBarFill.style.width = '99%';
          progressPercent.textContent = '99%';
          progressStatusLabel.textContent = 'Merging video & high quality audio with FFmpeg...';
        } else if (job.status === 'completed') {
          clearInterval(state.pollTimer);
          state.pollTimer = null;
          progressBarFill.style.width = '100%';
          progressPercent.textContent = '100%';
          progressStatusLabel.textContent = '✅ Download & Conversion Complete!';
          progressSpeed.textContent = `File Size: ${job.file_size_formatted || ''}`;
          progressEta.textContent = 'Status: Ready to Save';

          btnSaveDisk.href = job.download_url;
          btnSaveDisk.download = job.file_name || 'video.mp4';
          progressCompleteActions.style.display = 'flex';

          showToast("Download Complete! Click 'Save to Computer'", "ri-checkbox-circle-fill");
          addNotification(`Completed: ${title.substring(0, 30)} (${job.file_size_formatted || ''})`);

          // Record in download history
          saveToDownloadsHistory({
            id: jobId,
            title: title,
            fileName: job.file_name,
            fileSize: job.file_size_formatted,
            downloadUrl: job.download_url,
            isAudio: isAudio,
            platform: job.platform || 'Media',
            date: new Date().toLocaleDateString()
          });

          // Trigger automatic browser file download
          const triggerLink = document.createElement('a');
          triggerLink.href = job.download_url;
          triggerLink.download = job.file_name || 'download';
          document.body.appendChild(triggerLink);
          triggerLink.click();
          triggerLink.remove();
        } else if (job.status === 'error') {
          clearInterval(state.pollTimer);
          state.pollTimer = null;
          progressStatusLabel.textContent = `Error: ${job.error || 'Download failed'}`;
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 800);
  }

  function saveToDownloadsHistory(item) {
    state.downloads.unshift(item);
    if (state.downloads.length > 50) state.downloads.pop();
    localStorage.setItem('vidtube_downloads', JSON.stringify(state.downloads));
    updateDownloadsBadge();
  }

  function updateDownloadsBadge() {
    if (state.downloads.length > 0) {
      activeDlBadge.textContent = state.downloads.length;
      activeDlBadge.style.display = 'inline-block';
    } else {
      activeDlBadge.style.display = 'none';
    }
  }
  updateDownloadsBadge();

  // --- WATCH PAGE CONTROLLER ---
  function playInWatchView(videoData) {
    switchView('watch');
    state.activeVideo = videoData;

    // Platform tag
    watchPlatformTag.innerHTML = `
      <i class="${getPlatformIconClass(videoData.platform_icon || videoData.platform)}"></i>
      ${videoData.platform || 'YouTube'}
    `;

    // Title & channel
    watchTitle.textContent = videoData.title || 'Untitled Video';
    watchChannelName.textContent = videoData.uploader || 'Creator Channel';
    watchChannelAvatar.src = videoData.channel_avatar || `https://api.dicebear.com/7.x/identicon/svg?seed=${videoData.uploader || 'user'}`;
    watchChannelSubs.textContent = "1.82M subscribers";
    watchLikes.textContent = videoData.likes || "142K";
    watchViewsCount.textContent = (videoData.views || "1.2M") + " views";
    watchUploadDate.textContent = videoData.upload_date || "Oct 2, 2026";
    watchDescText.textContent = videoData.description || `Enjoy this full high-definition video from ${videoData.uploader || 'Creator'}.\nStreamed with VidTube Universal Media Engine.\nSupports downloading directly to device with audio and video stream merging.`;

    // Reset like button
    btnLike.querySelector('i').className = 'ri-thumb-up-line';

    // Video Player Setup
    if (videoData.stream_url) {
      videoPlayer.src = videoData.stream_url;
      videoPlayer.load();
      videoPlayer.play().catch(e => console.log("Autoplay was prevented:", e));
    } else {
      // Use fallback stream or sample
      videoPlayer.src = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4";
      videoPlayer.load();
      videoPlayer.play().catch(e => console.log("Autoplay note:", e));
    }

    // Load related recommendations
    renderRelatedVideos(videoData);

    // Load default realistic comments
    renderComments([
      { author: "Alex Chen", time: "2 hours ago", text: "The quality on this downloader is insane! Finally 1080p without any ads or watermarks.", likes: 142 },
      { author: "Elena Rostova", time: "5 hours ago", text: "Terabox links always gave me headaches, this tool resolved my cloud file in seconds! 🔥", likes: 89 },
      { author: "DevMarcus", time: "1 day ago", text: "The YouTube watch page interface feels so native. Cleanest UI I've seen in a while.", likes: 31 }
    ]);
  }

  // Subscribe button toggle
  btnSubscribe.addEventListener('click', () => {
    const isSubbed = btnSubscribe.classList.contains('subscribed');
    if (isSubbed) {
      btnSubscribe.classList.remove('subscribed');
      btnSubscribe.textContent = 'Subscribe';
      showToast("Unsubscribed from channel");
    } else {
      btnSubscribe.classList.add('subscribed');
      btnSubscribe.textContent = 'Subscribed ✓';
      showToast("Subscribed to channel!", "ri-notification-3-line");
    }
  });

  // Like / Dislike toggle
  btnLike.addEventListener('click', () => {
    const icon = btnLike.querySelector('i');
    if (icon.classList.contains('ri-thumb-up-fill')) {
      icon.className = 'ri-thumb-up-line';
    } else {
      icon.className = 'ri-thumb-up-fill';
      btnDislike.querySelector('i').className = 'ri-thumb-down-line';
      showToast("Added to Liked Videos", "ri-thumb-up-fill");
    }
  });

  btnDislike.addEventListener('click', () => {
    const icon = btnDislike.querySelector('i');
    if (icon.classList.contains('ri-thumb-down-fill')) {
      icon.className = 'ri-thumb-down-line';
    } else {
      icon.className = 'ri-thumb-down-fill';
      btnLike.querySelector('i').className = 'ri-thumb-up-line';
    }
  });

  // Share button
  btnShare.addEventListener('click', () => {
    const url = (state.activeVideo && state.activeVideo.url) ? state.activeVideo.url : window.location.href;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url);
      showToast("Video link copied to clipboard!", "ri-file-copy-line");
    } else {
      showToast(`Share URL: ${url}`);
    }
  });

  // Prominent Download button on watch page
  btnWatchDownload.addEventListener('click', () => {
    if (state.activeVideo) {
      if (state.activeVideo.video_formats) {
        openModal();
        renderModalDetails(state.activeVideo);
      } else {
        handleExtraction(state.activeVideo.url);
      }
    }
  });

  // Description expand toggle
  btnToggleDesc.addEventListener('click', () => {
    descBox.classList.toggle('expanded');
    btnToggleDesc.textContent = descBox.classList.contains('expanded') ? 'Show less' : 'Show more';
  });

  // Comments interaction
  newCommentInput.addEventListener('focus', () => {
    commentActionsBar.style.display = 'flex';
  });

  btnCancelComment.addEventListener('click', () => {
    newCommentInput.value = '';
    commentActionsBar.style.display = 'none';
  });

  btnSubmitComment.addEventListener('click', () => {
    const text = newCommentInput.value.trim();
    if (!text) return;

    const newComment = {
      author: "You",
      time: "Just now",
      text: text,
      likes: 0
    };

    const currentList = Array.from(document.querySelectorAll('.comment-card')).map(card => ({
      author: card.querySelector('.comment-author').textContent,
      time: card.querySelector('.comment-time').textContent,
      text: card.querySelector('.comment-text').textContent,
      likes: parseInt(card.querySelector('.comment-likes-count').textContent) || 0
    }));

    currentList.unshift(newComment);
    renderComments(currentList);
    newCommentInput.value = '';
    commentActionsBar.style.display = 'none';
    showToast("Comment posted!");
  });

  function renderComments(comments) {
    commentsCountTitle.textContent = `${comments.length + 342} Comments`;
    commentsList.innerHTML = comments.map(c => `
      <div class="comment-card">
        <img src="https://api.dicebear.com/7.x/identicon/svg?seed=${encodeURIComponent(c.author)}" alt="Avatar" class="comment-avatar">
        <div>
          <div>
            <span class="comment-author">${c.author}</span>
            <span class="comment-time">${c.time}</span>
          </div>
          <p class="comment-text">${c.text}</p>
          <div class="comment-actions-row">
            <button class="comment-like-btn">
              <i class="ri-thumb-up-line"></i>
              <span class="comment-likes-count">${c.likes || ''}</span>
            </button>
            <button><i class="ri-thumb-down-line"></i></button>
            <button style="font-weight: 600; font-size: 11px;">Reply</button>
          </div>
        </div>
      </div>
    `).join('');
  }

  function renderRelatedVideos(currentVideo) {
    const related = state.sampleVideos.filter(v => v.id !== currentVideo.id);
    relatedVideosList.innerHTML = related.map(v => `
      <div class="related-card" data-url="${v.url || ''}" data-id="${v.id}">
        <div class="related-thumb-wrap">
          <img src="${v.thumbnail}" alt="${v.title}">
          <span class="duration-badge">${v.duration || '0:45'}</span>
        </div>
        <div class="related-meta">
          <h4 class="related-title">${v.title}</h4>
          <div class="related-channel">${v.uploader || 'Creator'}</div>
          <div class="related-stats">${v.views || '1M views'}</div>
        </div>
      </div>
    `).join('');

    document.querySelectorAll('.related-card').forEach(card => {
      card.addEventListener('click', () => {
        const id = card.dataset.id;
        const video = state.sampleVideos.find(v => v.id === id);
        if (video) playInWatchView(video);
      });
    });
  }

  // --- SHORTS / REELS PLAYER ---
  const reelVideo = document.querySelector('.reel-video');
  const reelPlayBtn = document.querySelector('.reel-play-btn');
  const reelDlBtn = document.querySelector('.reel-download-btn');

  if (reelVideo) {
    reelVideo.addEventListener('click', () => {
      if (reelVideo.paused) {
        reelVideo.play();
        reelPlayBtn.style.display = 'none';
      } else {
        reelVideo.pause();
        reelPlayBtn.style.display = 'flex';
      }
    });

    reelDlBtn.addEventListener('click', () => {
      handleExtraction("https://www.instagram.com/reel/C_example_shinjuku/");
    });
  }

  // --- DOWNLOADS MANAGER VIEW ---
  function renderDownloadsManager() {
    if (state.downloads.length === 0) {
      downloadsEmpty.style.display = 'block';
      downloadsTasksList.innerHTML = '';
      return;
    }

    downloadsEmpty.style.display = 'none';
    downloadsTasksList.innerHTML = state.downloads.map(item => `
      <div class="download-task-item">
        <div class="task-left">
          <div class="task-icon">
            <i class="${item.isAudio ? 'ri-music-2-line' : 'ri-video-line'}"></i>
          </div>
          <div>
            <div class="task-title">${item.title}</div>
            <div class="task-sub">${item.fileName || 'Media File'} • ${item.fileSize || 'Standard'} • ${item.platform} • ${item.date}</div>
          </div>
        </div>
        <div class="task-actions">
          <a href="${item.downloadUrl}" class="btn-task-action primary" download>
            <i class="ri-download-2-line"></i> Save
          </a>
        </div>
      </div>
    `).join('');
  }

  // --- SUPPORTED PLATFORMS VIEW ---
  async function loadPlatformsView() {
    try {
      const resp = await fetch('/api/platforms');
      const data = await resp.json();
      const platforms = data.platforms || [];

      platformsGrid.innerHTML = platforms.map(p => `
        <div class="platform-card">
          <div class="plat-card-header">
            <div class="plat-card-title">
              <i class="${getPlatformIconClass(p.icon)}"></i>
              <span>${p.name}</span>
            </div>
            <span class="plat-pill">${p.badge}</span>
          </div>
          <p class="plat-card-desc">${p.description}</p>
          <div class="plat-card-formats">
            ${p.formats.map(f => `<span class="format-chip-mini">${f}</span>`).join('')}
          </div>
          <button class="btn-plat-try" data-sample="${p.sample}">
            <i class="ri-flashlight-line"></i> Test / Download Sample
          </button>
        </div>
      `).join('');

      document.querySelectorAll('.btn-plat-try').forEach(btn => {
        btn.addEventListener('click', () => {
          const sample = btn.dataset.sample;
          handleExtraction(sample);
        });
      });
    } catch (err) {
      console.error("Platforms fetch error:", err);
    }
  }

  // --- ANTI-BOT & COOKIE SETTINGS CONTROLLER ---
  const antiBotModal = document.getElementById('anti-bot-modal');
  const btnOpenAntiBot = document.getElementById('btn-open-anti-bot');
  const antiBotCloseBtn = document.getElementById('anti-bot-close-btn');
  const cookieStatusDot = document.getElementById('cookie-status-dot');
  const antiBotStatusTag = document.getElementById('anti-bot-status-tag');
  const cookiesTextarea = document.getElementById('cookies-textarea');
  const cookieFileInput = document.getElementById('cookie-file-input');
  const btnTriggerCookieFile = document.getElementById('btn-trigger-cookie-file');
  const btnSaveCookies = document.getElementById('btn-save-cookies');
  const btnClearCookies = document.getElementById('btn-clear-cookies');

  function openAntiBotModal() {
    antiBotModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    checkCookieStatus();
  }

  function closeAntiBotModal() {
    antiBotModal.style.display = 'none';
    document.body.style.overflow = 'auto';
  }

  if (btnOpenAntiBot) btnOpenAntiBot.addEventListener('click', openAntiBotModal);
  if (antiBotCloseBtn) antiBotCloseBtn.addEventListener('click', closeAntiBotModal);
  if (antiBotModal) {
    antiBotModal.addEventListener('click', (e) => {
      if (e.target === antiBotModal) closeAntiBotModal();
    });
  }

  async function checkCookieStatus() {
    try {
      const resp = await fetch('/api/cookies/status');
      const data = await resp.json();
      if (data.has_cookies) {
        if (cookieStatusDot) cookieStatusDot.className = 'bot-dot active';
        if (antiBotStatusTag) {
          antiBotStatusTag.className = 'bot-status-tag active';
          antiBotStatusTag.textContent = `Active (${data.cookie_count} cookies loaded)`;
        }
      } else {
        if (cookieStatusDot) cookieStatusDot.className = 'bot-dot';
        if (antiBotStatusTag) {
          antiBotStatusTag.className = 'bot-status-tag';
          antiBotStatusTag.textContent = 'Mobile Client Bypass Active (No custom cookies)';
        }
      }
    } catch (err) {
      console.error("Cookie status error:", err);
    }
  }

  if (btnTriggerCookieFile) {
    btnTriggerCookieFile.addEventListener('click', () => {
      cookieFileInput.click();
    });
  }

  if (cookieFileInput) {
    cookieFileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (event) => {
        cookiesTextarea.value = event.target.result;
        showToast("cookies.txt loaded into text area!", "ri-file-text-line");
      };
      reader.readAsText(file);
    });
  }

  if (btnSaveCookies) {
    btnSaveCookies.addEventListener('click', async () => {
      const text = cookiesTextarea.value.trim();
      if (!text) {
        showToast("Please paste your cookies text first", "ri-alert-line");
        return;
      }
      try {
        const resp = await fetch('/api/cookies/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cookies_text: text })
        });
        const data = await resp.json();
        if (data.success) {
          showToast(`Successfully saved & activated ${data.cookie_count} cookies!`, "ri-checkbox-circle-fill");
          checkCookieStatus();
          setTimeout(closeAntiBotModal, 1200);
        } else {
          showToast("Failed to save cookies", "ri-error-warning-line");
        }
      } catch (err) {
        console.error("Save cookies error:", err);
        showToast("Network error saving cookies", "ri-error-warning-line");
      }
    });
  }

  if (btnClearCookies) {
    btnClearCookies.addEventListener('click', async () => {
      try {
        await fetch('/api/cookies/clear', { method: 'POST' });
        cookiesTextarea.value = '';
        showToast("Cookies cleared. Reverted to Mobile Client bypass.", "ri-delete-bin-line");
        checkCookieStatus();
      } catch (err) {
        console.error("Clear cookies error:", err);
      }
    });
  }

  // --- PROXY HANDLERS ---
  const proxyInput = document.getElementById('proxy-input');
  const btnSaveProxy = document.getElementById('btn-save-proxy');
  const btnClearProxy = document.getElementById('btn-clear-proxy');
  const proxyStatusBadge = document.getElementById('proxy-status-badge');

  async function checkProxyStatus() {
    try {
      const resp = await fetch('/api/proxy/status');
      const data = await resp.json();
      if (data.has_proxy) {
        proxyInput.value = data.proxy || '';
        proxyStatusBadge.textContent = `Active (${data.source})`;
        proxyStatusBadge.style.color = '#4caf50';
      } else {
        proxyInput.value = '';
        proxyStatusBadge.textContent = 'No proxy';
        proxyStatusBadge.style.color = 'var(--yt-text-secondary)';
      }
    } catch (err) {
      console.error("Proxy status check error:", err);
    }
  }

  if (btnSaveProxy) {
    btnSaveProxy.addEventListener('click', async () => {
      const p = proxyInput.value.trim();
      if (!p) {
        showToast("Please enter a proxy URL", "ri-alert-line");
        return;
      }
      try {
        const resp = await fetch('/api/proxy/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ proxy_url: p })
        });
        const data = await resp.json();
        if (data.success) {
          showToast("Proxy saved & activated successfully!", "ri-checkbox-circle-fill");
          checkProxyStatus();
        }
      } catch (err) {
        console.error("Save proxy error:", err);
        showToast("Error saving proxy", "ri-error-warning-line");
      }
    });
  }

  if (btnClearProxy) {
    btnClearProxy.addEventListener('click', async () => {
      try {
        await fetch('/api/proxy/clear', { method: 'POST' });
        proxyInput.value = '';
        showToast("Proxy removed.", "ri-delete-bin-line");
        checkProxyStatus();
      } catch (err) {
        console.error("Clear proxy error:", err);
      }
    });
  }

  // Check cookie and proxy status on boot
  checkCookieStatus();
  checkProxyStatus();

  // --- INITIALIZE APPLICATION ---
  loadTrendingFeed('All');
});

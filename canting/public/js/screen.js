(function () {
  const shell = document.getElementById('screen-shell');
  const promoStage = document.getElementById('promo-stage');
  const promoDots = document.getElementById('promo-dots');
  const recommendedGrid = document.getElementById('recommended-grid');
  const menuPages = document.getElementById('menu-pages');
  const menuDots = document.getElementById('menu-dots');
  const categoryList = document.getElementById('category-list');
  const announcement = document.getElementById('announcement');
  const updatedAt = document.getElementById('updated-at');
  const clockText = document.getElementById('clock-text');
  const restaurantName = document.getElementById('restaurant-name');
  const restaurantSlogan = document.getElementById('restaurant-slogan');
  const promoTitle = document.getElementById('promo-title');
  const recommendedTitle = document.getElementById('recommended-title');
  const boardTitle = document.getElementById('board-title');

  const state = {
    data: window.__SCREEN_DATA__ || null,
    intervals: [],
    refreshTimer: null,
    clockTimer: null
  };

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function chunk(items, size) {
    const chunks = [];
    for (let index = 0; index < items.length; index += size) {
      chunks.push(items.slice(index, index + size));
    }
    return chunks;
  }

  function money(value) {
    const symbol = state.data?.settings?.currencySymbol || '￥';
    const amount = Number(value) || 0;
    return `${symbol}${amount.toFixed(2)}`;
  }

  function formatUpdatedAt(value) {
    if (!value) {
      return '--';
    }

    return new Date(value).toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function renderDots(container, count, activeIndex) {
    container.innerHTML = '';
    for (let index = 0; index < count; index += 1) {
      const dot = document.createElement('span');
      if (index === activeIndex) {
        dot.classList.add('is-active');
      }
      container.appendChild(dot);
    }
  }

  function clearIntervals() {
    state.intervals.forEach((timer) => window.clearInterval(timer));
    state.intervals = [];
  }

  function setupCarousel(items, dotsElement, intervalMs) {
    if (items.length === 0) {
      dotsElement.innerHTML = '';
      return;
    }

    let activeIndex = 0;

    const paint = () => {
      items.forEach((item, index) => {
        item.classList.toggle('is-active', index === activeIndex);
      });
      renderDots(dotsElement, items.length, activeIndex);
    };

    paint();

    if (items.length > 1) {
      const timer = window.setInterval(() => {
        activeIndex = (activeIndex + 1) % items.length;
        paint();
      }, intervalMs);
      state.intervals.push(timer);
    }
  }

  function buildPromoCard(item) {
    const imageMarkup = item.image
      ? `<div class="promo-media"><img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.title)}"></div>`
      : `
        <div class="promo-media">
          <div class="promo-media__fallback">
            <p class="chip">${escapeHtml(item.badge || '活动推荐')}</p>
            <strong>${escapeHtml(item.title)}</strong>
            <p>${escapeHtml(item.subtitle || '限时特惠')}</p>
          </div>
        </div>
      `;

    return `
      <article class="promo-card">
        ${imageMarkup}
        <div class="promo-content">
          <span class="chip">${escapeHtml(item.badge || '活动推荐')}</span>
          <h3>${escapeHtml(item.title)}</h3>
          <p>${escapeHtml(item.subtitle || '欢迎到店选购')}</p>
          <p>${escapeHtml(item.description || '后台可编辑该活动的说明、套餐内容和优惠力度。')}</p>
        </div>
      </article>
    `;
  }

  function buildRecommendedCard(item) {
    return `
      <article class="recommended-card">
        <div class="recommended-card__visual">
          ${item.image ? `<img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.name)}">` : ''}
        </div>
        <div class="recommended-card__body">
          <h3>${escapeHtml(item.name)}</h3>
          <p>${escapeHtml(item.description || '招牌推荐，欢迎点单。')}</p>
          <div class="price-badge">
            <div>
              <p class="price-badge__label">${escapeHtml(item.category?.name || '推荐菜')}</p>
              <strong class="price-badge__current">${money(item.price)}</strong>
            </div>
            ${
              item.originalPrice > 0
                ? `<span class="price-badge__origin">${money(item.originalPrice)}</span>`
                : ''
            }
          </div>
        </div>
      </article>
    `;
  }

  function buildDishCard(item) {
    const tags = Array.isArray(item.tags) ? item.tags : [];
    const spicyText = Number(item.spicyLevel) > 0 ? `辣度 ${'★'.repeat(Number(item.spicyLevel))}` : '不辣';

    return `
      <article class="dish-card">
        <div class="dish-card__media">
          ${item.image ? `<img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.name)}">` : ''}
        </div>
        <div class="dish-card__body">
          <div>
            <h3>${escapeHtml(item.name)}</h3>
            <p>${escapeHtml(item.description || '欢迎到店点单。')}</p>
          </div>
          <div class="dish-card__meta">
            <span class="tag">${escapeHtml(item.category?.name || '未分类')}</span>
            <span class="tag">${escapeHtml(spicyText)}</span>
            ${tags.slice(0, 3).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
          </div>
          <div class="dish-card__footer">
            <span class="dish-card__category">${escapeHtml(item.recommended ? '推荐菜' : '门店热销')}</span>
            <strong class="dish-card__price">${money(item.price)}</strong>
          </div>
        </div>
      </article>
    `;
  }

  function renderPromotions(data) {
    const promotions = data.promotions || [];
    if (!promotions.length) {
      promoStage.innerHTML = '<div class="empty-state">后台还没有启用优惠活动。</div>';
      promoDots.innerHTML = '';
      return;
    }

    promoStage.innerHTML = promotions.map(buildPromoCard).join('');
    setupCarousel(Array.from(promoStage.querySelectorAll('.promo-card')), promoDots, data.settings.rotationSeconds * 1000);
  }

  function renderRecommended(data) {
    const items = (data.recommendedDishes || []).slice(0, 4);
    if (!items.length) {
      recommendedGrid.innerHTML = '<div class="empty-state">还没有推荐菜，请先在后台标记推荐菜品。</div>';
      return;
    }

    recommendedGrid.innerHTML = items.map(buildRecommendedCard).join('');
  }

  function renderMenu(data) {
    const dishes = data.dishes || [];
    if (!dishes.length) {
      menuPages.innerHTML = '<div class="empty-state">暂无上架菜品。</div>';
      menuDots.innerHTML = '';
      return;
    }

    const pages = chunk(dishes, 6);
    menuPages.innerHTML = pages
      .map((page) => `<section class="menu-page">${page.map(buildDishCard).join('')}</section>`)
      .join('');

    setupCarousel(
      Array.from(menuPages.querySelectorAll('.menu-page')),
      menuDots,
      data.settings.rotationSeconds * 1000
    );
  }

  function renderCategories(data) {
    const categories = data.categories || [];
    if (!categories.length) {
      categoryList.innerHTML = '<div class="empty-state">暂无分类，请在后台创建。</div>';
      return;
    }

    categoryList.innerHTML = categories
      .map(
        (item) => `
          <article class="category-item" style="--item-color:${escapeHtml(item.color || '#fbbf24')}">
            <div class="category-item__header">
              <strong>${escapeHtml(item.name)}</strong>
              <span class="category-item__count">${Number(item.dishCount) || 0} 道菜</span>
            </div>
            <p>${escapeHtml(item.description || '欢迎查看本档口热卖产品。')}</p>
          </article>
        `
      )
      .join('');
  }

  function updateClock() {
    clockText.textContent = new Date().toLocaleString('zh-CN', {
      weekday: 'short',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  function render(data) {
    if (!data) {
      return;
    }

    clearIntervals();
    state.data = data;

    document.title = `${data.settings.restaurantName} 展示屏`;
    shell.style.setProperty('--theme-color', data.settings.themeColor || '#c2410c');
    shell.style.setProperty('--accent-color', data.settings.accentColor || '#fbbf24');

    restaurantName.textContent = data.settings.restaurantName || '餐厅展示屏';
    restaurantSlogan.textContent = data.settings.slogan || '';
    promoTitle.textContent = data.settings.promoTitle || '今日优惠';
    recommendedTitle.textContent = data.settings.recommendedTitle || '招牌热卖';
    boardTitle.textContent = data.settings.boardTitle || '今日菜单';
    announcement.textContent = data.settings.announcement || '欢迎光临。';
    updatedAt.textContent = formatUpdatedAt(data.updatedAt);

    renderPromotions(data);
    renderRecommended(data);
    renderMenu(data);
    renderCategories(data);
  }

  async function refreshData() {
    try {
      const response = await fetch(`/api/screen?ts=${Date.now()}`, {
        cache: 'no-store'
      });
      if (!response.ok) {
        return;
      }

      const nextData = await response.json();
      if (nextData.updatedAt !== state.data?.updatedAt) {
        render(nextData);
      }
    } catch (_error) {
      // 网络短暂失败时保持当前画面
    }
  }

  function start() {
    render(state.data);
    updateClock();

    state.clockTimer = window.setInterval(updateClock, 1000);

    const refreshSeconds = Math.max(Number(state.data?.settings?.refreshSeconds) || 45, 15);
    state.refreshTimer = window.setInterval(refreshData, refreshSeconds * 1000);
  }

  start();
})();


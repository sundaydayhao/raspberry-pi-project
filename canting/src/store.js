const fs = require('fs');
const path = require('path');
const { randomUUID } = require('crypto');

const dataDir = path.join(__dirname, '..', 'data');
const storeFile = path.join(dataDir, 'store.json');

function now() {
  return new Date().toISOString();
}

function createId(prefix) {
  return `${prefix}_${randomUUID().slice(0, 8)}`;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function normalizeText(value, fallback = '') {
  const text = String(value ?? '').trim();
  return text || fallback;
}

function normalizeColor(value, fallback) {
  const color = String(value ?? '').trim();
  return /^#[0-9a-fA-F]{6}$/.test(color) ? color : fallback;
}

function toInt(value, fallback = 0) {
  const parsed = Number.parseInt(String(value ?? '').trim(), 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function toPrice(value, fallback = 0) {
  if (value === '' || value === null || value === undefined) {
    return fallback;
  }

  const parsed = Number.parseFloat(String(value).trim());
  if (!Number.isFinite(parsed) || parsed < 0) {
    return fallback;
  }

  return Number(parsed.toFixed(2));
}

function toBool(value) {
  return value === true || value === 'true' || value === 'on' || value === 1 || value === '1';
}

function parseTags(value) {
  return String(value ?? '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function sortByOrder(items, labelKey = 'name') {
  return [...items].sort((left, right) => {
    const orderDelta = (Number(left.sortOrder) || 0) - (Number(right.sortOrder) || 0);
    if (orderDelta !== 0) {
      return orderDelta;
    }

    return String(left[labelKey] || '').localeCompare(String(right[labelKey] || ''), 'zh-CN');
  });
}

function buildDefaultStore() {
  return {
    settings: {
      restaurantName: '食味小馆',
      slogan: '现炒现做 · 今日优选',
      announcement: '欢迎光临，请到收银台扫码点餐，优惠套餐限时供应。',
      currencySymbol: '￥',
      rotationSeconds: 10,
      refreshSeconds: 45,
      recommendedTitle: '招牌热卖',
      boardTitle: '今日菜单',
      promoTitle: '今日优惠',
      themeColor: '#c2410c',
      accentColor: '#fbbf24'
    },
    categories: [
      {
        id: 'cat_hot',
        name: '热菜现炒',
        description: '适合正餐，现点现做。',
        color: '#dc6b2f',
        sortOrder: 1
      },
      {
        id: 'cat_snack',
        name: '风味小吃',
        description: '高翻台爆款，适合加购。',
        color: '#0f766e',
        sortOrder: 2
      },
      {
        id: 'cat_drink',
        name: '饮品甜点',
        description: '堂食外带都方便。',
        color: '#7c3aed',
        sortOrder: 3
      }
    ],
    dishes: [
      {
        id: 'dish_1',
        categoryId: 'cat_hot',
        name: '招牌小炒黄牛肉',
        description: '鲜嫩牛肉搭配线椒爆炒，香气足、下饭快。',
        price: 38,
        originalPrice: 45,
        image: '',
        tags: ['招牌', '热卖', '下饭'],
        spicyLevel: 2,
        recommended: true,
        available: true,
        sortOrder: 1
      },
      {
        id: 'dish_2',
        categoryId: 'cat_hot',
        name: '金汤酸菜鱼',
        description: '金汤浓郁，鱼片滑嫩，适合多人共享。',
        price: 52,
        originalPrice: 0,
        image: '',
        tags: ['新品', '多人推荐'],
        spicyLevel: 1,
        recommended: true,
        available: true,
        sortOrder: 2
      },
      {
        id: 'dish_3',
        categoryId: 'cat_snack',
        name: '藤椒鸡排饭',
        description: '外酥里嫩，藤椒香气清爽不腻。',
        price: 24,
        originalPrice: 28,
        image: '',
        tags: ['套餐', '午市'],
        spicyLevel: 1,
        recommended: true,
        available: true,
        sortOrder: 3
      },
      {
        id: 'dish_4',
        categoryId: 'cat_drink',
        name: '鲜橙气泡饮',
        description: '鲜橙果香配气泡口感，适合搭配炸物。',
        price: 12,
        originalPrice: 15,
        image: '',
        tags: ['加购推荐'],
        spicyLevel: 0,
        recommended: false,
        available: true,
        sortOrder: 4
      }
    ],
    promotions: [
      {
        id: 'promo_1',
        title: '午市双人套餐',
        subtitle: '11:00 - 14:00 限时优惠',
        description: '任意热菜 2 份 + 米饭 2 份 + 饮品 2 杯，立减 16 元。',
        badge: '限时套餐',
        image: '',
        enabled: true,
        sortOrder: 1
      },
      {
        id: 'promo_2',
        title: '进店扫码立减',
        subtitle: '新客点单专享',
        description: '首次扫码下单满 39 元，自动减 8 元。',
        badge: '新客福利',
        image: '',
        enabled: true,
        sortOrder: 2
      }
    ],
    updatedAt: now()
  };
}

function withDefaults(source) {
  const defaults = buildDefaultStore();

  return {
    settings: {
      ...defaults.settings,
      ...(source.settings || {})
    },
    categories: Array.isArray(source.categories) ? source.categories : defaults.categories,
    dishes: Array.isArray(source.dishes) ? source.dishes : defaults.dishes,
    promotions: Array.isArray(source.promotions) ? source.promotions : defaults.promotions,
    updatedAt: source.updatedAt || defaults.updatedAt
  };
}

function writeStore(data) {
  const next = {
    ...data,
    updatedAt: now()
  };

  fs.mkdirSync(dataDir, { recursive: true });
  const tempFile = `${storeFile}.tmp`;
  fs.writeFileSync(tempFile, JSON.stringify(next, null, 2), 'utf8');
  fs.renameSync(tempFile, storeFile);
  return next;
}

function ensureStore() {
  fs.mkdirSync(dataDir, { recursive: true });
  if (!fs.existsSync(storeFile)) {
    writeStore(buildDefaultStore());
  }
}

function readStore() {
  ensureStore();
  const raw = fs.readFileSync(storeFile, 'utf8');
  return withDefaults(JSON.parse(raw || '{}'));
}

function getScreenData() {
  const store = readStore();
  const categories = sortByOrder(store.categories);
  const dishes = sortByOrder(store.dishes)
    .filter((item) => item.available)
    .map((dish) => ({
      ...dish,
      category: categories.find((category) => category.id === dish.categoryId) || null
    }));

  const promotions = sortByOrder(store.promotions, 'title').filter((item) => item.enabled);
  const recommendedDishes = dishes.filter((item) => item.recommended);

  return {
    settings: store.settings,
    categories: categories.map((category) => ({
      ...category,
      dishCount: dishes.filter((dish) => dish.categoryId === category.id).length
    })),
    dishes,
    promotions: promotions.length
      ? promotions
      : [
          {
            id: 'promo_fallback',
            title: store.settings.promoTitle,
            subtitle: '后台还没有开启优惠项',
            description: '可在后台新增活动海报、限时折扣、套餐推荐等内容。',
            badge: '待配置',
            image: '',
            enabled: true,
            sortOrder: 999
          }
        ],
    recommendedDishes: recommendedDishes.length ? recommendedDishes : dishes.slice(0, 4),
    updatedAt: store.updatedAt
  };
}

function upsertSettings(input) {
  const store = readStore();

  store.settings = {
    ...store.settings,
    restaurantName: normalizeText(input.restaurantName, '食味小馆'),
    slogan: normalizeText(input.slogan, '现炒现做 · 今日优选'),
    announcement: normalizeText(input.announcement, '欢迎光临，请到收银台扫码点餐。'),
    currencySymbol: normalizeText(input.currencySymbol, '￥'),
    rotationSeconds: clamp(toInt(input.rotationSeconds, 10), 5, 60),
    refreshSeconds: clamp(toInt(input.refreshSeconds, 45), 15, 300),
    recommendedTitle: normalizeText(input.recommendedTitle, '招牌热卖'),
    boardTitle: normalizeText(input.boardTitle, '今日菜单'),
    promoTitle: normalizeText(input.promoTitle, '今日优惠'),
    themeColor: normalizeColor(input.themeColor, '#c2410c'),
    accentColor: normalizeColor(input.accentColor, '#fbbf24')
  };

  return writeStore(store);
}

function upsertCategory(input) {
  const store = readStore();
  const id = normalizeText(input.id);

  const nextCategory = {
    id: id || createId('cat'),
    name: normalizeText(input.name),
    description: normalizeText(input.description),
    color: normalizeColor(input.color, '#c2410c'),
    sortOrder: toInt(input.sortOrder, 0)
  };

  if (!nextCategory.name) {
    throw new Error('分类名称不能为空。');
  }

  if (id) {
    const index = store.categories.findIndex((item) => item.id === id);
    if (index === -1) {
      throw new Error('要编辑的分类不存在。');
    }
    store.categories[index] = nextCategory;
  } else {
    store.categories.push(nextCategory);
  }

  return writeStore(store);
}

function deleteCategory(id) {
  const store = readStore();
  const inUse = store.dishes.some((dish) => dish.categoryId === id);
  if (inUse) {
    throw new Error('该分类下仍有菜品，不能直接删除。');
  }

  const nextCategories = store.categories.filter((item) => item.id !== id);
  if (nextCategories.length === store.categories.length) {
    throw new Error('要删除的分类不存在。');
  }

  store.categories = nextCategories;
  return writeStore(store);
}

function upsertDish(input) {
  const store = readStore();
  const id = normalizeText(input.id);
  const categoryId = normalizeText(input.categoryId);

  if (categoryId && !store.categories.some((item) => item.id === categoryId)) {
    throw new Error('菜品分类不存在，请先创建分类。');
  }

  const nextDish = {
    id: id || createId('dish'),
    categoryId,
    name: normalizeText(input.name),
    description: normalizeText(input.description),
    price: toPrice(input.price),
    originalPrice: toPrice(input.originalPrice),
    image: normalizeText(input.image),
    tags: parseTags(input.tags),
    spicyLevel: clamp(toInt(input.spicyLevel, 0), 0, 5),
    recommended: toBool(input.recommended),
    available: toBool(input.available),
    sortOrder: toInt(input.sortOrder, 0)
  };

  if (!nextDish.name) {
    throw new Error('菜品名称不能为空。');
  }

  if (!Number.isFinite(nextDish.price) || nextDish.price <= 0) {
    throw new Error('菜品价格必须大于 0。');
  }

  if (id) {
    const index = store.dishes.findIndex((item) => item.id === id);
    if (index === -1) {
      throw new Error('要编辑的菜品不存在。');
    }
    store.dishes[index] = nextDish;
  } else {
    store.dishes.push(nextDish);
  }

  return writeStore(store);
}

function deleteDish(id) {
  const store = readStore();
  const nextDishes = store.dishes.filter((item) => item.id !== id);
  if (nextDishes.length === store.dishes.length) {
    throw new Error('要删除的菜品不存在。');
  }

  store.dishes = nextDishes;
  return writeStore(store);
}

function upsertPromotion(input) {
  const store = readStore();
  const id = normalizeText(input.id);

  const nextPromotion = {
    id: id || createId('promo'),
    title: normalizeText(input.title),
    subtitle: normalizeText(input.subtitle),
    description: normalizeText(input.description),
    badge: normalizeText(input.badge, '活动推荐'),
    image: normalizeText(input.image),
    enabled: toBool(input.enabled),
    sortOrder: toInt(input.sortOrder, 0)
  };

  if (!nextPromotion.title) {
    throw new Error('优惠标题不能为空。');
  }

  if (id) {
    const index = store.promotions.findIndex((item) => item.id === id);
    if (index === -1) {
      throw new Error('要编辑的优惠不存在。');
    }
    store.promotions[index] = nextPromotion;
  } else {
    store.promotions.push(nextPromotion);
  }

  return writeStore(store);
}

function deletePromotion(id) {
  const store = readStore();
  const nextPromotions = store.promotions.filter((item) => item.id !== id);
  if (nextPromotions.length === store.promotions.length) {
    throw new Error('要删除的优惠不存在。');
  }

  store.promotions = nextPromotions;
  return writeStore(store);
}

module.exports = {
  readStore,
  getScreenData,
  upsertSettings,
  upsertCategory,
  deleteCategory,
  upsertDish,
  deleteDish,
  upsertPromotion,
  deletePromotion,
  sortByOrder
};


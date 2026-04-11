const fs = require('fs');
const path = require('path');
const express = require('express');
const session = require('express-session');
const multer = require('multer');
const {
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
} = require('./store');

const app = express();
const host = process.env.HOST || '0.0.0.0';
const port = Number.parseInt(process.env.PORT || '3200', 10);
const adminUser = process.env.ADMIN_USER || 'admin';
const adminPassword = process.env.ADMIN_PASSWORD || 'admin123456';
const sessionSecret = process.env.SESSION_SECRET || 'change-me-before-production';

const publicDir = path.join(__dirname, '..', 'public');
const uploadDir = path.join(publicDir, 'uploads');

fs.mkdirSync(uploadDir, { recursive: true });

const upload = multer({
  storage: multer.diskStorage({
    destination: (_req, _file, callback) => {
      callback(null, uploadDir);
    },
    filename: (_req, file, callback) => {
      const ext = path.extname(file.originalname).toLowerCase();
      const safeExt = ext && ext.length <= 8 ? ext : '.jpg';
      callback(null, `${Date.now()}-${Math.random().toString(36).slice(2, 8)}${safeExt}`);
    }
  }),
  limits: {
    fileSize: 5 * 1024 * 1024
  },
  fileFilter: (_req, file, callback) => {
    if (file.mimetype.startsWith('image/')) {
      callback(null, true);
      return;
    }

    callback(new Error('仅支持上传图片文件。'));
  }
});

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, '..', 'views'));

app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(
  session({
    secret: sessionSecret,
    resave: false,
    saveUninitialized: false,
    cookie: {
      httpOnly: true,
      sameSite: 'lax',
      maxAge: 8 * 60 * 60 * 1000
    }
  })
);

app.use(express.static(publicDir));

app.locals.formatDateTime = (value) => {
  if (!value) {
    return '-';
  }

  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

app.locals.formatMoney = (value, symbol = '￥') => {
  const amount = Number(value) || 0;
  return `${symbol}${amount.toFixed(2)}`;
};

app.locals.categoryNameById = (categories, categoryId) => {
  return categories.find((item) => item.id === categoryId)?.name || '未分类';
};

function setFlash(req, type, text) {
  req.session.flash = { type, text };
}

function consumeFlash(req) {
  const flash = req.session.flash;
  delete req.session.flash;
  return flash || null;
}

function isAuthenticated(req) {
  return Boolean(req.session?.authenticated);
}

function requireAuth(req, res, next) {
  if (!isAuthenticated(req)) {
    res.redirect('/admin/login');
    return;
  }

  next();
}

function buildAdminViewModel(req, activeNav, pageTitle) {
  const store = readStore();
  return {
    pageTitle,
    activeNav,
    flash: consumeFlash(req),
    store,
    adminAccount: req.session.username || adminUser,
    defaultPasswordInUse: adminPassword === 'admin123456'
  };
}

function runUpload(req, res, fieldName) {
  return new Promise((resolve, reject) => {
    upload.single(fieldName)(req, res, (error) => {
      if (error) {
        reject(error);
        return;
      }

      resolve();
    });
  });
}

function resolveImage(req) {
  if (req.body.removeImage === 'on') {
    return '';
  }

  if (req.file) {
    return `/uploads/${req.file.filename}`;
  }

  const external = String(req.body.imageUrl || '').trim();
  if (external) {
    return external;
  }

  return String(req.body.existingImage || '').trim();
}

app.get(['/', '/screen'], (_req, res) => {
  const screenData = getScreenData();
  res.render('screen', {
    pageTitle: `${screenData.settings.restaurantName} 展示屏`,
    screenData
  });
});

app.get('/api/screen', (_req, res) => {
  res.json(getScreenData());
});

app.get('/healthz', (_req, res) => {
  const store = readStore();
  res.json({
    ok: true,
    updatedAt: store.updatedAt
  });
});

app.get('/admin/login', (req, res) => {
  if (isAuthenticated(req)) {
    res.redirect('/admin');
    return;
  }

  res.render('admin/login', {
    pageTitle: '后台登录',
    flash: consumeFlash(req),
    defaultPasswordInUse: adminPassword === 'admin123456',
    adminUser
  });
});

app.post('/admin/login', (req, res) => {
  const username = String(req.body.username || '').trim();
  const password = String(req.body.password || '');

  if (username === adminUser && password === adminPassword) {
    req.session.authenticated = true;
    req.session.username = username;
    setFlash(req, 'success', '已登录后台管理。');
    res.redirect('/admin');
    return;
  }

  setFlash(req, 'error', '账号或密码错误。');
  res.redirect('/admin/login');
});

app.post('/admin/logout', requireAuth, (req, res) => {
  req.session.destroy(() => {
    res.redirect('/admin/login');
  });
});

app.get('/admin', requireAuth, (req, res) => {
  const store = readStore();
  const categories = sortByOrder(store.categories);
  const dishes = sortByOrder(store.dishes);
  const promotions = sortByOrder(store.promotions, 'title');

  res.render('admin/dashboard', {
    ...buildAdminViewModel(req, 'dashboard', '总览'),
    counts: {
      categories: categories.length,
      dishes: dishes.length,
      activeDishes: dishes.filter((item) => item.available).length,
      promotions: promotions.filter((item) => item.enabled).length,
      recommended: dishes.filter((item) => item.recommended && item.available).length
    },
    latestDishes: dishes.slice(0, 5),
    latestPromotions: promotions.slice(0, 4),
    categories
  });
});

app.get('/admin/settings', requireAuth, (req, res) => {
  const store = readStore();
  res.render('admin/settings', {
    ...buildAdminViewModel(req, 'settings', '展示设置'),
    settings: store.settings
  });
});

app.post('/admin/settings', requireAuth, (req, res) => {
  try {
    upsertSettings(req.body);
    setFlash(req, 'success', '展示设置已更新。');
  } catch (error) {
    setFlash(req, 'error', error.message);
  }

  res.redirect('/admin/settings');
});

app.get('/admin/categories', requireAuth, (req, res) => {
  const store = readStore();
  const categories = sortByOrder(store.categories);
  const editId = String(req.query.edit || '').trim();

  res.render('admin/categories', {
    ...buildAdminViewModel(req, 'categories', '分类管理'),
    categories,
    editingCategory: categories.find((item) => item.id === editId) || null
  });
});

app.post('/admin/categories/save', requireAuth, (req, res) => {
  try {
    upsertCategory(req.body);
    setFlash(req, 'success', '分类已保存。');
  } catch (error) {
    setFlash(req, 'error', error.message);
  }

  res.redirect('/admin/categories');
});

app.post('/admin/categories/:id/delete', requireAuth, (req, res) => {
  try {
    deleteCategory(req.params.id);
    setFlash(req, 'success', '分类已删除。');
  } catch (error) {
    setFlash(req, 'error', error.message);
  }

  res.redirect('/admin/categories');
});

app.get('/admin/dishes', requireAuth, (req, res) => {
  const store = readStore();
  const categories = sortByOrder(store.categories);
  const dishes = sortByOrder(store.dishes);
  const editId = String(req.query.edit || '').trim();

  res.render('admin/dishes', {
    ...buildAdminViewModel(req, 'dishes', '菜品管理'),
    categories,
    dishes,
    editingDish: dishes.find((item) => item.id === editId) || null
  });
});

app.post('/admin/dishes/save', requireAuth, async (req, res) => {
  try {
    await runUpload(req, res, 'imageFile');
    upsertDish({
      ...req.body,
      image: resolveImage(req)
    });
    setFlash(req, 'success', '菜品已保存。');
  } catch (error) {
    setFlash(req, 'error', error.message);
  }

  res.redirect('/admin/dishes');
});

app.post('/admin/dishes/:id/delete', requireAuth, (req, res) => {
  try {
    deleteDish(req.params.id);
    setFlash(req, 'success', '菜品已删除。');
  } catch (error) {
    setFlash(req, 'error', error.message);
  }

  res.redirect('/admin/dishes');
});

app.get('/admin/promotions', requireAuth, (req, res) => {
  const store = readStore();
  const promotions = sortByOrder(store.promotions, 'title');
  const editId = String(req.query.edit || '').trim();

  res.render('admin/promotions', {
    ...buildAdminViewModel(req, 'promotions', '优惠管理'),
    promotions,
    editingPromotion: promotions.find((item) => item.id === editId) || null
  });
});

app.post('/admin/promotions/save', requireAuth, async (req, res) => {
  try {
    await runUpload(req, res, 'imageFile');
    upsertPromotion({
      ...req.body,
      image: resolveImage(req)
    });
    setFlash(req, 'success', '优惠已保存。');
  } catch (error) {
    setFlash(req, 'error', error.message);
  }

  res.redirect('/admin/promotions');
});

app.post('/admin/promotions/:id/delete', requireAuth, (req, res) => {
  try {
    deletePromotion(req.params.id);
    setFlash(req, 'success', '优惠已删除。');
  } catch (error) {
    setFlash(req, 'error', error.message);
  }

  res.redirect('/admin/promotions');
});

app.use((error, req, res, _next) => {
  if (req.path.startsWith('/admin')) {
    setFlash(req, 'error', error.message || '发生未知错误。');
    res.redirect('back');
    return;
  }

  res.status(500).json({
    ok: false,
    message: error.message || 'Internal Server Error'
  });
});

app.listen(port, host, () => {
  console.log(`canting-display-system running at http://${host}:${port}`);
});

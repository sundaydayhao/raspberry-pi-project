# 餐厅菜品展示与优惠推荐系统

一个适合部署在树莓派上的轻量餐厅展示系统，包含：

- 前台展示屏：自动轮播菜品、推荐菜、优惠活动和分类信息
- 后台管理：编辑菜品、优惠、分类和展示参数
- 本地持久化：数据保存在 `data/store.json`
- 图片支持：可上传本地图片，也可直接使用图片 URL
- 树莓派部署：附带 `systemd` 服务模板和 Chromium kiosk 脚本

## 技术方案

- 服务端：Node.js + Express + EJS
- 数据存储：本地 JSON 文件
- 前台展示：单页大屏，自动轮播并定时从后台拉取最新数据
- 后台登录：基于 session 的轻量登录

这样做的优点是部署简单，适合单店单机运行，不需要额外数据库服务。

## 本地启动

要求：

- Node.js 18 或更高版本

初始化：

```bash
cp .env.example .env
npm install
npm start
```

默认地址：

- 前台展示页：`http://127.0.0.1:3200/`
- 后台管理页：`http://127.0.0.1:3200/admin/login`
- 健康检查：`http://127.0.0.1:3200/healthz`

默认后台账号：

- 用户名：`admin`
- 密码：`admin123456`

部署前务必修改 `.env` 中的 `ADMIN_PASSWORD` 和 `SESSION_SECRET`。

如果你只想在本机回环地址调试，也可以把 `HOST` 改成 `127.0.0.1`。

## 后台可管理内容

- 展示设置：餐厅名称、宣传语、公告、轮播速度、刷新速度、主题色
- 分类管理：如热菜、小吃、饮品等
- 菜品管理：名称、描述、价格、标签、辣度、图片、上下架、推荐标记
- 优惠管理：标题、副标题、说明、角标、图片、启用状态

## 数据与图片位置

- 菜单数据：`data/store.json`
- 上传图片：`public/uploads/`

如果要做备份，直接备份这两个位置即可。

## 树莓派部署步骤

1. 把项目放到树莓派目录，例如 `/home/pi/canting`
2. 安装 Node.js 18+ 和 Chromium
3. 在项目目录执行：

```bash
cp .env.example .env
npm install --omit=dev
```

4. 编辑 `.env`，设置后台密码
5. 修改 `deploy/canting-app.service` 和 `deploy/canting-kiosk.service` 中的用户与路径
6. 安装服务：

```bash
sudo cp deploy/canting-app.service /etc/systemd/system/
sudo cp deploy/canting-kiosk.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable canting-app.service
sudo systemctl enable canting-kiosk.service
sudo systemctl start canting-app.service
sudo systemctl start canting-kiosk.service
```

## Chromium 全屏说明

`deploy/canting-kiosk.sh` 会用 kiosk 模式打开前台展示页。适合门店电视、竖屏或收银区横屏。

如果你希望手动启动，也可以直接执行：

```bash
bash deploy/canting-kiosk.sh
```

## 适合后续扩展的方向

- 增加扫码点餐二维码展示
- 增加营业时间和门店地址卡片
- 增加定时切换早餐/午市/晚市菜单
- 把 JSON 存储升级为 SQLite
- 增加多门店、多屏幕模板配置

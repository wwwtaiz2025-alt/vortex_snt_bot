const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const path = require('path');
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname)));

// ============================================================
// 1. قاعدة البيانات والنماذج (Models)
// ============================================================
mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log('✅ MongoDB Connected'))
  .catch(err => console.error('❌ MongoDB Error:', err));

const UserSchema = new mongoose.Schema({
  name: String,
  phone: String,
  email: { type: String, unique: true, required: true },
  password: { type: String, required: true },
  balance: { type: Number, default: 0 },
  points_balance: { type: Number, default: 0 },
  casino_balance: { type: Number, default: 0 },
  miningEarnings: { type: Number, default: 0 },
  lastMineTime: { type: Date, default: null },
  transactions: [{
    type: String,
    amount: Number,
    currency: String,
    status: { type: String, default: 'completed' },
    created_at: { type: Date, default: Date.now }
  }]
});
const User = mongoose.model('User', UserSchema);

// ============================================================
// 2. دوال المساعدة (Middleware, Auth)
// ============================================================
const authMiddleware = async (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ message: 'Unauthorized' });
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const user = await User.findById(decoded.id);
    if (!user) return res.status(401).json({ message: 'User not found' });
    req.user = user;
    next();
  } catch (err) {
    return res.status(401).json({ message: 'Invalid token' });
  }
};

const MAX_DAILY_EARNINGS = 0.005;
const MINING_DURATION = 86400;

// ============================================================
// 3. نقاط النهاية (APIs)
// ============================================================

// ----- المصادقة -----
app.post('/api/register', async (req, res) => {
  const { name, phone, email, password } = req.body;
  try {
    const existing = await User.findOne({ email });
    if (existing) return res.status(400).json({ message: 'البريد الإلكتروني مستخدم بالفعل' });
    const hashed = await bcrypt.hash(password, 10);
    const user = new User({ name, phone, email, password: hashed });
    await user.save();
    res.json({ message: 'تم إنشاء الحساب بنجاح' });
  } catch (err) {
    res.status(500).json({ message: 'خطأ في التسجيل' });
  }
});

app.post('/api/login', async (req, res) => {
  const { email, password } = req.body;
  try {
    const user = await User.findOne({ email });
    if (!user) return res.status(401).json({ message: 'بيانات غير صحيحة' });
    const valid = await bcrypt.compare(password, user.password);
    if (!valid) return res.status(401).json({ message: 'بيانات غير صحيحة' });
    const token = jwt.sign({ id: user._id }, process.env.JWT_SECRET);
    res.json({ token, user });
  } catch (err) {
    res.status(500).json({ message: 'خطأ في تسجيل الدخول' });
  }
});

app.get('/api/user', authMiddleware, async (req, res) => {
  res.json(req.user);
});

// ----- التعدين -----
app.get('/api/mining-status', authMiddleware, async (req, res) => {
  const user = req.user;
  const now = Date.now();
  const last = user.lastMineTime ? new Date(user.lastMineTime).getTime() : 0;
  const elapsed = (now - last) / 1000;
  const canMine = elapsed >= MINING_DURATION;
  const remaining = Math.max(0, MINING_DURATION - elapsed);
  res.json({ canMine, miningEarnings: user.miningEarnings, cooldownRemaining: Math.floor(remaining) });
});

app.post('/api/mine', authMiddleware, async (req, res) => {
  const user = req.user;
  const now = Date.now();
  const last = user.lastMineTime ? new Date(user.lastMineTime).getTime() : 0;
  const elapsed = (now - last) / 1000;
  if (elapsed < MINING_DURATION) {
    return res.status(403).json({ 
      message: 'في مهلة الانتظار', 
      cooldownRemaining: Math.floor(MINING_DURATION - elapsed) 
    });
  }
  const newEarnings = Math.min(user.miningEarnings + 0.0005, MAX_DAILY_EARNINGS);
  user.miningEarnings = newEarnings;
  user.lastMineTime = new Date();
  await user.save();
  res.json({ 
    message: 'تم التعدين!', 
    miningEarnings: user.miningEarnings,
    balance: user.balance,
    points_balance: user.points_balance,
    casino_balance: user.casino_balance
  });
});

app.post('/api/harvest', authMiddleware, async (req, res) => {
  const user = req.user;
  const earning = user.miningEarnings;
  if (earning <= 0) {
    return res.status(400).json({ message: 'لا توجد أرباح لجنيها' });
  }
  user.points_balance += earning;
  user.miningEarnings = 0;
  user.transactions.push({ type: 'harvest', amount: earning, currency: 'Points', status: 'completed' });
  await user.save();
  res.json({ 
    message: `تم حصاد ${earning.toFixed(4)} نقطة`, 
    miningEarnings: 0,
    balance: user.balance,
    points_balance: user.points_balance,
    casino_balance: user.casino_balance,
    transactions: user.transactions
  });
});

// ----- المحفظة والسوق -----
app.post('/api/transfer/points-to-casino', authMiddleware, async (req, res) => {
  const { amount } = req.body;
  const user = req.user;
  if (user.points_balance < amount) return res.status(400).json({ message: 'رصيد نقاط غير كافي' });
  user.points_balance -= amount;
  user.casino_balance += amount;
  user.transactions.push({ type: 'transfer', amount, currency: 'Points->Casino', status: 'completed' });
  await user.save();
  res.json({ message: 'تم التحويل إلى الكازينو', balance: user.balance, points_balance: user.points_balance, casino_balance: user.casino_balance });
});

app.post('/api/transfer/casino-to-points', authMiddleware, async (req, res) => {
  const { amount } = req.body;
  const user = req.user;
  if (user.casino_balance < amount) return res.status(400).json({ message: 'رصيد كازينو غير كافي' });
  user.casino_balance -= amount;
  user.points_balance += amount;
  user.transactions.push({ type: 'transfer', amount, currency: 'Casino->Points', status: 'completed' });
  await user.save();
  res.json({ message: 'تم التحويل إلى النقاط', balance: user.balance, points_balance: user.points_balance, casino_balance: user.casino_balance });
});

app.post('/api/market/buy', authMiddleware, async (req, res) => {
  const { amount } = req.body;
  const user = req.user;
  const cost = amount * 1.05;
  if (user.balance < cost) return res.status(400).json({ message: 'رصيد USDT غير كافي' });
  user.balance -= cost;
  user.points_balance += amount;
  user.transactions.push({ type: 'buy', amount, currency: 'Points', status: 'completed' });
  await user.save();
  res.json({ message: `تم شراء ${amount} نقطة (عمولة 5%)`, balance: user.balance, points_balance: user.points_balance });
});

app.post('/api/market/sell', authMiddleware, async (req, res) => {
  const { amount } = req.body;
  const user = req.user;
  const revenue = amount * 0.95;
  if (user.points_balance < amount) return res.status(400).json({ message: 'نقاط غير كافية' });
  user.points_balance -= amount;
  user.balance += revenue;
  user.transactions.push({ type: 'sell', amount: revenue, currency: 'USDT', status: 'completed' });
  await user.save();
  res.json({ message: `تم بيع ${amount} نقطة (عمولة 5%)`, balance: user.balance, points_balance: user.points_balance });
});

app.post('/api/deposit', authMiddleware, async (req, res) => {
  const { txId } = req.body;
  if (!txId) return res.status(400).json({ message: 'يرجى إدخال رقم العملية' });
  // هنا في الواقع يتم التحقق من العملية، لكننا نعتبرها مقبولة الآن
  user.transactions.push({ type: 'deposit', amount: 0, currency: 'USDT', status: 'pending' });
  await user.save();
  res.json({ message: 'تم إيداع طلب الإيداع، بانتظار مراجعة الإدارة' });
});

app.post('/api/withdraw', authMiddleware, async (req, res) => {
  const { address, amount } = req.body;
  const user = req.user;
  if (amount < 4) return res.status(400).json({ message: 'الحد الأدنى للسحب 4 USDT' });
  if (user.balance < amount) return res.status(400).json({ message: 'رصيد غير كافي' });
  user.balance -= amount;
  user.transactions.push({ type: 'withdraw', amount, currency: 'USDT', status: 'pending' });
  await user.save();
  res.json({ message: 'تم طلب السحب، بانتظار موافقة الإدارة' });
});

app.get('/api/transactions', authMiddleware, async (req, res) => {
  res.json({ transactions: req.user.transactions.slice(-10).reverse() });
});

// ----- الألعاب -----
app.post('/api/games/:game', authMiddleware, async (req, res) => {
  const { game } = req.params;
  const { risk, bet } = req.body;
  const user = req.user;

  if (user.casino_balance < bet) {
    return res.status(400).json({ message: 'رصيد كازينو غير كافي' });
  }

  let win = false;
  let result = 0;
  let multiplier = 1;
  let details = '';

  if (game === 'chicken') {
    const safeCells = Math.floor((risk / 100) * 25);
    const hit = Math.random() > 0.5;
    win = hit;
    multiplier = hit ? (1 + (safeCells / 25) * 2) : 0;
    result = win ? bet * multiplier : 0;
    details = win ? `وصلت للخطوة ${safeCells}` : 'انفجر اللغم!';
  } else if (game === 'dice') {
    const target = risk;
    const roll = Math.floor(Math.random() * 100) + 1;
    win = roll <= target;
    multiplier = win ? 100 / target : 0;
    result = win ? bet * multiplier : 0;
    details = `الرقم: ${roll}`;
  } else if (game === 'wall') {
    const levels = 10;
    const currentLevel = Math.floor(Math.random() * levels) + 1;
    win = currentLevel > risk / 10;
    multiplier = win ? currentLevel : 0;
    result = win ? bet * multiplier : 0;
    details = `المستوى ${currentLevel}`;
  }

  user.casino_balance -= bet;
  if (win) user.casino_balance += result;

  user.transactions.push({
    type: `game_${game}`,
    amount: win ? result : -bet,
    currency: 'Casino',
    status: 'completed'
  });
  await user.save();

  res.json({
    win,
    result,
    details,
    casino_balance: user.casino_balance
  });
});

// ============================================================
// 4. تقديم ملفات الواجهة الأمامية (Index & App)
// ============================================================
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// ============================================================
// 5. تشغيل الخادم
// ============================================================
app.listen(PORT, () => {
  console.log(`🚀 Vortex server running on port ${PORT}`);
});

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname)));

// استيراد المسارات (لاحظ أننا أضفنا /src/ أمام routes)
const authRoutes = require('./src/routes/auth');
const miningRoutes = require('./src/routes/mining');
const walletRoutes = require('./src/routes/wallet');
const marketRoutes = require('./src/routes/market');
const gamesRoutes = require('./src/routes/games');

app.use('/api', authRoutes);
app.use('/api', miningRoutes);
app.use('/api', walletRoutes);
app.use('/api', marketRoutes);
app.use('/api/games', gamesRoutes);

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
    console.log(`🚀 Vortex server running on port ${PORT}`);
});

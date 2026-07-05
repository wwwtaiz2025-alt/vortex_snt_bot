const express = require('express');
const router = express.Router();
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

// POST /api/create-offer
router.post('/create-offer', async (req, res) => {
  try {
    const { telegram_id, amount } = req.body;

    if (!telegram_id || !amount || amount <= 0) {
      return res.status(400).json({ error: 'telegram_id و amount موجب مطلوبان' });
    }

    // 1. جلب المستخدم
    const { data: user, error: userError } = await supabase
      .from('users')
      .select('*')
      .eq('telegram_id', telegram_id)
      .single();

    if (userError || !user) {
      return res.status(404).json({ error: 'المستخدم غير موجود' });
    }

    // 2. التحقق من الرصيد المتاح
    const available = user.wallet_balance - user.frozen_balance;
    if (available < amount) {
      return res.status(400).json({ error: 'رصيدك غير كافٍ (يشمل النقاط المجمدة)' });
    }

    // 3. استدعاء الدالة المخزنة لإنشاء العرض وتجميد النقاط
    const { data, error } = await supabase.rpc('create_sell_offer', {
      p_seller_id: user.id,
      p_amount: amount
    });

    if (error) {
      console.error('خطأ في rpc:', error);
      return res.status(500).json({ error: 'فشل في إنشاء العرض' });
    }

    return res.json({
      success: true,
      message: 'تم إنشاء العرض بنجاح وتم تجميد النقاط',
      offer_id: data.offer_id,
      frozen_amount: amount
    });

  } catch (err) {
    console.error('خطأ في create-offer:', err);
    return res.status(500).json({ error: 'حدث خطأ في الخادم' });
  }
});

module.exports = router;

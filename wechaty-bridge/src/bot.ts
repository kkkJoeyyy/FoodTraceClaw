import { WechatyBuilder, Message, log, types } from 'wechaty';
import QRCode from 'qrcode-terminal';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const PUPPET = process.env.WECHATY_PUPPET || 'wechaty-puppet-wechat4u';
const ALLOW_SELF = process.env.ALLOW_SELF === 'true';
const WHITELIST: string[] = (process.env.WHITELIST || '')
  .split(',')
  .map(s => s.trim())
  .filter(Boolean);

function isAllowed(name: string): boolean {
  if (WHITELIST.length === 0) return false; // no whitelist = deny all
  return WHITELIST.includes(name);
}

// Map: WeChat user ID -> our session_id
const sessionMap = new Map<string, string>();

function getSessionId(wechatUserId: string): string {
  let sid = sessionMap.get(wechatUserId);
  if (!sid) {
    sid = `wx_${wechatUserId}`;
    sessionMap.set(wechatUserId, sid);
    log.info('New session', { wechatUserId, sid });
  }
  return sid;
}

async function callBackend(path: string, params: Record<string, string>): Promise<any> {
  const url = new URL(path, BACKEND_URL);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url.toString(), { signal: AbortSignal.timeout(120000) });
  if (!res.ok) throw new Error(`Backend returned ${res.status}`);
  return res.json();
}

async function callBackendPost(path: string, params: Record<string, string>): Promise<any> {
  const url = new URL(path, BACKEND_URL);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url.toString(), { method: 'POST', signal: AbortSignal.timeout(120000) });
  if (!res.ok) throw new Error(`Backend returned ${res.status}`);
  return res.json();
}

function formatStoresReply(data: any): string {
  // If there are stores, list first 5
  const stores = data.stores || data.all_stores || [];
  if (stores.length === 0) return data.reply || '';

  const lines: string[] = [data.reply || ''];
  for (let i = 0; i < Math.min(stores.length, 5); i++) {
    const s = stores[i];
    const dist = s.distance_km != null ? `(${s.distance_km}km)` : '';
    const closestAddr = (s as any).closest_addr || '';
    const addr = closestAddr ? ` · ${closestAddr}${dist}` : (dist ? ` · ${dist}` : '');
    const dishNames = (s.dishes || []).slice(0, 3).map((d: any) => d.name).filter(Boolean).join('、');
    const dishStr = dishNames ? `\n  菜品：${dishNames}` : '';
    lines.push(`${i + 1}. ${s.name}${addr ? `\n   ${addr}` : ''}${dishStr}`);
  }
  return lines.join('\n');
}

async function handleLocationFromAddress(
  msg: Message, address: string, sessionId: string
) {
  try {
    // Let backend do the geocoding (better network)
    const data = await callBackendPost('/api/location', {
      session_id: sessionId,
      address: address,
    });
    const reply = formatStoresReply(data);
    await msg.say(reply);
  } catch (e: any) {
    log.error('Location from address error', e);
    await msg.say('位置解析失败，请重试');
  }
}

async function handleTextMessage(msg: Message) {
  const text = msg.text().trim();
  const talker = msg.talker();
  const wechatId = talker.id;
  const sessionId = getSessionId(wechatId);

  log.info('Text message', { from: talker.name(), text: text.substring(0, 50) });


  // Detect WeChat location share (comes as text: "广东省广州市越秀区...: url")
  const locationMatch = text.match(
    /^(?:([一-龥]{2,}(?:省|市|区|县|镇|路|街|号|附近).+?))(?:[:：]|\/cgi-bin)/
  );
  if (locationMatch) {
    const address = locationMatch[1].trim();
    console.log(`[LOCATION] Detected from text: "${address}"`);
    await handleLocationFromAddress(msg, address, sessionId);
    return;
  }

  // 1. Immediately send acknowledgment
  let ackText = '收到～正在处理中...';
  const lower = text.toLowerCase();
  if (
    text.includes('有什么好吃的') || text.includes('有什么美食') ||
    text.includes('推荐') || text.includes('好吃的')
  ) {
    if (text.includes('附近') || text.includes('周边') || text.includes('最近')) {
      ackText = '收到～正在查询中...';
    } else {
      ackText = '收到～正在查询中...';
    }
  } else if (text.length > 20 || text.includes('👍') || text.includes('👎')) {
    ackText = '收到～正在分析记录中...';
  }

  await msg.say(ackText);

  // 2. Call backend
  try {
    const data = await callBackend('/api/chat', {
      message: text,
      session_id: sessionId,
    });

    const reply = formatStoresReply(data);
    await msg.say(reply);

    // If more than 5 stores, tell user how to see more
    const total = data.total || 0;
    if (total > 5) {
      await msg.say(`（共 ${total} 家店铺，回复「还有吗」查看更多）`);
    }
  } catch (e: any) {
    log.error('Backend error', e);
    await msg.say('抱歉，处理失败，请稍后重试');
  }
}

async function handleLocationMessage(msg: Message) {
  const talker = msg.talker();
  const sessionId = getSessionId(talker.id);

  log.info('Location message', { from: talker.name() });

  try {
    // WeChat location message - try to extract coordinates
    const locationPayload = msg.payload as any;
    // wechaty-wechat4u provides location as text, not lat/lon directly
    // For wechat4u puppet, location is in text format like "地点名称\n地址"
    const locationText = msg.text();
    log.info('Location text', { text: locationText });

    // Try to parse location from the message payload
    // If the puppet provides lat/lon, use them; otherwise use text
    const lat = locationPayload?.lat || locationPayload?.latitude;
    const lon = locationPayload?.lng || locationPayload?.longitude || locationPayload?.lon;

    if (lat != null && lon != null) {
      const data = await callBackendPost('/api/location', {
        session_id: sessionId,
        lat: String(lat),
        lon: String(lon),
      });
      const reply = formatStoresReply(data);
      await msg.say(reply);
    } else {
      // Can't extract coordinates, ask user to try again
      await msg.say('无法读取位置信息，请尝试重新发送位置，或直接告诉我你在哪个城市～');
    }
  } catch (e: any) {
    log.error('Location handling error', e);
    await msg.say('抱歉，处理位置信息失败');
  }
}

async function handleImageMessage(msg: Message) {
  const talker = msg.talker();
  const sessionId = getSessionId(talker.id);

  log.info('Image message', { from: talker.name() });

  await msg.say('收到图片～正在识别中...');

  try {
    // Download image as base64
    const imageFile = await msg.toFileBox();
    const buffer = await imageFile.toBuffer();
    const base64 = buffer.toString('base64');

    // Call backend with image
    // Use POST /api/chat for image
    const res = await fetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: '',
        session_id: sessionId,
        images: [base64],
      }),
      signal: AbortSignal.timeout(120000),
    });

    // Read SSE response
    const text = await res.text();
    // Parse last SSE event (the done event)
    const events = text.split('\n\n').filter(Boolean);
    let lastData: any = { reply: '未识别到美食信息' };
    for (const event of events) {
      if (event.startsWith('data: ')) {
        try {
          lastData = JSON.parse(event.slice(6));
        } catch {}
      }
    }

    const reply = formatStoresReply(lastData);
    await msg.say(reply);
  } catch (e: any) {
    log.error('Image handling error', e);
    await msg.say('抱歉，识别失败，请稍后重试');
  }
}

async function main() {
  let heartbeatLogged = false;
  console.log(`Starting bot with puppet: ${PUPPET}`);
  console.log(`Backend URL: ${BACKEND_URL}`);
  if (ALLOW_SELF) console.log('Self-message mode ENABLED (for testing)');

  const bot = WechatyBuilder.build({
    name: 'foodtrace-bot',
    puppet: PUPPET as any,
    puppetOptions: PUPPET === 'wechaty-puppet-wechat4u' ? { uos: true } : {},
  });

  bot.on('scan', (qrcode, status) => {
    console.log(`\n[SCAN] Scan QR Code to login (status: ${status})\n`);
    QRCode.generate(qrcode, { small: true });
  });

  bot.on('login', async (user) => {
    const contact = await user;
    console.log(`[LOGIN] Logged in as: ${contact.name()}`);
  });

  bot.on('logout', async (user) => {
    const contact = await user;
    console.log(`[LOGOUT] ${contact.name()}`);
  });

  bot.on('ready', () => {
    console.log('[READY] Bot is ready! All data synced.');
  });

  bot.on('friendship', async (friendship) => {
    const contact = await friendship.contact();
    console.log(`[FRIENDSHIP] type=${friendship.type()} from=${contact.name()}`);
  });

  bot.on('error', (e) => {
    console.error('[ERROR]', e);
  });

  bot.on('heartbeat', (data) => {
    // Only log first heartbeat
    if (!heartbeatLogged) {
      console.log(`[HEARTBEAT] Bot is alive, data: ${JSON.stringify(data)}`);
      heartbeatLogged = true;
    }
  });

  bot.on('room-invite', async (invitation) => {
    const inviter = await invitation.inviter();
    console.log(`[ROOM-INVITE] from=${inviter.name()}`);
  });

  bot.on('message', async (msg: Message) => {
    // Skip messages from self unless testing
    if (msg.self() && !ALLOW_SELF) return;

    const type = msg.type();
    const typeName = types.Message[type] || `Unknown(${type})`;
    const talkerName = msg.talker().name();
    const text = msg.text().substring(0, 100);

    // Always log incoming messages for debugging
    console.log(`[MSG] type=${typeName}(${type}) from="${talkerName}" text="${text}"`);

    // Whitelist check
    if (!isAllowed(talkerName)) {
      console.log(`[BLOCKED] ${talkerName} not in whitelist`);
      return;
    }

    try {
      if (type === types.Message.Text) {
        await handleTextMessage(msg);
      } else if (type === types.Message.Image) {
        await handleImageMessage(msg);
      } else if (type === types.Message.Attachment) {
        // WeChat location or other attachment
        await handleTextMessage(msg); // Try treating as text first
      } else {
        log.info('Unhandled message type', { type: typeName });
        await msg.say(`收到消息（类型: ${typeName}），暂仅支持文字、图片和位置～`);
      }
    } catch (e: any) {
      log.error('Message handling error', e);
      console.error('Handler error:', e);
    }
  });

  bot.on('error', (e) => {
    log.error('Bot error', e);
  });

  await bot.start();
  console.log('Wechaty bridge started, waiting for WeChat login...');
}

main().catch((e) => {
  console.error('Failed to start bot:', e);
  process.exit(1);
});

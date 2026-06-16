// Vercel serverless: fetch recent Google News headlines for a topic (server-side, avoids browser CORS).
// admin '주제로 글 생성'이 시의성 주제에서 과거/허구 정보를 쓰지 않도록 최신 실제 헤드라인을 주입한다.
export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const q = (req.query && req.query.q ? String(req.query.q) : '').trim();
  if (!q) return res.status(400).json({ error: 'q required', headlines: [] });

  try {
    const url = `https://news.google.com/rss/search?q=${encodeURIComponent(q)}&hl=en-US&gl=US&ceid=US:en`;
    const r = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0 (compatible; KoreanSalarymanBot/1.0)' } });
    if (!r.ok) return res.status(200).json({ headlines: [], note: `rss ${r.status}` });

    const xml = await r.text();
    const headlines = [];
    const itemRe = /<item>([\s\S]*?)<\/item>/g;
    let item;
    while ((item = itemRe.exec(xml)) && headlines.length < 10) {
      const block = item[1];
      const tm = block.match(/<title>([\s\S]*?)<\/title>/);
      const dm = block.match(/<pubDate>([\s\S]*?)<\/pubDate>/);
      if (!tm) continue;
      let title = tm[1].replace(/<!\[CDATA\[|\]\]>/g, '').trim();
      title = title.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
                   .replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&apos;/g, "'");
      const date = dm ? dm[1].trim() : '';
      if (title) headlines.push({ title, date });
    }
    return res.status(200).json({ headlines });
  } catch (e) {
    // 실패해도 200 + 빈 배열 (호출측이 best-effort로 무시하고 진행)
    return res.status(200).json({ headlines: [], error: String(e && e.message || e) });
  }
}

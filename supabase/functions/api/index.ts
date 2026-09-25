// 라밥 API — 모든 판정은 여기서만. 앱은 결과만 표시.
import { createClient } from "npm:@supabase/supabase-js@2";

const db = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (b: unknown, s = 200) =>
  new Response(JSON.stringify(b), { status: s, headers: { ...CORS, "Content-Type": "application/json" } });
const fail = (reason: string, s = 400) => json({ ok: false, reason }, s);

// KST 도우미
const KST = 9 * 60 * 60 * 1000;
function kstNow() { return new Date(Date.now() + KST); }
function kstTime(d: Date) { return d.toISOString().slice(11, 19); }      // HH:MM:SS
function kstDate(d: Date) { return d.toISOString().slice(0, 10); }       // YYYY-MM-DD
function kstWeekday(d: Date) { return d.getUTCDay(); }

function normPhone(p: string) {
  const d = (p || "").replace(/\D/g, "");
  return /^01[016789]\d{7,8}$/.test(d) ? d : null;
}
function inRange(t: string, open: string, close: string) { return t >= open && t <= close; }

async function auth(token?: string) {
  if (!token) return null;
  const { data } = await db.from("users").select("*").eq("token", token).eq("status", "active").maybeSingle();
  return data;
}

async function windows() {
  const { data } = await db.from("discount_windows").select("start_time,end_time").order("start_time");
  return data ?? [];
}
function windowNow(ws: { start_time: string; end_time: string }[], t: string) {
  return ws.some((w) => inRange(t, w.start_time, w.end_time));
}
function nextWindow(ws: { start_time: string; end_time: string }[], t: string) {
  const n = ws.map((w) => w.start_time).filter((s) => s > t).sort()[0];
  return n ? n.slice(0, 5) : null; // null이면 오늘 남은 시간대 없음
}

async function todayRedemption(userId: string, date: string) {
  const { data } = await db.from("redemptions").select("id, store_id, redeemed_at, stores(name)")
    .eq("user_id", userId).eq("redeemed_date", date).maybeSingle();
  return data;
}

async function membership(userId: string) {
  const { data } = await db.from("memberships").select("*").eq("user_id", userId).maybeSingle();
  if (!data) return null;
  const live = (data.status === "active" || data.status === "past_due") && new Date(data.current_period_end) > new Date();
  return { ...data, live };
}

// ---------- actions ----------
async function join(b: { code?: string; phone?: string; device_id?: string }) {
  const code = (b.code || "").trim().toUpperCase();
  const phone = normPhone(b.phone || "");
  if (!code) return fail("초대 코드를 입력하세요");
  if (!phone) return fail("휴대폰 번호 형식이 올바르지 않습니다");

  // 재설치: 같은 번호 + 같은 기기면 토큰 재발급
  const { data: existing } = await db.from("users").select("*").eq("phone", phone).maybeSingle();
  if (existing) {
    if (existing.status !== "active") return fail("이용이 제한된 계정입니다");
    if (b.device_id && existing.device_id === b.device_id) return json({ ok: true, token: existing.token, returning: true });
    return fail("이미 가입된 번호입니다. 다른 기기에서는 로그인할 수 없어요. 문의: 라밥 카톡채널");
  }

  const { data: inv } = await db.from("invites").select("*").eq("code", code).maybeSingle();
  if (!inv) return fail("존재하지 않는 초대 코드입니다");
  if (inv.expires_at && new Date(inv.expires_at) < new Date()) return fail("만료된 초대 코드입니다");
  if (inv.used_count >= inv.max_uses) return fail("사용 횟수를 다 쓴 초대 코드입니다");

  const { data: user, error } = await db.from("users")
    .insert({ phone, device_id: b.device_id ?? null, invited_by: inv.issuer_id, invite_code_used: code })
    .select().single();
  if (error) return fail("가입 처리 중 오류: " + error.message, 500);

  await db.from("invites").update({ used_count: inv.used_count + 1 }).eq("code", code);

  // 첫 달 무료
  const end = new Date(Date.now() + 30 * 24 * 3600 * 1000).toISOString();
  await db.from("memberships").insert({ user_id: user.id, status: "active", price_krw: 0, current_period_end: end });

  // 내 초대 코드 (5명)
  const my = "R" + phone.slice(-4) + Math.random().toString(36).slice(2, 5).toUpperCase();
  await db.from("invites").insert({ code: my, issuer_id: user.id, max_uses: 5 });

  return json({ ok: true, token: user.token });
}

async function me(u: any) {
  const now = kstNow(); const t = kstTime(now); const d = kstDate(now);
  const ws = await windows();
  const [m, today, inv, cnt] = await Promise.all([
    membership(u.id),
    todayRedemption(u.id, d),
    db.from("invites").select("code, used_count, max_uses").eq("issuer_id", u.id).maybeSingle().then((r) => r.data),
    db.from("redemptions").select("id", { count: "exact", head: true }).eq("user_id", u.id).then((r) => r.count ?? 0),
  ]);
  return json({
    ok: true,
    phone_masked: u.phone.slice(0, 3) + "-****-" + u.phone.slice(-4),
    membership: m ? { status: m.status, live: m.live, period_end: m.current_period_end, price_krw: m.price_krw } : null,
    windows: ws.map((w) => [w.start_time.slice(0, 5), w.end_time.slice(0, 5)]),
    in_window: windowNow(ws, t),
    next_window: nextWindow(ws, t),
    used_today: today ? { store: (today as any).stores?.name, at: today.redeemed_at } : null,
    invite: inv,
    total_count: cnt,
    now: t.slice(0, 5),
  });
}

async function stores(_u: any) {
  const now = kstNow(); const t = kstTime(now); const wd = kstWeekday(now);
  const { data: list } = await db.from("stores").select("id,name,address,lat,lng,phone,menu_note,naver_url,discount_krw, store_hours(weekday,open_time,close_time)")
    .eq("is_active", true).order("name");
  const out = (list ?? []).map((s: any) => {
    const hours = (s.store_hours ?? []).filter((h: any) => h.weekday === wd)
      .map((h: any) => [h.open_time.slice(0, 5), h.close_time.slice(0, 5)]).sort();
    const open_now = (s.store_hours ?? []).some((h: any) => h.weekday === wd && inRange(t, h.open_time, h.close_time));
    const { store_hours: _h, ...rest } = s;
    return { ...rest, today_hours: hours, open_now };
  });
  return json({ ok: true, stores: out });
}

async function redeem(u: any, b: { secret?: string }) {
  const raw = (b.secret || "").trim();
  const secret = raw.split("/").pop()!.split("?")[0]; // URL이 와도 마지막 세그먼트만
  if (!secret) return fail("QR을 인식하지 못했습니다");

  const now = kstNow(); const t = kstTime(now); const d = kstDate(now); const wd = kstWeekday(now);

  const m = await membership(u.id);
  if (!m?.live) return fail("멤버십이 만료되었습니다");

  const ws = await windows();
  if (!windowNow(ws, t)) {
    const n = nextWindow(ws, t);
    return fail(n ? `지금은 할인 시간이 아니에요. ${n}부터 가능` : "오늘 할인 시간이 끝났어요. 내일 14:00부터");
  }

  const { data: s } = await db.from("stores").select("id,name,discount_krw,is_active, store_hours(weekday,open_time,close_time)")
    .eq("qr_secret", secret).maybeSingle();
  if (!s || !s.is_active) return fail("등록되지 않은 매장 QR입니다");
  const open = (s.store_hours ?? []).some((h: any) => h.weekday === wd && inRange(t, h.open_time, h.close_time));
  if (!open) return fail(`${s.name}은(는) 지금 영업시간이 아니에요`);

  const today = await todayRedemption(u.id, d);
  if (today) return fail("오늘은 이미 사용했어요. 하루 1회만 가능");

  const { data: r, error } = await db.from("redemptions")
    .insert({ user_id: u.id, store_id: s.id, discount_krw: s.discount_krw, redeemed_date: d }).select().single();
  if (error) return fail(error.code === "23505" ? "오늘은 이미 사용했어요. 하루 1회만 가능" : "처리 오류: " + error.message, 500);

  return json({ ok: true, store: s.name, discount_krw: s.discount_krw, at: r.redeemed_at, now: t.slice(0, 5) });
}

async function history(u: any) {
  const { data } = await db.from("redemptions").select("redeemed_at, discount_krw, stores(name)")
    .eq("user_id", u.id).order("redeemed_at", { ascending: false }).limit(60);
  return json({ ok: true, items: (data ?? []).map((r: any) => ({ at: r.redeemed_at, krw: r.discount_krw, store: r.stores?.name })) });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return fail("POST only", 405);
  let b: any; try { b = await req.json(); } catch { return fail("bad json"); }

  if (b.action === "join") return join(b);
  const u = await auth(b.token);
  if (!u) return fail("로그인이 필요합니다", 401);
  switch (b.action) {
    case "me": return me(u);
    case "stores": return stores(u);
    case "redeem": return redeem(u, b);
    case "history": return history(u);
    default: return fail("unknown action", 404);
  }
});

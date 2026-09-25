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
async function createUser(phone: string, code: string) {
  const { data: inv } = await db.from("invites").select("*").eq("code", code).maybeSingle();
  if (!inv) return fail("존재하지 않는 초대 코드예요");
  if (inv.expires_at && new Date(inv.expires_at) < new Date()) return fail("만료된 초대 코드예요");
  if (inv.used_count >= inv.max_uses) return fail("사용 횟수를 다 쓴 초대 코드예요");
  const { data: user, error } = await db.from("users")
    .insert({ phone, invited_by: inv.issuer_id, invite_code_used: code }).select().single();
  if (error) return fail("가입 처리 중 오류: " + error.message, 500);
  await db.from("invites").update({ used_count: inv.used_count + 1 }).eq("code", code);
  const end = new Date(Date.now() + 30 * 24 * 3600 * 1000).toISOString();
  await db.from("memberships").insert({ user_id: user.id, status: "active", price_krw: 0, current_period_end: end });
  const my = "R" + phone.slice(-4) + Math.random().toString(36).slice(2, 5).toUpperCase();
  await db.from("invites").insert({ code: my, issuer_id: user.id, max_uses: 5 });
  return json({ ok: true, token: user.token });
}

// SMS (Solapi). 키가 없으면 OTP 비활성 → 번호만으로 로그인
const SOLAPI_KEY = Deno.env.get("SOLAPI_API_KEY"); const SOLAPI_SECRET = Deno.env.get("SOLAPI_API_SECRET"); const SMS_FROM = Deno.env.get("SMS_FROM");
const otpEnabled = () => !!(SOLAPI_KEY && SOLAPI_SECRET && SMS_FROM);
async function sendSms(to: string, text: string) {
  const date = new Date().toISOString(); const salt = crypto.randomUUID().replace(/-/g, "");
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(SOLAPI_SECRET!), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = Array.from(new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(date + salt)))).map((b) => b.toString(16).padStart(2, "0")).join("");
  const r = await fetch("https://api.solapi.com/messages/v4/send", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `HMAC-SHA256 apiKey=${SOLAPI_KEY}, date=${date}, salt=${salt}, signature=${sig}` },
    body: JSON.stringify({ message: { to, from: SMS_FROM, text } }),
  });
  if (!r.ok) throw new Error("SMS 발송 실패: " + (await r.text()).slice(0, 200));
}

// 1단계: 번호 입력
async function start(b: { phone?: string; code?: string }) {
  const phone = normPhone(b.phone || "");
  if (!phone) return fail("휴대폰 번호 형식이 올바르지 않아요");
  const { data: existing } = await db.from("users").select("*").eq("phone", phone).maybeSingle();
  if (existing && existing.status !== "active") return fail("이용이 제한된 계정이에요");

  if (!otpEnabled()) { // 직접 로그인 모드
    if (existing) return json({ ok: true, mode: "direct", token: existing.token });
    const code = (b.code || "").trim().toUpperCase();
    if (!code) return json({ ok: true, mode: "direct", is_new: true });
    return createUser(phone, code);
  }

  // OTP 모드: 60초 재발송 제한, 하루 10회
  const { data: prev } = await db.from("otps").select("*").eq("phone", phone).maybeSingle();
  if (prev) {
    if (Date.now() - new Date(prev.last_sent_at).getTime() < 60_000) return fail("잠시 후 다시 요청해 주세요 (1분)");
    if (prev.sent_count >= 10 && Date.now() - new Date(prev.last_sent_at).getTime() < 86_400_000) return fail("오늘 인증 요청 한도를 넘었어요");
  }
  const otp = String(Math.floor(100000 + Math.random() * 900000));
  await db.from("otps").upsert({ phone, code: otp, expires_at: new Date(Date.now() + 5 * 60_000).toISOString(), attempts: 0,
    sent_count: prev && Date.now() - new Date(prev.last_sent_at).getTime() < 86_400_000 ? prev.sent_count + 1 : 1, last_sent_at: new Date().toISOString() });
  try { await sendSms(phone, `[라밥] 인증번호 ${otp} (5분 안에 입력)`); } catch (e) { return fail(String(e), 502); }
  return json({ ok: true, mode: "otp", is_new: !existing });
}

// 2단계: 인증번호 확인
async function verify(b: { phone?: string; otp?: string; code?: string }) {
  const phone = normPhone(b.phone || ""); const otp = (b.otp || "").trim();
  if (!phone || !/^\d{6}$/.test(otp)) return fail("인증번호 6자리를 입력해 주세요");
  const { data: row } = await db.from("otps").select("*").eq("phone", phone).maybeSingle();
  if (!row || new Date(row.expires_at) < new Date()) return fail("인증번호가 만료됐어요. 다시 받아주세요");
  if (row.attempts >= 5) return fail("틀린 횟수가 많아요. 인증번호를 다시 받아주세요");
  if (row.code !== otp) { await db.from("otps").update({ attempts: row.attempts + 1 }).eq("phone", phone); return fail("인증번호가 틀렸어요"); }
  await db.from("otps").delete().eq("phone", phone);
  const { data: existing } = await db.from("users").select("*").eq("phone", phone).maybeSingle();
  if (existing) return json({ ok: true, token: existing.token });
  const code = (b.code || "").trim().toUpperCase();
  if (!code) return fail("처음이면 초대 코드가 필요해요");
  return createUser(phone, code);
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

  if (b.action === "start") return start(b);
  if (b.action === "verify") return verify(b);
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

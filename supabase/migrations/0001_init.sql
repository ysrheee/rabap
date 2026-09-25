-- 라밥 초기 스키마 (2026-09-25)
create extension if not exists pgcrypto;

create table users (
  id uuid primary key default gen_random_uuid(),
  phone text unique not null,
  device_id text,
  token text unique not null default encode(gen_random_bytes(24),'hex'),
  invited_by uuid references users(id),
  invite_code_used text not null,
  status text not null default 'active' check (status in ('active','blocked')),
  created_at timestamptz default now()
);

create table invites (
  code text primary key,
  issuer_id uuid references users(id),        -- null = 관리자 시드 코드
  max_uses int not null default 5,
  used_count int not null default 0,
  expires_at timestamptz,
  created_at timestamptz default now()
);

create table memberships (
  id uuid primary key default gen_random_uuid(),
  user_id uuid unique references users(id),
  status text not null check (status in ('active','past_due','canceled','expired')),
  price_krw int not null default 1000,
  billing_key text,
  current_period_end timestamptz not null,
  canceled_at timestamptz,
  created_at timestamptz default now()
);

create table payments (
  id uuid primary key default gen_random_uuid(),
  membership_id uuid references memberships(id),
  amount_krw int not null,
  status text not null check (status in ('paid','failed','refunded')),
  pg_payment_key text,
  paid_at timestamptz default now()
);

create table stores (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  address text not null,
  lat double precision,
  lng double precision,
  phone text,
  menu_note text,                              -- 대표 메뉴/가격 한 줄
  naver_url text,                              -- 네이버지도 링크
  qr_secret text unique not null default encode(gen_random_bytes(12),'hex'),
  discount_krw int not null default 3000,
  is_active boolean not null default true,
  created_at timestamptz default now()
);

create table store_hours (
  id bigserial primary key,
  store_id uuid references stores(id) on delete cascade,
  weekday int not null check (weekday between 0 and 6),  -- 0=일
  open_time time not null,
  close_time time not null
);
create index on store_hours(store_id, weekday);

create table redemptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id),
  store_id uuid references stores(id),
  discount_krw int not null,
  redeemed_at timestamptz default now(),
  redeemed_date date not null
);
create unique index one_per_day on redemptions(user_id, redeemed_date);

create table discount_windows (
  id serial primary key,
  start_time time not null,
  end_time time not null
);
insert into discount_windows(start_time, end_time) values ('14:00','17:00'), ('20:00','23:59:59');

-- 외부(anon) 직접 접근 전부 차단. 모든 접근은 Edge Function(service role)으로만.
alter table users enable row level security;
alter table invites enable row level security;
alter table memberships enable row level security;
alter table payments enable row level security;
alter table stores enable row level security;
alter table store_hours enable row level security;
alter table redemptions enable row level security;
alter table discount_windows enable row level security;

-- 매장 영업시간 일괄 입력 도우미: select set_hours('매장id', '11:00','15:00'), set_hours('매장id','17:00','21:00')
create or replace function set_hours(p_store uuid, p_open time, p_close time, p_days int[] default '{0,1,2,3,4,5,6}')
returns void language sql as $$
  insert into store_hours(store_id, weekday, open_time, close_time)
  select p_store, d, p_open, p_close from unnest(p_days) d;
$$;

-- 시드 코드 발급: select make_seed_codes(30)
create or replace function make_seed_codes(n int) returns setof text language plpgsql as $$
declare c text; i int;
begin
  for i in 1..n loop
    c := upper(substr(encode(gen_random_bytes(6),'hex'),1,8));
    insert into invites(code, issuer_id, max_uses) values (c, null, 1);
    return next c;
  end loop;
end $$;

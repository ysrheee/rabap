create table push_subs (
  id bigserial primary key,
  user_id uuid references users(id) on delete cascade,
  endpoint text unique not null,
  p256dh text not null,
  auth text not null,
  ua text,
  created_at timestamptz default now(),
  last_ok_at timestamptz,
  fail_count int not null default 0
);
alter table push_subs enable row level security;

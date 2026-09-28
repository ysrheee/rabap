create table events (
  id bigserial primary key,
  event text not null,              -- invite_open, join_view 등
  code text,                        -- 초대 코드
  visitor text,                     -- 브라우저 익명 ID (localStorage)
  ua text,
  created_at timestamptz default now()
);
create index on events(code, event);
alter table events enable row level security;

create table otps (
  phone text primary key,
  code text not null,
  expires_at timestamptz not null,
  attempts int not null default 0,
  sent_count int not null default 1,
  last_sent_at timestamptz not null default now()
);
alter table otps enable row level security;

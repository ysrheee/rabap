alter table events add column if not exists user_id uuid references users(id);
create index if not exists events_user_idx on events(user_id, created_at);

alter table memberships add column if not exists card_info text;          -- 예: "신한 **** 1234"
alter table memberships add column if not exists customer_key text unique; -- 토스 customerKey
alter table memberships add column if not exists fail_count int not null default 0;
alter table payments add column if not exists order_id text unique;
alter table payments add column if not exists fail_reason text;

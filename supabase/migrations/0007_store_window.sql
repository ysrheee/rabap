-- 매장별 할인 시작/종료 시각 (null이면 전역 discount_windows 사용)
alter table stores add column if not exists window_start time;
alter table stores add column if not exists window_end time;

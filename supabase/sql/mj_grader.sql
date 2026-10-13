-- Mary Jane grader: paste this whole file into the Supabase SQL Editor
-- (finance chief project) and press Run. Safe to run more than once.
-- It scores each logged recommendation against SPY at 30/90/365 days.
create or replace function public.mj_grade_due_evaluations()
returns text
language plpgsql
security definer
set search_path = public
as $$
declare
  e record;
  start_px numeric; end_px numeric; bench_start numeric; bench_end numeric;
  ret numeric; bench_ret numeric; dir integer; edge numeric;
  graded integer := 0; waiting integer := 0; unavailable integer := 0;
begin
  for e in
    select ev.id, ev.due_at, ev.start_price, r.ticker, r.action, r.created_at::date as decided_on
    from public.mj_recommendation_evaluations ev
    join public.mj_recommendations r on r.id = ev.recommendation_id
    where ev.status in ('pending', 'due') and ev.due_at <= current_date
  loop
    if e.ticker is null then
      update public.mj_recommendation_evaluations
         set status = 'unavailable', notes = 'No ticker on the recommendation', evaluated_at = now()
       where id = e.id;
      unavailable := unavailable + 1;
      continue;
    end if;

    start_px := coalesce(e.start_price, public.mj_price_on_or_after(e.ticker, e.decided_on));
    end_px := public.mj_price_on_or_after(e.ticker, e.due_at);

    if start_px is null or end_px is null or start_px = 0 then
      if current_date > e.due_at + 14 then
        update public.mj_recommendation_evaluations
           set status = 'unavailable', evaluated_at = now(),
               notes = 'No US price history for ' || e.ticker || ' in price_snapshots'
         where id = e.id;
        unavailable := unavailable + 1;
      else
        update public.mj_recommendation_evaluations set status = 'due' where id = e.id;
        waiting := waiting + 1;
      end if;
      continue;
    end if;

    bench_start := public.mj_price_on_or_after('SPY', e.decided_on);
    bench_end := public.mj_price_on_or_after('SPY', e.due_at);
    ret := round((end_px / start_px - 1) * 100, 2);
    bench_ret := case when bench_start > 0 and bench_end is not null
                      then round((bench_end / bench_start - 1) * 100, 2) end;
    dir := public.mj_action_direction(e.action);
    edge := dir * (ret - coalesce(bench_ret, 0));

    update public.mj_recommendation_evaluations set
      status = 'completed',
      start_price = start_px,
      end_price = end_px,
      return_pct = ret,
      benchmark_return_pct = bench_ret,
      outcome_grade = case when dir <> 0 then round(edge, 2) end,
      opportunity_cost_pct = case when dir <> 0 then round(greatest(0, -edge), 2) end,
      thesis_result = case
        when dir = 0 then 'not_directional'
        when edge > 1 then 'beat'
        when edge < -1 then 'lagged'
        else 'inline' end,
      notes = case when bench_ret is null
                   then 'SPY history unavailable for this window; graded on absolute return'
                   else 'Graded vs SPY' end,
      evaluated_at = now()
    where id = e.id;
    graded := graded + 1;
  end loop;

  return format('graded=%s waiting=%s unavailable=%s', graded, waiting, unavailable);
end $$;

revoke all on function public.mj_grade_due_evaluations() from public, anon, authenticated;

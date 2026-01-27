-- Create a secure function to look up user ID by email
-- This allows the backend to find users to invite by querying auth.users directly via a secure RPC
-- Run this in Supabase SQL Editor

create or replace function get_user_id_by_email(email text)
returns table (id uuid)
language plpgsql
security definer
set search_path = public
as $$
begin
  return query
  select au.id
  from auth.users au
  where au.email = get_user_id_by_email.email;
end;
$$;

-- Grant execute permission to authenticated users (or service role)
grant execute on function get_user_id_by_email(text) to authenticated;
grant execute on function get_user_id_by_email(text) to service_role;

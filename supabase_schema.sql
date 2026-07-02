-- ============================================================
-- NEXUS IA — Schema do Supabase
-- Cole este script inteiro em: Supabase > SQL Editor > New Query > Run
-- ============================================================

-- Tabela de perfis (1 linha por usuário, criada automaticamente no cadastro)
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  created_at timestamptz default now()
);

-- Tabela de conversas
create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  title text default 'Nova conversa',
  created_at timestamptz default now()
);

-- Tabela de mensagens
create table if not exists public.messages (
  id bigint generated always as identity primary key,
  conversation_id uuid references public.conversations(id) on delete cascade,
  user_id uuid references auth.users(id) on delete cascade,
  role text not null,               -- 'user' ou 'assistant'
  content text,
  is_image boolean default false,
  attachments jsonb,
  created_at timestamptz default now()
);

-- ── Segurança: cada usuário só enxerga os próprios dados ──
alter table public.profiles enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;

create policy "usuario ve seu proprio perfil"
  on public.profiles for select
  using (auth.uid() = id);

create policy "usuario gerencia suas conversas"
  on public.conversations for all
  using (auth.uid() = user_id);

create policy "usuario gerencia suas mensagens"
  on public.messages for all
  using (auth.uid() = user_id);

-- ── Cria o perfil automaticamente quando alguém se cadastra ──
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
as $$
begin
  insert into public.profiles (id, email) values (new.id, new.email);
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- ── Função para contar usuários (usada no painel admin) ──
-- security definer = roda com permissão elevada, retornando só o número (nada sensível)
create or replace function public.contar_usuarios()
returns bigint
language sql
security definer
as $$
  select count(*) from public.profiles;
$$;

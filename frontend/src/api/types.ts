export type Role = 'user' | 'admin'

export type UserOut = {
  id: number
  username: string
  name: string
  email: string | null
  email_verified_at: string | null
  role: Role
  is_active: boolean
  token_limit: number
  created_at: string
}

export type AdminUserOut = UserOut & {
  month_used: number
  session_count: number
}

export type SessionOut = {
  id: number
  title: string
  model_code: string
  preset: string
  created_at: string
  updated_at: string
  message_count: number
}

export type MessageOut = {
  id: number
  session_id: number
  role: 'user' | 'assistant'
  content: string
  status: 'ok' | 'error'
  error_code: string | null
  model_code: string | null
  input_tokens: number
  output_tokens: number
  billed_tokens: number
  latency_ms: number | null
  created_at: string
}

export type ChatLogItem = {
  id: number
  session_id: number
  session_title: string
  question: string
  answer: string | null
  status: 'ok' | 'error'
  error_code: string | null
  model_code: string | null
  billed_tokens: number
  created_at: string
}

export type ChatLogPage = {
  items: ChatLogItem[]
  total: number
}

export type AdminChatLogPage = {
  items: (ChatLogItem & { username: string; name: string })[]
  total: number
}

export type UsageOut = {
  month_used: number
  token_limit: number
  remaining: number
}

export type ModelOut = {
  code: string
  name: string
  provider: string
  multiplier: number
  is_default: boolean
}

export type AdminModelOut = {
  code: string
  name: string
  provider: string
  multiplier: number
  max_tokens: number
  is_active: boolean
  is_default: boolean
  sort_order: number
}

export type DailyUsage = {
  date: string
  model_code: string
  billed_tokens: number
  requests: number
}

export type PresetOut = {
  code: string
  name: string
  description: string
}

export type ChatResponse = {
  session_id: number
  user_message: MessageOut
  assistant_message: MessageOut
  usage: UsageOut
}

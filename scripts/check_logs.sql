-- 사용자별 최근 대화 (사용자마다 최근 5건)
WITH paired AS (
    SELECT
        m.id,
        m.user_id,
        m.session_id,
        m.role,
        m.content,
        m.error_code,
        m.created_at,
        LEAD(m.id) OVER (PARTITION BY m.session_id ORDER BY m.id) AS next_id
    FROM messages m
),
chats AS (
    SELECT
        u.username,
        s.title AS session_title,
        q.content AS question,
        a.content AS answer,
        CASE WHEN a.id IS NULL THEN 'error' ELSE a.status END AS status,
        COALESCE(a.error_code, q.error_code) AS error_code,
        q.created_at,
        ROW_NUMBER() OVER (PARTITION BY q.user_id ORDER BY q.created_at DESC, q.id DESC) AS rn
    FROM paired q
    JOIN users u ON u.id = q.user_id
    JOIN chat_sessions s ON s.id = q.session_id
    LEFT JOIN messages a ON a.id = q.next_id AND a.role = 'assistant'
    WHERE q.role = 'user'
)
SELECT username, session_title, question, answer, status, error_code, created_at
FROM chats
WHERE rn <= 5
ORDER BY username, created_at DESC;

-- 사용자별 질문 건수와 토큰 합계
SELECT
    u.username,
    COUNT(m.id) FILTER (WHERE m.role = 'user') AS questions,
    COUNT(m.id) FILTER (WHERE m.status = 'error') AS errors,
    COALESCE(SUM(m.input_tokens + m.output_tokens), 0) AS tokens,
    COALESCE(SUM(m.billed_tokens), 0) AS billed_tokens
FROM users u
LEFT JOIN messages m ON m.user_id = u.id
GROUP BY u.id, u.username
ORDER BY billed_tokens DESC, u.username;

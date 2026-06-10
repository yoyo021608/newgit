## users 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| username | VARCHAR(50) | 用户名 |
| created_at | DATETIME | 创建时间 |

## agent 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| name | VARCHAR(50) | 名称 |
| created_at | DATETIME | 创建时间 |

## sessions 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| user_id | INT | 用户ID |
| agent_id | INT | Agent ID |
| created_at | DATETIME | 创建时间 |

## tasks 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| title | VARCHAR(200) | 任务标题 |
| status | VARCHAR(20) | 状态 |
| created_at | DATETIME | 创建时间 |
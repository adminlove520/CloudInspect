# 05 - 服务状态检测

**系统服务运行状态监控模块**

---

## 功能说明

服务状态模块检测主机的服务健康状态，包括：
- 30+ 常见服务监控
- 服务启动/停止状态
- 开机自启配置
- 异常服务告警

---

## 检测的服务列表

### 基础服务

| 服务名 | 说明 | 重要性 |
|---|---|---|
| sshd | SSH 远程连接 | ⭐⭐⭐ |
| crond | 定时任务 | ⭐⭐⭐ |
| firewalld | 防火墙 | ⭐⭐ |
| ufw | UFW 防火墙 | ⭐⭐ |

### 容器服务

| 服务名 | 说明 | 重要性 |
|---|---|---|
| docker | Docker 容器引擎 | ⭐⭐ |
| podman | Podman 容器引擎 | ⭐⭐ |
| containerd | 容器运行时 | ⭐⭐ |

### Web 服务

| 服务名 | 说明 | 重要性 |
|---|---|---|
| nginx | Nginx Web 服务器 | ⭐⭐ |
| httpd | Apache HTTP Server | ⭐⭐ |
| php-fpm | PHP FastCGI | ⭐ |

### 数据库服务

| 服务名 | 说明 | 重要性 |
|---|---|---|
| mysqld | MySQL 数据库 | ⭐⭐⭐ |
| mariadb | MariaDB 数据库 | ⭐⭐⭐ |
| postgresql | PostgreSQL 数据库 | ⭐⭐ |
| redis | Redis 缓存 | ⭐⭐ |
| mongod | MongoDB 数据库 | ⭐⭐ |

### 其他服务

| 服务名 | 说明 | 重要性 |
|---|---|---|
| elasticsearch | ES 搜索引擎 | ⭐⭐ |
| tomcat | Tomcat 应用服务器 | ⭐⭐ |
| kubelet | Kubernetes 节点代理 | ⭐⭐ |
| zabbix-agent | Zabbix 监控代理 | ⭐ |
| prometheus | Prometheus 监控 | ⭐ |
| grafana-server | Grafana 可视化 | ⭐ |
| haproxy | HAProxy 负载均衡 | ⭐ |
| keepalived | Keepalived 高可用 | ⭐ |
| postfix | Postfix 邮件服务 | ⭐ |
| smbd | Samba 文件共享 | ⭐ |
| vsftpd | VSFTPD FTP 服务 | ⭐ |
| named | BIND DNS 服务 | ⭐ |
| ntp / chronyd | 时间同步 | ⭐⭐ |
| snmpd | SNMP 监控服务 | ⭐ |
| rsyncd | Rsync 同步服务 | ⭐ |
| rpcbind | RPC 端口映射 | ⭐ |
| autofs | 自动挂载 | ⭐ |

---

## 检测方法

### systemd 系统

```bash
# 检查服务状态
systemctl is-active nginx

# 检查开机自启
systemctl is-enabled nginx

# 列出所有服务
systemctl list-units --type=service --state=running
```

### SysV Init 系统

```bash
# 检查服务状态
service sshd status

# 检查开机自启
chkconfig --list sshd

# 检查 init.d 脚本
/etc/init.d/sshd status
```

---

## 输出示例

### HTML 报告

```
┌─────────────────────────────────────────┐
│  ⚙️ 服务状态                              │
├─────────────────────────────────────────┤
│  ┌────────┐ ┌────────┐ ┌────────┐       │
│  │ 运行中 │ │ 已停止 │ │ 未找到 │       │
│  │  23    │ │   5    │ │   2    │       │
│  └────────┘ └────────┘ └────────┘       │
│                                         │
│  服务状态详情:                            │
│  ├─ ✓ sshd      running   enabled        │
│  ├─ ✓ crond     running   enabled        │
│  ├─ ✓ firewalld running   enabled        │
│  ├─ ✓ nginx     running   enabled        │
│  ├─ ✓ mysqld    running   enabled        │
│  ├─ ✗ postfix   stopped  enabled         │
│  ├─ ✗ vsftpd    stopped  disabled        │
│  └─ − snmpd     notfound  -              │
└─────────────────────────────────────────┘
```

### JSON 输出

```json
{
  "service": {
    "running": 23,
    "stopped": 5,
    "notfound": 2,
    "services": [
      {"name": "sshd", "status": "active", "enabled": "enabled"},
      {"name": "crond", "status": "active", "enabled": "enabled"},
      {"name": "firewalld", "status": "active", "enabled": "enabled"},
      {"name": "nginx", "status": "active", "enabled": "enabled"},
      {"name": "mysqld", "status": "active", "enabled": "enabled"},
      {"name": "postfix", "status": "inactive", "enabled": "enabled"},
      {"name": "vsftpd", "status": "inactive", "enabled": "disabled"},
      {"name": "snmpd", "status": "notfound", "enabled": "notfound"}
    ],
    "issues": []
  }
}
```

---

## 告警规则

| 规则 | 条件 | 级别 | 说明 |
|---|---|---|---|
| 关键服务停止 | sshd/crond/firewalld 停止 | 严重 | 影响系统安全和功能 |
| 数据库服务停止 | mysqld/mariadb/postgresql 停止 | 警告 | 影响业务 |
| Web 服务停止 | nginx/httpd 停止 | 警告 | 影响网站 |
| 服务异常 | 服务状态未知 | 信息 | 可能未安装 |

---

## 使用场景

### 日常巡检

```bash
./inspect.sh -m routine
# 自动包含服务检测
```

### 查看服务状态

```bash
# 查看所有运行中的服务
systemctl list-units --type=service --state=running

# 查看特定服务
systemctl status nginx

# 查看服务依赖
systemctl list-dependencies nginx
```

### 管理服务

```bash
# 启动服务
systemctl start nginx

# 停止服务
systemctl stop nginx

# 重启服务
systemctl restart nginx

# 设置开机自启
systemctl enable nginx

# 取消开机自启
systemctl disable nginx
```

---

## 故障排查

**Q: 服务状态显示 "unknown"**

```bash
# 检查 systemctl 是否可用
systemctl --version

# 检查服务单元是否存在
systemctl list-unit-files | grep nginx

# 手动检查进程
ps aux | grep nginx
```

**Q: 服务启动失败**

```bash
# 查看服务日志
journalctl -u nginx --no-pager -n 50

# 查看错误信息
systemctl status nginx

# 检查配置文件
nginx -t

# 检查端口占用
ss -tlnp | grep :80
```

**Q: 防火墙服务检测不到**

```bash
# 检查防火墙类型
systemctl is-active firewalld && echo "firewalld"
systemctl is-active ufw && echo "ufw"
iptables -L -n 2>/dev/null && echo "iptables"

# 检查 iptables 规则
iptables -L -n | head -20
```

---

*最后更新: 2026-06-11*
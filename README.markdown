### 准备你自己的.env文件
```bash
redis_url=redis://192.168.0.5:6379/10
sqlite=sqlite+aiosqlite:///./pyforum/data.db
# pg_dsn=postgresql+asyncpg://user:password@127.0.0.1/db
debug=True
```

#### 参考config.py中Settings的字段，也可以直接设置环境变量
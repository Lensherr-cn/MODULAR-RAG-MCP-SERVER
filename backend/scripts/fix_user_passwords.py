"""
修复用户密码脚本
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 先导入所有模型以建立关系
from app.core.database import SessionLocal
from app.models.document import Document
from app.models.chat import Conversation, ChatMessage
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
try:
    users = db.query(User).all()
    print('Existing users:')
    for u in users:
        print(f'  {u.username} (role={u.role}, has_password={bool(u.password_hash)})')

        # 如果用户没有密码，设置默认密码
        if not u.password_hash:
            u.password_hash = get_password_hash('User123!')
            print(f'    -> Set default password: User123!')

    db.commit()
    print('\nPasswords fixed!')
finally:
    db.close()

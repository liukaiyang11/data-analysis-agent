#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序主入口点
"""
import uvicorn
from config.settings import settings

def main():
    """主函数"""
    # 验证配置
    if not settings.validate():
        print("配置验证失败，请检查配置文件")
        return

    # 启动应用
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )

if __name__ == "__main__":
    main()
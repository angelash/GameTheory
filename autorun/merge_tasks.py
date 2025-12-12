#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并近五年任务到主任务文件
"""

import json
from pathlib import Path

def main():
    # 读取现有任务
    tasks_file = Path("autorun/tasks.json")
    if tasks_file.exists():
        with open(tasks_file, "r", encoding="utf-8") as f:
            existing_tasks = json.load(f)
    else:
        existing_tasks = []
    
    # 读取新任务
    new_tasks_file = Path("autorun/tasks_2021_2025.json")
    if not new_tasks_file.exists():
        print(f"错误: {new_tasks_file} 不存在")
        return
    
    with open(new_tasks_file, "r", encoding="utf-8") as f:
        new_tasks = json.load(f)
    
    # 合并任务（避免ID冲突）
    max_existing_id = max([t.get("id", 0) for t in existing_tasks], default=0)
    
    # 合并
    all_tasks = existing_tasks + new_tasks
    
    # 保存
    with open(tasks_file, "w", encoding="utf-8") as f:
        json.dump(all_tasks, f, ensure_ascii=False, indent=2)
    
    print(f"合并完成:")
    print(f"  现有任务: {len(existing_tasks)}")
    print(f"  新任务: {len(new_tasks)}")
    print(f"  总任务: {len(all_tasks)}")
    print(f"  已保存到: {tasks_file}")

if __name__ == "__main__":
    main()


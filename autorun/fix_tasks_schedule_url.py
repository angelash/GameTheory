#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 tasks.json 中缺失的 schedule_url 字段
"""

import json
from pathlib import Path

def main():
    # 读取新任务文件（包含完整的 schedule_url）
    new_tasks_file = Path("autorun/tasks_2021_2025.json")
    with open(new_tasks_file, "r", encoding="utf-8") as f:
        new_tasks = json.load(f)
    
    # 创建新任务的映射（按ID）
    new_tasks_map = {t.get("id"): t for t in new_tasks}
    
    # 读取主任务文件
    tasks_file = Path("autorun/tasks.json")
    with open(tasks_file, "r", encoding="utf-8") as f:
        all_tasks = json.load(f)
    
    # 更新任务
    updated_count = 0
    for task in all_tasks:
        task_id = task.get("id")
        if task_id in new_tasks_map:
            new_task = new_tasks_map[task_id]
            # 更新 schedule_url
            if "schedule_url" in new_task and new_task["schedule_url"]:
                if task.get("schedule_url") != new_task["schedule_url"]:
                    task["schedule_url"] = new_task["schedule_url"]
                    updated_count += 1
    
    # 保存
    with open(tasks_file, "w", encoding="utf-8") as f:
        json.dump(all_tasks, f, ensure_ascii=False, indent=2)
    
    print(f"修复完成:")
    print(f"  更新任务数: {updated_count}")
    print(f"  总任务数: {len(all_tasks)}")
    print(f"  已保存到: {tasks_file}")

if __name__ == "__main__":
    main()


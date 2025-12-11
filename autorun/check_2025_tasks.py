#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查2025年任务完成情况
"""

import json
from pathlib import Path
from collections import defaultdict

TASK_FILE = Path("autorun/tasks.json")

def main():
    print("=" * 70)
    print("2025年任务完成情况检查报告")
    print("=" * 70)
    
    # 加载任务
    with open(TASK_FILE, "r", encoding="utf-8") as f:
        tasks = json.load(f)
    
    # 统计2025年相关任务
    tasks_2025 = [t for t in tasks if "2025" in t.get("title", "")]
    
    print(f"\n总任务数: {len(tasks)}")
    print(f"2025年相关任务: {len(tasks_2025)}")
    
    # 按状态统计
    status_count = defaultdict(int)
    for t in tasks_2025:
        status = t.get("status", "unknown")
        status_count[status] += 1
    
    print(f"\n任务状态统计:")
    for status, count in sorted(status_count.items()):
        print(f"  {status}: {count}")
    
    # 按会议分类统计
    print(f"\n按会议分类:")
    conferences = {
        "GDC 2025": [],
        "Unreal Fest 2025": [],
        "UWA Day 2025": [],
        "Unite 2025": []
    }
    
    for t in tasks_2025:
        title = t.get("title", "")
        if "GDC 2025" in title:
            conferences["GDC 2025"].append(t)
        elif "Unreal Fest 2025" in title:
            conferences["Unreal Fest 2025"].append(t)
        elif "UWA Day 2025" in title:
            conferences["UWA Day 2025"].append(t)
        elif "Unite 2025" in title:
            conferences["Unite 2025"].append(t)
    
    for conf, conf_tasks in conferences.items():
        done = len([t for t in conf_tasks if t.get("status") == "done"])
        total = len(conf_tasks)
        print(f"  {conf}: {done}/{total} 已完成 ({done*100//total if total > 0 else 0}%)")
    
    # 检查任务类型
    print(f"\n按任务类型分类:")
    content_tasks = [t for t in tasks_2025 if "补充" in t.get("title", "")]
    new_tasks = [t for t in tasks_2025 if "收集" in t.get("title", "") or "创建" in t.get("title", "")]
    
    print(f"  内容补充任务: {len(content_tasks)} (已完成: {len([t for t in content_tasks if t.get('status') == 'done'])})")
    print(f"  新建文档任务: {len(new_tasks)} (已完成: {len([t for t in new_tasks if t.get('status') == 'done'])})")
    
    # 检查实际文档完成情况
    print(f"\n实际文档完成情况（对比计划）:")
    print(f"  注意：任务完成 ≠ 文档收集完成")
    print(f"  任务完成只表示该任务已被处理，但实际文档数量可能未达到目标")
    
    # 检查是否有待处理的任务
    pending = [t for t in tasks_2025 if t.get("status") == "pending"]
    in_progress = [t for t in tasks_2025 if t.get("status") == "in_progress"]
    
    if pending:
        print(f"\n⚠ 待处理任务 ({len(pending)} 个):")
        for t in pending[:5]:
            print(f"  - ID {t['id']}: {t.get('title', 'N/A')[:60]}")
        if len(pending) > 5:
            print(f"  ... 还有 {len(pending) - 5} 个")
    
    if in_progress:
        print(f"\n⚠ 进行中任务 ({len(in_progress)} 个):")
        for t in in_progress[:5]:
            print(f"  - ID {t['id']}: {t.get('title', 'N/A')[:60]}")
        if len(in_progress) > 5:
            print(f"  ... 还有 {len(in_progress) - 5} 个")
    
    # 总结
    all_done = all(t.get("status") == "done" for t in tasks_2025)
    
    print(f"\n" + "=" * 70)
    if all_done:
        print("✅ 所有2025年任务都已标记为完成")
        print("\n但请注意：")
        print("  1. 任务完成 ≠ 文档收集完成")
        print("  2. 很多任务是'新建文档'任务，实际文档可能还未创建")
        print("  3. 建议检查实际文档数量是否达到计划目标")
        print("\n建议：")
        print("  - 查看 docs/collection-plan-2025-final-status.md 了解实际文档数量")
        print("  - 对比计划目标，确认是否需要继续收集")
    else:
        print("⚠ 还有未完成的2025年任务")
        print(f"  待处理: {len(pending)} 个")
        print(f"  进行中: {len(in_progress)} 个")
    print("=" * 70)

if __name__ == "__main__":
    main()


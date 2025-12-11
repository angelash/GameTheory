#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 Orchestrator 状态
"""

import json
from pathlib import Path
from datetime import datetime

TASK_FILE = Path("autorun/tasks.json")
INPUT_DIR = Path("cursor_workspace/input")
OUTPUT_DIR = Path("cursor_workspace/output")

def main():
    print("=" * 60)
    print("Orchestrator 状态检查")
    print("=" * 60)
    
    # 检查任务状态
    if TASK_FILE.exists():
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        
        status_count = {}
        for t in tasks:
            status = t.get("status", "unknown")
            status_count[status] = status_count.get(status, 0) + 1
        
        print(f"\n任务状态统计:")
        for status, count in sorted(status_count.items()):
            print(f"  {status}: {count}")
        
        # 检查进行中的任务
        in_progress = [t for t in tasks if t.get("status") == "in_progress"]
        if in_progress:
            print(f"\n进行中的任务 ({len(in_progress)} 个):")
            for t in in_progress[:5]:  # 只显示前5个
                print(f"  - ID {t['id']}: {t.get('title', 'N/A')[:50]}")
            if len(in_progress) > 5:
                print(f"  ... 还有 {len(in_progress) - 5} 个")
    
    # 检查输入文件
    print(f"\n输入目录 ({INPUT_DIR}):")
    if INPUT_DIR.exists():
        input_files = list(INPUT_DIR.glob("batch_*.json"))
        print(f"  批次文件数: {len(input_files)}")
        for f in sorted(input_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            print(f"  - {f.name} (创建时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    else:
        print("  目录不存在")
    
    # 检查输出文件
    print(f"\n输出目录 ({OUTPUT_DIR}):")
    if OUTPUT_DIR.exists():
        output_files = list(OUTPUT_DIR.glob("batch_*.json"))
        print(f"  输出文件数: {len(output_files)}")
        for f in sorted(output_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            print(f"  - {f.name} (创建时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    else:
        print("  目录不存在")
    
    # 检查未匹配的输入文件
    print(f"\n未匹配的批次:")
    if INPUT_DIR.exists() and OUTPUT_DIR.exists():
        input_batches = {f.stem for f in INPUT_DIR.glob("batch_*.json")}
        output_batches = {f.stem for f in OUTPUT_DIR.glob("batch_*.json")}
        unmatched = input_batches - output_batches
        if unmatched:
            print(f"  未处理的批次 ({len(unmatched)} 个):")
            for batch_name in sorted(unmatched):
                print(f"  - {batch_name}.json")
        else:
            print("  所有批次都已处理")
    
    print("\n" + "=" * 60)
    print("建议:")
    print("1. 如果有未处理的批次，在 Cursor 中运行 @cursor-worker 处理")
    print("2. 如果 Orchestrator 已停止，重新运行: python autorun/orchestrator.py")
    print("3. 如果任务卡在 in_progress，可以手动检查并更新状态")
    print("=" * 60)

if __name__ == "__main__":
    main()


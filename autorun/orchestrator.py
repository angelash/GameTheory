#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator - 任务队列管理和文件协调服务

负责：
- 从任务池中挑选待处理任务
- 将任务写入 Cursor 工程的 input 目录
- 监控 Cursor 输出目录
- 更新任务状态
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 配置常量
# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "autorun" else SCRIPT_DIR

TASK_FILE = PROJECT_ROOT / "autorun" / "tasks.json"
CURSOR_INPUT_DIR = PROJECT_ROOT / "cursor_workspace" / "input"
CURSOR_OUTPUT_DIR = PROJECT_ROOT / "cursor_workspace" / "output"
ARCHIVE_DIR = PROJECT_ROOT / "cursor_workspace" / "archive"

BATCH_SIZE = 20
POLL_INTERVAL = 10  # 秒
OUTPUT_TIMEOUT = 3600  # 秒（1小时）


def load_tasks() -> List[Dict]:
    """加载任务池"""
    if not TASK_FILE.exists():
        print(f"任务文件不存在: {TASK_FILE}")
        return []
    
    with open(TASK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tasks(tasks: List[Dict]):
    """保存任务池"""
    TASK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def pick_batch(tasks: List[Dict], batch_size: int) -> List[Dict]:
    """挑选一批待处理任务（按优先级排序）"""
    pending = [t for t in tasks if t.get("status") == "pending"]
    # 按 priority 排序（数字越小优先级越高）
    pending.sort(key=lambda x: x.get("priority", 999))
    return pending[:batch_size]


def mark_in_progress(tasks: List[Dict], batch: List[Dict]):
    """标记任务为进行中"""
    ids = {t["id"] for t in batch}
    for t in tasks:
        if t["id"] in ids:
            t["status"] = "in_progress"
            t["started_at"] = datetime.now().isoformat()


def mark_done(tasks: List[Dict], batch: List[Dict]):
    """标记任务为完成"""
    ids = {t["id"] for t in batch}
    for t in tasks:
        if t["id"] in ids:
            t["status"] = "done"
            t["completed_at"] = datetime.now().isoformat()


def mark_failed(tasks: List[Dict], batch: List[Dict], reason: str = ""):
    """标记任务为失败"""
    ids = {t["id"] for t in batch}
    for t in tasks:
        if t["id"] in ids:
            t["status"] = "failed"
            t["failed_at"] = datetime.now().isoformat()
            if reason:
                t["failure_reason"] = reason


def write_input_file(batch: List[Dict], batch_name: str) -> Path:
    """将批次任务写入输入文件"""
    CURSOR_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    input_path = CURSOR_INPUT_DIR / f"{batch_name}.json"
    
    batch_data = {
        "batch_name": batch_name,
        "created_at": datetime.now().isoformat(),
        "tasks": batch
    }
    
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(batch_data, f, ensure_ascii=False, indent=2)
    
    return input_path


def wait_for_output(batch_name: str, timeout: int = OUTPUT_TIMEOUT) -> Optional[Path]:
    """等待输出文件出现"""
    CURSOR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 支持 .json 和 .md 两种输出格式
    output_paths = [
        CURSOR_OUTPUT_DIR / f"{batch_name}.json",
        CURSOR_OUTPUT_DIR / f"{batch_name}.md"
    ]
    
    start = time.time()
    while time.time() - start < timeout:
        for output_path in output_paths:
            if output_path.exists():
                return output_path
        time.sleep(POLL_INTERVAL)
    
    return None


def parse_output(output_path: Path) -> Optional[Dict]:
    """解析输出文件"""
    try:
        if output_path.suffix == ".json":
            with open(output_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # Markdown 格式，返回原始内容
            with open(output_path, "r", encoding="utf-8") as f:
                return {"content": f.read(), "format": "markdown"}
    except Exception as e:
        print(f"解析输出文件失败: {e}")
        return None


def archive_output(output_path: Path, batch_name: str):
    """归档输出文件到存档目录"""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    archive_path = ARCHIVE_DIR / output_path.name
    if output_path.exists():
        import shutil
        shutil.copy2(output_path, archive_path)
        print(f"已归档到: {archive_path}")


def main_loop():
    """主循环"""
    print("=" * 60)
    print("Orchestrator 启动")
    print(f"任务文件: {TASK_FILE}")
    print(f"输入目录: {CURSOR_INPUT_DIR}")
    print(f"输出目录: {CURSOR_OUTPUT_DIR}")
    print("=" * 60)
    
    iteration = 0
    while True:
        iteration += 1
        print(f"\n[迭代 {iteration}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 加载任务
        tasks = load_tasks()
        if not tasks:
            print("任务池为空，等待 60 秒后重试...")
            time.sleep(60)
            continue
        
        # 统计任务状态
        status_count = {}
        for t in tasks:
            status = t.get("status", "unknown")
            status_count[status] = status_count.get(status, 0) + 1
        print(f"任务状态统计: {status_count}")
        
        # 挑选批次
        batch = pick_batch(tasks, BATCH_SIZE)
        if not batch:
            print("所有任务已完成！")
            break
        
        print(f"挑选了 {len(batch)} 个任务")
        
        # 生成批次名称
        batch_name = f"batch_{int(time.time())}"
        
        # 标记为进行中
        mark_in_progress(tasks, batch)
        save_tasks(tasks)
        
        # 写入输入文件
        input_file = write_input_file(batch, batch_name)
        print(f"✓ 已写入输入文件: {input_file}")
        print(f"  包含任务: {[t['id'] for t in batch]}")
        print("\n" + "=" * 60)
        print("请在 Cursor 中运行 Worker 角色处理这一批任务...")
        print("  激活方式: @cursor-worker")
        print("  或使用: action('cursor-worker')")
        print("=" * 60)
        
        # 等待输出
        print(f"\n等待输出文件（超时: {OUTPUT_TIMEOUT}秒）...")
        output_file = wait_for_output(batch_name, OUTPUT_TIMEOUT)
        
        if output_file is None:
            print("⚠ 等待输出超时！")
            print("  可能原因：")
            print("  1. Cursor Worker 尚未处理")
            print("  2. 处理时间超过超时限制")
            print("  3. 输出文件名不匹配")
            print("\n选择操作：")
            print("  [1] 回滚任务状态为 pending（重新处理）")
            print("  [2] 标记为 failed（跳过）")
            print("  [3] 继续等待（手动检查）")
            
            # 默认回滚
            choice = input("请输入选择 (1/2/3，默认1): ").strip() or "1"
            if choice == "1":
                for t in tasks:
                    if t["id"] in {b["id"] for b in batch}:
                        t["status"] = "pending"
                        if "started_at" in t:
                            del t["started_at"]
                save_tasks(tasks)
                print("✓ 已回滚任务状态")
            elif choice == "2":
                mark_failed(tasks, batch, "输出超时")
                save_tasks(tasks)
                print("✓ 已标记为失败")
            else:
                print("继续等待，请手动检查...")
            continue
        
        # 解析输出
        print(f"✓ 检测到输出文件: {output_file}")
        output_data = parse_output(output_file)
        if output_data:
            print(f"  输出格式: {output_data.get('format', 'json')}")
        
        # 归档输出
        archive_output(output_file, batch_name)
        
        # 标记完成
        mark_done(tasks, batch)
        save_tasks(tasks)
        print(f"✓ 已标记 {len(batch)} 个任务为完成")
        
        # 短暂休息
        time.sleep(5)
    
    print("\n" + "=" * 60)
    print("所有任务处理完成！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n\n用户中断，退出...")
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback
        traceback.print_exc()


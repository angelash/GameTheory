#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新任务状态脚本
根据输出目录中的批次结果更新tasks.json中的任务状态
"""

import json
from pathlib import Path
from datetime import datetime

def main():
    # 路径
    task_file = Path('autorun/tasks.json')
    output_dir = Path('cursor_workspace/output')
    
    # 读取任务
    with open(task_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    # 读取所有输出文件
    processed_ids = set()
    task_status_map = {}
    
    for output_file in output_dir.glob('batch_*.json'):
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for result in data.get('results', []):
                task_id = result['id']
                processed_ids.add(task_id)
                status = result.get('status', 'partial')
                # 将success映射为done
                if status == 'success':
                    status = 'done'
                task_status_map[task_id] = status
    
    # 更新任务状态
    updated_count = 0
    for task in tasks:
        task_id = task['id']
        if task_id in task_status_map:
            old_status = task.get('status', 'pending')
            new_status = task_status_map[task_id]
            if old_status in ['in_progress', 'pending'] and new_status in ['done', 'partial', 'skipped']:
                task['status'] = new_status
                if 'started_at' in task:
                    del task['started_at']
                if new_status == 'done':
                    task['completed_at'] = datetime.now().isoformat()
                updated_count += 1
    
    # 保存更新后的任务
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    # 统计
    status_count = {}
    for t in tasks:
        s = t.get('status', 'pending')
        status_count[s] = status_count.get(s, 0) + 1
    
    print(f'任务状态已更新! 共更新 {updated_count} 个任务')
    print('\n当前任务状态统计:')
    for s, c in sorted(status_count.items()):
        print(f'  {s}: {c}')
    
    # 年份统计
    year_stats = {}
    for t in tasks:
        title = t.get('title', '')
        for year in ['2021', '2022', '2023', '2024', '2025']:
            if year in title:
                if year not in year_stats:
                    year_stats[year] = {'total': 0, 'done': 0, 'partial': 0, 'pending': 0, 'skipped': 0}
                year_stats[year]['total'] += 1
                status = t.get('status', 'pending')
                if status in year_stats[year]:
                    year_stats[year][status] += 1
                break
    
    print('\n按年份统计:')
    for year in sorted(year_stats.keys()):
        stats = year_stats[year]
        print(f'  {year}: 总数={stats["total"]}, 完成={stats["done"]}, 部分={stats["partial"]}, 待处理={stats["pending"]}, 跳过={stats["skipped"]}')

if __name__ == '__main__':
    main()


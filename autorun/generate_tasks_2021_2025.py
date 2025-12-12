#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成近五年（2021-2025）会议资料收集任务
按照新规范：每个任务最多5个文档，推荐1个
"""

import json
from pathlib import Path
from typing import List, Dict

# 配置
MAX_DOCUMENTS_PER_TASK = 5
RECOMMENDED_DOCUMENTS_PER_TASK = 1

# 目录路径
BASE_DIR = Path("docs")
GDC_DIR = BASE_DIR / "gdc" / "talks"
UNREAL_FEST_DIR = BASE_DIR / "unreal-fest" / "talks"
UNITE_DIR = BASE_DIR / "unite" / "talks"
UWA_DAY_DIR = BASE_DIR / "uwa-day" / "talks"

# 任务ID起始值（避免与现有任务冲突）
START_ID = 1000


def get_existing_documents(year: int, conference: str) -> List[str]:
    """获取已存在的文档列表"""
    if conference == "gdc":
        dir_path = GDC_DIR / str(year)
    elif conference == "unreal-fest":
        dir_path = UNREAL_FEST_DIR / str(year)
    elif conference == "unite":
        dir_path = UNITE_DIR / str(year)
    elif conference == "uwa-day":
        dir_path = UWA_DAY_DIR / str(year)
    else:
        return []
    
    if not dir_path.exists():
        return []
    
    return [str(f.relative_to(BASE_DIR.parent)) for f in dir_path.glob("*.md")]


def create_content_supplement_tasks(documents: List[str], base_id: int, priority: int, year: int, conference: str) -> List[Dict]:
    """创建内容补充任务"""
    tasks = []
    task_id = base_id
    
    # 按推荐粒度分组（每个任务1个文档）
    for i in range(0, len(documents), RECOMMENDED_DOCUMENTS_PER_TASK):
        batch = documents[i:i + RECOMMENDED_DOCUMENTS_PER_TASK]
        if not batch:
            continue
        
        # 生成任务标题
        if len(batch) == 1:
            doc_name = Path(batch[0]).stem
            title = f"补充{conference.upper()} {year}演讲内容 - {doc_name}"
        else:
            title = f"补充{conference.upper()} {year}演讲内容（{len(batch)}个文档）"
        
        task = {
            "id": task_id,
            "type": "content_supplement",
            "title": title,
            "status": "pending",
            "priority": priority,
            "description": f"补充{conference.upper()} {year}年{len(batch)}个演讲的资源链接、详细内容和关键要点",
            "target_files": batch
        }
        
        tasks.append(task)
        task_id += 1
    
    return tasks


def create_document_tasks(year: int, conference: str, base_id: int, priority: int, 
                         estimated_count: int, requires_permission: bool = False) -> List[Dict]:
    """创建新建文档任务"""
    tasks = []
    task_id = base_id
    
    if requires_permission:
        # 需要特殊权限，创建skipped任务
        schedule_url = f"https://schedule.gdconf.com/{year}"
        task = {
            "id": task_id,
            "type": "create_document",
            "title": f"收集{conference.upper()} {year}演讲（需要GDC Vault权限）",
            "status": "skipped",
            "priority": 5,
            "description": f"收集{conference.upper()} {year}年演讲，需要GDC Vault账号访问完整视频和PPT",
            "requires_permission": True,
            "reason": "需要GDC Vault账号访问完整视频和PPT",
            "target_count": estimated_count,
            "schedule_url": schedule_url,
            "search_keywords": f"{conference.upper()} {year} schedule talks"
        }
        tasks.append(task)
    else:
        # 不需要特殊权限，创建正常任务
        # 按批次拆分（每个任务最多5个文档）
        batch_size = MAX_DOCUMENTS_PER_TASK
        num_batches = (estimated_count + batch_size - 1) // batch_size
        
        for i in range(num_batches):
            batch_start = i * batch_size + 1
            batch_end = min((i + 1) * batch_size, estimated_count)
            batch_count = batch_end - batch_start + 1
            
            # 生成schedule_url（根据会议类型）
            schedule_url = ""
            if conference == "gdc":
                schedule_url = f"https://schedule.gdconf.com/{year}"
            elif conference == "unreal-fest":
                schedule_url = f"https://www.unrealengine.com/en-US/events/unreal-fest-{year}"
            elif conference == "unite":
                schedule_url = f"https://unity.com/events/unite-{year}"
            elif conference == "uwa-day":
                schedule_url = f"https://www.uwa4d.com/uwa-day-{year}"
            
            task = {
                "id": task_id,
                "type": "create_document",
                "title": f"收集{conference.upper()} {year}演讲（{batch_start}-{batch_end}/{estimated_count}）",
                "status": "pending",
                "priority": priority,
                "description": f"收集{conference.upper()} {year}年第{batch_start}-{batch_end}个演讲，共{batch_count}个",
                "target_count": batch_count,
                "schedule_url": schedule_url,
                "search_keywords": f"{conference.upper()} {year} schedule talks"
            }
            
            tasks.append(task)
            task_id += 1
    
    return tasks


def generate_gdc_tasks() -> List[Dict]:
    """生成GDC任务"""
    tasks = []
    task_id = START_ID
    
    # GDC 2025 - 内容补充（已有94个文档框架）
    gdc_2025_docs = get_existing_documents(2025, "gdc")
    if gdc_2025_docs:
        supplement_tasks = create_content_supplement_tasks(
            gdc_2025_docs, task_id, priority=1, year=2025, conference="gdc"
        )
        tasks.extend(supplement_tasks)
        task_id += len(supplement_tasks)
    
    # GDC 2024 - 新建文档（需要GDC Vault权限）
    tasks.extend(create_document_tasks(
        2024, "gdc", task_id, priority=2, estimated_count=50, requires_permission=True
    ))
    task_id += 1
    
    # GDC 2023 - 新建文档（需要GDC Vault权限）
    tasks.extend(create_document_tasks(
        2023, "gdc", task_id, priority=3, estimated_count=50, requires_permission=True
    ))
    task_id += 1
    
    # GDC 2022 - 新建文档（需要GDC Vault权限）
    tasks.extend(create_document_tasks(
        2022, "gdc", task_id, priority=4, estimated_count=50, requires_permission=True
    ))
    task_id += 1
    
    # GDC 2021 - 新建文档（需要GDC Vault权限）
    tasks.extend(create_document_tasks(
        2021, "gdc", task_id, priority=4, estimated_count=50, requires_permission=True
    ))
    task_id += 1
    
    return tasks


def generate_unreal_fest_tasks() -> List[Dict]:
    """生成Unreal Fest任务"""
    tasks = []
    task_id = START_ID + 200
    
    # Unreal Fest 2025 - 内容补充（已有15个文档框架）
    uf_2025_docs = get_existing_documents(2025, "unreal-fest")
    if uf_2025_docs:
        supplement_tasks = create_content_supplement_tasks(
            uf_2025_docs, task_id, priority=2, year=2025, conference="unreal-fest"
        )
        tasks.extend(supplement_tasks)
        task_id += len(supplement_tasks)
    
    # Unreal Fest 2024 - 新建文档
    tasks.extend(create_document_tasks(
        2024, "unreal-fest", task_id, priority=3, estimated_count=30, requires_permission=False
    ))
    task_id += 1
    
    # Unreal Fest 2023 - 新建文档
    tasks.extend(create_document_tasks(
        2023, "unreal-fest", task_id, priority=3, estimated_count=30, requires_permission=False
    ))
    task_id += 1
    
    # Unreal Fest 2022 - 新建文档
    tasks.extend(create_document_tasks(
        2022, "unreal-fest", task_id, priority=4, estimated_count=30, requires_permission=False
    ))
    task_id += 1
    
    # Unreal Fest 2021 - 新建文档
    tasks.extend(create_document_tasks(
        2021, "unreal-fest", task_id, priority=4, estimated_count=30, requires_permission=False
    ))
    task_id += 1
    
    return tasks


def generate_unite_tasks() -> List[Dict]:
    """生成Unite任务"""
    tasks = []
    task_id = START_ID + 300
    
    # Unite 2025 - 内容补充（已有5个文档框架）
    unite_2025_docs = get_existing_documents(2025, "unite")
    if unite_2025_docs:
        supplement_tasks = create_content_supplement_tasks(
            unite_2025_docs, task_id, priority=2, year=2025, conference="unite"
        )
        tasks.extend(supplement_tasks)
        task_id += len(supplement_tasks)
    
    # Unite 2024 - 新建文档
    tasks.extend(create_document_tasks(
        2024, "unite", task_id, priority=3, estimated_count=20, requires_permission=False
    ))
    task_id += 1
    
    # Unite 2023 - 新建文档
    tasks.extend(create_document_tasks(
        2023, "unite", task_id, priority=4, estimated_count=20, requires_permission=False
    ))
    task_id += 1
    
    # Unite 2022 - 新建文档
    tasks.extend(create_document_tasks(
        2022, "unite", task_id, priority=4, estimated_count=20, requires_permission=False
    ))
    task_id += 1
    
    # Unite 2021 - 新建文档
    tasks.extend(create_document_tasks(
        2021, "unite", task_id, priority=4, estimated_count=20, requires_permission=False
    ))
    task_id += 1
    
    return tasks


def generate_uwa_day_tasks() -> List[Dict]:
    """生成UWA Day任务"""
    tasks = []
    task_id = START_ID + 400
    
    # UWA Day 2025 - 内容补充（已有9个文档框架）
    uwa_2025_docs = get_existing_documents(2025, "uwa-day")
    if uwa_2025_docs:
        supplement_tasks = create_content_supplement_tasks(
            uwa_2025_docs, task_id, priority=2, year=2025, conference="uwa-day"
        )
        tasks.extend(supplement_tasks)
        task_id += len(supplement_tasks)
    
    # UWA Day 2024 - 新建文档
    tasks.extend(create_document_tasks(
        2024, "uwa-day", task_id, priority=3, estimated_count=15, requires_permission=False
    ))
    task_id += 1
    
    # UWA Day 2023 - 新建文档
    tasks.extend(create_document_tasks(
        2023, "uwa-day", task_id, priority=4, estimated_count=15, requires_permission=False
    ))
    task_id += 1
    
    # UWA Day 2022 - 新建文档
    tasks.extend(create_document_tasks(
        2022, "uwa-day", task_id, priority=4, estimated_count=15, requires_permission=False
    ))
    task_id += 1
    
    # UWA Day 2021 - 新建文档
    tasks.extend(create_document_tasks(
        2021, "uwa-day", task_id, priority=4, estimated_count=15, requires_permission=False
    ))
    task_id += 1
    
    return tasks


def main():
    """主函数"""
    print("=" * 60)
    print("生成近五年（2021-2025）会议资料收集任务")
    print("=" * 60)
    
    # 生成所有任务
    all_tasks = []
    
    print("\n1. 生成GDC任务...")
    gdc_tasks = generate_gdc_tasks()
    all_tasks.extend(gdc_tasks)
    print(f"   生成 {len(gdc_tasks)} 个GDC任务")
    
    print("\n2. 生成Unreal Fest任务...")
    uf_tasks = generate_unreal_fest_tasks()
    all_tasks.extend(uf_tasks)
    print(f"   生成 {len(uf_tasks)} 个Unreal Fest任务")
    
    print("\n3. 生成Unite任务...")
    unite_tasks = generate_unite_tasks()
    all_tasks.extend(unite_tasks)
    print(f"   生成 {len(unite_tasks)} 个Unite任务")
    
    print("\n4. 生成UWA Day任务...")
    uwa_tasks = generate_uwa_day_tasks()
    all_tasks.extend(uwa_tasks)
    print(f"   生成 {len(uwa_tasks)} 个UWA Day任务")
    
    # 统计
    print("\n" + "=" * 60)
    print("任务统计:")
    print(f"  总任务数: {len(all_tasks)}")
    
    status_count = {}
    for task in all_tasks:
        status = task.get("status", "unknown")
        status_count[status] = status_count.get(status, 0) + 1
    
    print("\n  状态分布:")
    for status, count in status_count.items():
        print(f"    {status}: {count}")
    
    priority_count = {}
    for task in all_tasks:
        priority = task.get("priority", 999)
        priority_count[priority] = priority_count.get(priority, 0) + 1
    
    print("\n  优先级分布:")
    for priority in sorted(priority_count.keys()):
        print(f"    {priority}: {priority_count[priority]}")
    
    # 保存到文件
    output_file = Path("autorun/tasks_2021_2025.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_tasks, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] 任务已保存到: {output_file}")
    print("=" * 60)
    
    return all_tasks


if __name__ == "__main__":
    main()


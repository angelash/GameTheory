#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务验证工具 - 验证任务是否符合规范
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

# 规范常量
MAX_DOCUMENTS_PER_TASK = 5
RECOMMENDED_DOCUMENTS_PER_TASK = 1

TASK_TYPE_REQUIREMENTS = {
    "content_supplement": {
        "required_fields": ["target_files"],
        "optional_fields": ["resource_list", "target_file"]
    },
    "create_document": {
        "required_fields": ["document_list", "schedule_url"],  # 至少一个
        "optional_fields": ["target_count", "search_keywords"]
    },
    "url": {
        "required_fields": ["url"],
        "optional_fields": ["extract_fields"]
    },
    "topic": {
        "required_fields": ["title", "search_keywords"],  # 至少一个
        "optional_fields": ["max_results", "description"]
    },
    "skipped": {
        "required_fields": ["reason"],
        "optional_fields": ["requires_permission"]
    }
}


def validate_task(task: Dict) -> Tuple[bool, List[str]]:
    """验证单个任务是否符合规范"""
    errors = []
    
    # 检查必填字段
    task_type = task.get("type")
    if not task_type:
        errors.append("缺少 type 字段")
        return False, errors
    
    if task_type not in TASK_TYPE_REQUIREMENTS:
        errors.append(f"未知的任务类型: {task_type}")
        return False, errors
    
    requirements = TASK_TYPE_REQUIREMENTS[task_type]
    
    # 检查必填字段（至少满足一个）
    if task_type in ["create_document", "topic"]:
        # 这些类型需要至少一个必填字段
        has_required = any(task.get(field) for field in requirements["required_fields"])
        if not has_required:
            errors.append(f"任务类型 {task_type} 需要至少一个必填字段: {requirements['required_fields']}")
    else:
        # 其他类型需要所有必填字段
        for field in requirements["required_fields"]:
            if field not in task or not task[field]:
                errors.append(f"缺少必填字段: {field}")
    
    # 检查任务粒度
    if task_type == "content_supplement":
        target_files = task.get("target_files", [])
        if isinstance(target_files, list):
            if len(target_files) > MAX_DOCUMENTS_PER_TASK:
                errors.append(f"任务包含 {len(target_files)} 个文档，超过最大限制 {MAX_DOCUMENTS_PER_TASK}，必须拆分")
            elif len(target_files) > RECOMMENDED_DOCUMENTS_PER_TASK:
                errors.append(f"警告：任务包含 {len(target_files)} 个文档，推荐拆分为单个文档任务")
    
    # 检查状态一致性
    if task.get("requires_permission") and task.get("status") != "skipped":
        errors.append("需要特殊权限的任务必须标记为 skipped")
    
    # 检查优先级
    priority = task.get("priority", 999)
    if not isinstance(priority, int) or priority < 1 or priority > 5:
        errors.append(f"优先级必须在 1-5 之间，当前: {priority}")
    
    return len(errors) == 0, errors


def validate_task_file(task_file: Path) -> Tuple[bool, Dict]:
    """验证整个任务文件"""
    if not task_file.exists():
        return False, {"error": "任务文件不存在"}
    
    try:
        with open(task_file, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    except json.JSONDecodeError as e:
        return False, {"error": f"JSON格式错误: {e}"}
    
    results = {
        "total": len(tasks),
        "valid": 0,
        "invalid": 0,
        "errors": []
    }
    
    for task in tasks:
        is_valid, errors = validate_task(task)
        if is_valid:
            results["valid"] += 1
        else:
            results["invalid"] += 1
            results["errors"].append({
                "id": task.get("id"),
                "title": task.get("title", "N/A"),
                "errors": errors
            })
    
    return results["invalid"] == 0, results


def main():
    """主函数"""
    import sys
    
    task_file = Path("autorun/tasks.json")
    
    if len(sys.argv) > 1:
        task_file = Path(sys.argv[1])
    
    print("=" * 60)
    print("任务验证工具")
    print("=" * 60)
    print(f"\n验证文件: {task_file}")
    
    is_valid, results = validate_task_file(task_file)
    
    if is_valid:
        print(f"\n[OK] 所有任务验证通过！")
        print(f"  总任务数: {results['total']}")
        print(f"  有效任务: {results['valid']}")
    else:
        print(f"\n[WARN] 发现 {results['invalid']} 个无效任务")
        print(f"  总任务数: {results['total']}")
        print(f"  有效任务: {results['valid']}")
        print(f"  无效任务: {results['invalid']}")
        
        print(f"\n错误详情:")
        for error_info in results["errors"]:
            print(f"\n  任务 ID {error_info['id']}: {error_info.get('title', 'N/A')}")
            for error in error_info['errors']:
                print(f"    - {error}")
    
    print("\n" + "=" * 60)
    
    return 0 if is_valid else 1


if __name__ == "__main__":
    exit(main())


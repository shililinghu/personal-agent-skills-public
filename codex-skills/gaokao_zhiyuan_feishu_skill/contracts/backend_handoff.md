# 后端交接约定：单用户飞书档案包

## 目标

Skill 负责分析、整理和生成结构化 payload；后端负责调用飞书开放平台 API，创建单用户档案包并写入文档/多维表格。

## 标准流程

1. Skill 收集用户信息并生成 `feishu_archive_payload`。
2. 后端接收 payload。
3. 后端创建或复制一个飞书文件夹/模板，作为该用户独立档案包。
4. 后端创建/复制以下内容：
   - 志愿填报决策报告文档
   - 定位方法选择说明表
   - 候选院校表
   - 专业理解表
   - 联网检索任务表
   - 可选信息来源清单
   - 证据来源表
   - 风险审查表
   - AI 信息整理表
   - 用户评分表
   - 权重与汇总表
   - 最终志愿方案表
   - 版本记录表
5. 后端把 payload 分别写入对应文档和表格。
6. 后端设置权限：默认仅用户本人或授权对象可见。
7. 后端返回档案包链接、文档链接和表格链接。

## 后端返回建议

```json
{
  "consult_id": "A023",
  "archive_title": "2025志愿档案包｜咨询编号A023",
  "status": "created",
  "folder_url": "",
  "report_doc_url": "",
  "tables": {
    "positioning_method_rationale": "",
    "candidate_schools": "",
    "major_cards": "",
    "research_tasks": "",
    "source_candidates": "",
    "evidence_sources": "",
    "risk_checks": "",
    "volunteer_plan": "",
    "research_cards": "",
    "user_score_records": "",
    "score_summary": "",
    "version_records": ""
  },
  "permission": {
    "visibility": "authorized_people_only",
    "authorized_recipients": []
  }
}
```

## 隐私要求

- 不创建包含多个考生详细信息的公共总表。
- 后台索引表最多保存咨询编号、档案包链接、创建时间、当前版本、咨询状态。
- 分享前必须确认授权对象。
- 默认不要开启公开链接。
- 删除或归档时，应按单用户档案包处理。

## 错误处理

如果飞书写入失败，后端应返回：

- 哪一步失败
- 是否已创建部分文件
- 是否可重试
- 用户是否需要重新授权
- 原始 payload 是否已安全保存

Skill 回复时不得声称“已经创建成功”，除非后端明确返回成功状态。

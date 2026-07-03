---
title: 系統工程導航總覽 (README)
version: 0.1.0
status: Approved
last_updated: "2026-06-29"
---

# 系統工程導航總覽 (SE Navigation Overview)

本目錄是專案 **`Wisdom Weaving`** 的系統工程 (System Engineering, SE) 治理核心。所有關於本產品的「需求、規格、設計、實作、驗證與釋出」之 Living Documents 皆集中管理於此，作為本專案的 **單一事實來源 (Single Source of Truth, SSOT)**。

---

## 系統工程成熟度看板 (Maturity Dashboard)

| 範疇 (Domain) | 核心文件 | 當前狀態 (Status) | 最後更新日期 | 備註 |
| :--- | :--- | :---: | :---: | :--- |
| **01_Requirements** | [req_vision.md](file:///./01_requirements/req_vision.md) | `[Draft]` | `2026-06-29` | 產品願景與核心需求定義 |
| **02_Specification** | [spec_functional.md](file:///./02_specification/spec_functional.md) | `[Draft]` | `2026-06-29` | 功能與非功能規格 |
| **03_Design** | [architecture.md](file:///./03_design/architecture.md) | `[Draft]` | `2026-06-29` | 系統架構與模組設計 |
| **04_Implementation** | [impl_notes.md](file:///./04_implementation/impl_notes.md) | `[Draft]` | `2026-06-29` | 實作決策與技術債紀錄 |
| **05_Verification** | [test_plan.md](file:///./05_verification_testing/test_plan.md) | `[Draft]` | `2026-06-29` | 測試計畫與驗證紀錄 |
| **06_Release** | [changelog.md](file:///./06_release_operations/changelog.md) | `[Draft]` | `2026-06-29` | 釋出指南與變更日誌 |

> [!NOTE]
> * **狀態說明**：`[Draft]` (草案中) $\rightarrow$ `[In Review]` (審查中) $\rightarrow$ `[Approved]` (已核准) $\rightarrow$ `[Deprecated]` (已廢棄)。
> * 每次更新文件時，請一併更新此處與各文檔 YAML Header 中的 `status` 與 `last_updated` 屬性。

---

## 當前里程碑與系統地圖

### 系統工程聯絡資訊
* 系統工程治理者：`wuulong`
* AI Agent 協作狀態：已啟用 `system-engineer-navigator` 技能

---
title: 系統工程導航總覽 (README)
version: 0.1.1
status: Approved
last_updated: "2026-07-04"
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

---

## 4. 快捷開發與自檢指令 (Just Commands Guide)

為了降低開發、自檢與實驗階段的命令列輸入摩擦，本專案在子目錄根路徑下配置了 `justfile`。實驗者可以使用 `just` 快捷指令來簡化多資料庫運行流程：

*   **一鍵初始化並載入文本**
    ```bash
    # 預設：動態建立預設資料庫並載入無版權模擬文本
    just init
    
    # 進階：在自訂資料庫載入指定的本地文本切片
    just init db=events/wisdom-core/wisdom-weaving/custom.db text=path/to/custom_text.txt
    ```
*   **系統性 JIT 檢索與專題建置**
    ```bash
    # 預設：在預設資料庫執行查詢
    just query "分析資訊隔離與多重身分防穿幫"
    
    # 進階：在指定資料庫範疇下執行查詢
    just query "分析資訊隔離與多重身分防穿幫" db=events/wisdom-core/wisdom-weaving/custom.db
    ```
*   **版權隔離一鍵剝離 (發布前)**
    ```bash
    # 預設：剝離預設資料庫
    just strip
    
    # 進階：剝離指定的資料庫
    just strip db=events/wisdom-core/wisdom-weaving/custom.db
    ```
*   **本地原著對齊還原重建 (地端重建)**
    ```bash
    # 用法：必須指定本地原著文本路徑（db 為可選）
    just restore path/to/local_novel.txt
    just restore path/to/local_novel.txt db=events/wisdom-core/wisdom-weaving/custom.db
    ```

---
> **當前專案迭代狀態**：`Development Stage (0.1.1)` (版本：`0.1.1`)

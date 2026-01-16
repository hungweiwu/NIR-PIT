# 🧪 模擬符合 IEC 62304 的「受控開發環境」

（以下內容為可直接使用與下載的 Markdown 文件）

---

## 👥 角色設定

- **角色 A：Owner（主管）**  
  - GitHub 帳號：hungweiwu  
  - 職責：專案擁有者、最終核准者

- **角色 B：Reviewer（SCM / 守門員）**  
  - GitHub 帳號：hazzahwwu  
  - 職責：審核 PR、Git 歷史整形、合規檢查

- **角色 C：Author（研發同仁）**  
  - GitHub 帳號：hwwdev  
  - 職責：實作需求、撰寫 Commit、發起 PR

---

# 第一階段：技能與環境建置（SCM 視角）

## 第 1 天：建立三權分立的實驗室

### 帳號準備
- 建立三個 GitHub 帳號（Owner / Reviewer / Author）

### 環境模擬
- Owner 建立專案
- 啟用 Branch Protection Rule
  - main 分支禁止直接 push
  - 需至少 1 位 Reviewer 核准才可合併

### S-BOM 練習
- 建立 `S-BOM.md`
- 盤點 image_registration.py 依賴
  - SimpleITK==2.1.0

### 法規對齊（IEC 62304）
- 現行手動流程 vs 法規要求
- 列出 3 個落差點（追溯性、審核、版本控管）

---

# 第二階段：研發與追溯性實作（RD 視角）

## 第 2 天：完美提交與技術演練

### 任務領取
- 建立 GitHub Issue（例：#2026）
- 模擬 Redmine 領票

### 分支規範
```
git checkout -b UserB_2026
```

### 代碼開發
- 修改 image_registration.py
- 新增 Dice coefficient 或 Affine 變換

### 合規 Commit Message
```
[Problem]
描述現有問題

[Solution]
本次解法說明

[Feature]
新增或修改功能

[Test]
測試方式與結果
```

---

# 第三階段：守門員審核與歷史整形（SCM 視角）

## 第 3 天：Assignee 審查

### 審核 PR
- Reviewer 檢查 PR 與 Issue 一致性

### Git 歷史整形
- git commit --amend
- git rebase -i

### 合規檢查
- Commit / PR / Issue / Test 一致

---

# 第四階段：衝突處理與權限終結（Owner 視角）

## 第 4 天：系統整合

### 衝突模擬
- Reviewer 與 Author 修改同一行
- 手動解衝突

### 最終核准
- Reviewer @Owner 留言核准
- Owner 合併 PR

### Issue 同步
- Issue 狀態改為「已解決」
- 填寫完成日

---

# 第五階段：DHF 轉化與提案準備（SCM 視角）

## 第 5 天：操作轉文件

### DHF 草案
- Git Tag
- 對應 Issue / PR
- 測試證據

### 簡報主題
**提升軟體開發追溯性：  
落實 MR Assignee 審核機制與 Commit 規範**

---

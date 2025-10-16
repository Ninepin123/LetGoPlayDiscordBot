# 📄 Discord Bot 檔案轉換功能

## ✨ 功能說明

當 bot 被 `@提及` 且訊息中包含 Office 文件（.doc, .docx, .pptx）時，會自動將這些檔案轉換成 PDF 格式。

## 🎯 支援的檔案格式

- ✅ `.doc` - Microsoft Word 舊格式
- ✅ `.docx` - Microsoft Word 新格式
- ✅ `.pptx` - Microsoft PowerPoint

## 📋 使用方式

### 步驟 1：上傳檔案並提及 bot

在 Discord 頻道中：

1. 點擊附件按鈕上傳檔案（.doc, .docx, 或 .pptx）
2. 在訊息中輸入 `@Bot名稱`（提及你的 bot）
3. 送出訊息

### 步驟 2：等待轉換

Bot 會：
1. 📄 顯示 "正在處理檔案，請稍候..."
2. 下載檔案
3. 轉換為 PDF
4. ✅ 上傳轉換後的 PDF 檔案

### 範例

```
[使用者訊息]
@YourBot 請幫我轉換這個檔案
[附件: 報告.docx]

[Bot 回覆]
📄 正在處理 `報告.docx`，請稍候...

[Bot 回覆]
✅ 轉換完成！`報告.docx` → `報告.pdf`
[附件: 報告.pdf]
```

## ⚙️ 系統需求

### 轉換工具（擇一安裝）

Bot 支援**多種轉換方法**，會自動嘗試以下工具：

#### 選項 1：LibreOffice（推薦 - 免費）✅

- **下載：** https://www.libreoffice.org/download/download/
- **優點：**
  - ✅ 完全免費開源
  - ✅ 無需授權
  - ✅ 轉換品質優良
  - ✅ 跨平台支援
- **安裝：** 下載安裝程式並使用預設路徑安裝

#### 選項 2：Microsoft Office

- **需求：** Office 2013 或更新版本
- **元件：** Word 和 PowerPoint
- **注意：** 需要有效授權（非試用版）

### 安裝 Python 套件

```bash
pip install -r requirements.txt
```

### 新增的 Python 套件

```txt
aiohttp>=3.9.0      # 非同步 HTTP 請求（下載檔案）
comtypes>=1.4.0     # Windows COM 介面（呼叫 Office）
pypandoc>=1.13      # 備用轉換工具
docx2pdf>=0.1.8     # DOCX 轉換工具
python-pptx>=0.6.21 # PPTX 處理工具
```

### 快速開始

詳細安裝步驟請參考：
- 📚 [快速開始指南](./QUICK_START_CONVERTER.md)
- 🔧 [疑難排解指南](./TROUBLESHOOTING.md)

## 🔧 技術細節

### 轉換流程

1. **檢測訊息** - `on_message` 事件監聽器
   - 檢查 bot 是否被提及
   - 檢查是否有附件
   - 檢查檔案副檔名

2. **下載檔案** - `download_file()` 函數
   - 使用 `aiohttp` 非同步下載
   - 儲存到臨時目錄

3. **轉換檔案** - `convert_file_to_pdf()` 函數（多重備援）
   - **DOCX 轉換順序：**
     1. Microsoft Office (COM API)
     2. docx2pdf（可使用 Office 或 LibreOffice）
     3. LibreOffice（命令列）
   - **PPTX 轉換順序：**
     1. Microsoft Office (COM API)
     2. LibreOffice（命令列）

4. **上傳結果**
   - 檢查檔案大小（Discord 限制 8MB）
   - 使用 `discord.File` 上傳 PDF
   - 自動刪除臨時檔案

### 主要函數

#### `download_file(url: str, save_path: str) -> bool`
非同步下載檔案

#### `check_office_installed() -> bool`
檢查 Microsoft Office 是否已安裝

#### `check_libreoffice_installed() -> bool`
檢查 LibreOffice 是否已安裝

#### `convert_docx_to_pdf_office(docx_path: str, pdf_path: str) -> tuple[bool, str]`
使用 Microsoft Word COM API 轉換 DOCX 為 PDF

#### `convert_docx_to_pdf_docx2pdf(docx_path: str, pdf_path: str) -> tuple[bool, str]`
使用 docx2pdf 套件轉換（需要 Office 或 LibreOffice 作為後端）

#### `convert_docx_to_pdf_libreoffice(docx_path: str, pdf_path: str) -> tuple[bool, str]`
使用 LibreOffice 命令列介面轉換

#### `convert_pptx_to_pdf_office(pptx_path: str, pdf_path: str) -> tuple[bool, str]`
使用 Microsoft PowerPoint COM API 轉換 PPTX 為 PDF

#### `convert_pptx_to_pdf_libreoffice(pptx_path: str, pdf_path: str) -> tuple[bool, str]`
使用 LibreOffice 命令列介面轉換 PPTX

#### `convert_file_to_pdf(file_path: str, file_extension: str) -> tuple[Optional[str], str]`
統一的轉換介面，自動嘗試多種轉換方法，返回 PDF 路徑和使用的方法

### 智慧備援機制

Bot 會**自動嘗試多種轉換方法**，直到成功為止：

```python
# 範例：DOCX 轉換
1. 嘗試 Microsoft Office → 如果失敗 →
2. 嘗試 docx2pdf → 如果失敗 →
3. 嘗試 LibreOffice → 如果失敗 →
4. 回報所有方法都失敗
```

這確保了即使某個轉換工具無法使用，其他方法仍然可以接手處理。

## ⚠️ 注意事項

1. **需要轉換工具（至少一個）**
   - ✅ **LibreOffice**（推薦 - 免費）
   - ✅ **Microsoft Office**（需授權）
   - Bot 會自動嘗試所有可用的方法
   - 若都未安裝，轉換會失敗並顯示安裝指南

2. **檔案大小限制**
   - Discord 免費伺服器：最大 8MB
   - Discord Nitro 伺服器：最大 100MB
   - 轉換後的 PDF 可能比原檔案更大
   - 超過限制會顯示錯誤訊息

3. **轉換時間**
   - 小檔案（<1MB）：約 5-10 秒
   - 中檔案（1-5MB）：約 10-30 秒
   - 大檔案（>5MB）：約 30 秒以上
   - 不同轉換工具速度略有差異

4. **並發處理**
   - 可同時處理多個檔案
   - 每個檔案獨立轉換
   - 批次上傳會逐一處理

5. **安全性**
   - 檔案儲存在臨時目錄
   - 處理完成後自動刪除
   - 不會保留任何檔案
   - 使用 Python `tempfile` 模組確保安全

6. **系統診斷**
   - 提及 bot 但不附加檔案會顯示系統狀態
   - 可查看哪些轉換工具可用
   - 轉換失敗會提供詳細的錯誤診斷

## 🐛 常見問題

### Q: 轉換失敗怎麼辦？

**A:** 新版本會自動嘗試多種轉換方法：

1. **查看錯誤訊息** - Bot 會顯示詳細的診斷資訊
2. **安裝 LibreOffice** - 免費且推薦：https://www.libreoffice.org/
3. **查看詳細指南** - 參考 [疑難排解指南](./TROUBLESHOOTING.md)

常見原因：
- ❌ 未安裝任何轉換工具（Office 或 LibreOffice）
- ❌ 檔案損壞
- ❌ 檔案大小超過限制

### Q: 需要安裝 Microsoft Office 嗎？

**A:** **不需要！** 

你可以選擇：
- ✅ **LibreOffice**（免費 - 推薦）
- ✅ **Microsoft Office**（需授權）
- ✅ **兩者都安裝**（雙重保障）

Bot 會自動使用任何可用的工具。

### Q: 支援其他檔案格式嗎？

**A:** 目前支援：
- ✅ `.doc` - Word 舊格式
- ✅ `.docx` - Word 新格式
- ✅ `.pptx` - PowerPoint
- ❌ `.xlsx` - Excel（計劃中）
- ❌ `.odt`, `.odp` - OpenDocument（LibreOffice 可轉）

### Q: 可以在 Linux/Mac 上使用嗎？

**A:** 目前**部分支援**：

- ✅ **LibreOffice 方法**：跨平台，Linux/Mac 可用
- ❌ **Office COM API**：僅 Windows

在 Linux/Mac 上使用：
1. 安裝 LibreOffice
2. Bot 會自動使用 LibreOffice 轉換

### Q: 轉換品質如何？

**A:** 

| 方法 | 品質 | 說明 |
|------|------|------|
| Microsoft Office | ⭐⭐⭐⭐⭐ | 原生轉換，最高品質 |
| LibreOffice | ⭐⭐⭐⭐⭐ | 與 Office 相當 |
| docx2pdf | ⭐⭐⭐⭐ | 依賴後端工具 |

所有方法都能保留：
- ✅ 格式和排版
- ✅ 字體和樣式
- ✅ 圖片和圖表
- ✅ 頁眉和頁腳

### Q: Bot 沒有回應？

**A:** 檢查清單：

1. ✅ Bot 是否在線上
2. ✅ 是否正確 `@提及` bot
3. ✅ 是否有附加支援的檔案格式
4. ✅ Bot 是否有頻道的讀寫權限
5. ✅ 是否已安裝轉換工具（Office 或 LibreOffice）

**診斷方式：**
- 單獨 `@Bot`（不附加檔案）
- Bot 會顯示系統狀態和可用的轉換工具

### Q: 可以批次轉換嗎？

**A:** 可以！一次上傳多個檔案即可，Bot 會逐一處理。

### Q: 如何查看系統狀態？

**A:** 在 Discord 中單獨 `@Bot`（不附加檔案），Bot 會顯示：
- ✅/❌ Microsoft Office 狀態
- ✅/❌ LibreOffice 狀態
- 📚 使用說明

### Q: 為什麼推薦 LibreOffice？

**A:** 
- ✅ **完全免費** - 無需授權費用
- ✅ **開源軟體** - 安全透明
- ✅ **功能完整** - 支援所有 Office 格式
- ✅ **轉換品質** - 與 Office 相當
- ✅ **跨平台** - Windows/Mac/Linux 都能用
- ✅ **無授權煩惱** - 商業使用也免費

## 🚀 未來擴充

- [ ] 支援 .xlsx (Excel) 轉換
- [ ] 支援 .odt, .odp (OpenDocument)
- [ ] 跨平台支援（LibreOffice）
- [ ] 壓縮 PDF（減少檔案大小）
- [ ] 自訂 PDF 設定（頁面大小、方向）
- [ ] 轉換進度條
- [ ] 轉換佇列管理

## 📞 技術支援

若遇到問題，請提供：
1. 錯誤訊息截圖
2. 檔案類型和大小
3. Windows 版本
4. Office 版本

---

**最後更新**：2025-10-16


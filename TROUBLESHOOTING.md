# 🔧 疑難排解指南 - 檔案轉換功能

## ❌ 問題：轉換失敗

如果你看到以下錯誤訊息：
```
❌ 轉換 XXX.docx 失敗！請確保系統已安裝 Microsoft Office。
```

這表示系統缺少必要的轉換工具。請按照以下步驟解決：

---

## ✅ 解決方案

### 選項 1：安裝 LibreOffice（推薦 - 免費）

LibreOffice 是免費開源的 Office 套件，完全免費且功能強大。

#### 📥 下載與安裝

1. **前往官網下載**
   - 網址：https://www.libreoffice.org/download/download/
   - 選擇 Windows 版本
   - 下載最新穩定版

2. **安裝步驟**
   ```
   1. 執行下載的安裝檔（例如：LibreOffice_7.6.2_Win_x64.msi）
   2. 選擇「完整安裝」
   3. 保持預設安裝路徑（重要！）
      • C:\Program Files\LibreOffice
   4. 完成安裝
   5. 重新啟動 Bot
   ```

3. **驗證安裝**
   - 在 Discord 中提及 Bot（不附加檔案）
   - Bot 會顯示系統狀態
   - 確認顯示「✅ LibreOffice」

#### 🎯 推薦 LibreOffice 的原因

- ✅ 完全免費，無需授權
- ✅ 開源軟體，安全可靠
- ✅ 支援所有 Office 格式
- ✅ 轉換品質優良
- ✅ 跨平台（Windows/Mac/Linux）

---

### 選項 2：使用 Microsoft Office

如果你已經有 Microsoft Office 授權，也可以使用它。

#### 📋 需求

- Microsoft Office 2013 或更新版本
- 需要有效的授權（非試用版）
- 必須安裝以下元件：
  - **Word** - 用於 .doc/.docx 轉換
  - **PowerPoint** - 用於 .pptx 轉換

#### ⚙️ 設定

1. 確保 Office 已啟用
2. 至少開啟過 Word 和 PowerPoint 一次
3. 重新啟動 Bot

#### ⚠️ 常見問題

**Q: 我已經安裝 Office 但還是失敗？**

A: 可能原因：
1. Office 是試用版已過期
2. Office 未啟用
3. Office 元件不完整（缺少 Word 或 PowerPoint）
4. 安裝的是 Office 365 線上版（需要桌面版）

---

## 🧪 測試轉換功能

### 測試步驟

1. **檢查系統狀態**
   ```
   在 Discord 中輸入：@YourBot
   ```
   Bot 會顯示：
   ```
   📄 檔案轉換助手
   
   支援格式：
   ✅ .doc
   ✅ .docx
   ✅ .pptx
   
   系統狀態：
   ✅ Microsoft Office  或  ✅ LibreOffice
   ```

2. **測試轉換**
   - 上傳一個測試 .docx 檔案
   - 在訊息中 @Bot
   - 應該會看到：
     ```
     📄 正在處理 test.docx，請稍候...
     ✅ 轉換完成！test.docx → test.pdf
     使用方法: LibreOffice
     ```

---

## 📊 轉換方法優先順序

Bot 會按照以下順序嘗試不同的轉換方法：

### DOCX 轉換
1. **Microsoft Office** - 最優先
2. **docx2pdf** - 次要（需要 Office 或 LibreOffice）
3. **LibreOffice** - 備用

### PPTX 轉換
1. **Microsoft Office** - 最優先
2. **LibreOffice** - 備用

---

## 🔍 詳細錯誤診斷

### 錯誤 1：「未偵測到轉換工具」

**原因：** 系統沒有安裝 Office 也沒有 LibreOffice

**解決：** 
1. 安裝 LibreOffice（免費）- 推薦
2. 或安裝 Microsoft Office（需授權）

### 錯誤 2：「Office 錯誤: (-2147221005, '無效的類別字串', None, None)」

**原因：** Office 未正確註冊或損壞

**解決：**
1. 重新安裝 Office
2. 或改用 LibreOffice

### 錯誤 3：「LibreOffice 轉換失敗」

**原因：** LibreOffice 路徑不正確或程序損壞

**解決：**
1. 重新安裝 LibreOffice
2. 確保安裝到預設路徑：
   - `C:\Program Files\LibreOffice`
   - `C:\Program Files (x86)\LibreOffice`

### 錯誤 4：「所有轉換方法都失敗了」

**原因：** 檔案可能損壞或格式不正確

**解決：**
1. 檢查原始檔案是否可以正常開啟
2. 嘗試用 Office/LibreOffice 手動開啟並另存
3. 確認檔案副檔名正確

### 錯誤 5：「轉換後的 PDF 檔案太大」

**原因：** PDF 超過 Discord 上傳限制（8MB）

**解決：**
1. 壓縮原始檔案中的圖片
2. 移除不必要的內容
3. 分割成多個檔案

---

## 🛠️ 進階疑難排解

### 手動測試 LibreOffice

開啟命令提示字元 (cmd)，執行：

```bash
# 檢查 LibreOffice 是否安裝
"C:\Program Files\LibreOffice\program\soffice.exe" --version

# 手動轉換測試
"C:\Program Files\LibreOffice\program\soffice.exe" --headless --convert-to pdf "C:\path\to\test.docx" --outdir "C:\path\to\output"
```

如果這些命令無法執行，表示 LibreOffice 安裝有問題。

### 手動測試 Office COM

開啟 PowerShell，執行：

```powershell
# 測試 Word
$word = New-Object -ComObject Word.Application
$word.Quit()

# 測試 PowerPoint
$ppt = New-Object -ComObject Powerpoint.Application
$ppt.Quit()
```

如果出現錯誤，表示 Office COM 介面無法使用。

### 檢查 Python 套件

```bash
# 重新安裝套件
pip install -r requirements.txt --force-reinstall

# 檢查套件版本
pip list | findstr "discord aiohttp comtypes docx2pdf"
```

---

## 📱 在 Discord 中測試

### 完整測試流程

```
1. @YourBot
   → 查看系統狀態

2. 上傳 test.docx + @YourBot
   → 測試 DOCX 轉換

3. 上傳 test.pptx + @YourBot
   → 測試 PPTX 轉換

4. 一次上傳多個檔案 + @YourBot
   → 測試批次轉換
```

---

## 💡 最佳實踐

### 建議配置

1. **推薦方案：安裝 LibreOffice**
   - 免費
   - 穩定
   - 支援所有格式
   - 無授權問題

2. **企業方案：使用 Office + LibreOffice**
   - Office 作為主要工具
   - LibreOffice 作為備用
   - 雙重保障

### 使用技巧

1. **檔案大小**
   - 建議 < 5MB
   - 大檔案轉換時間較長

2. **檔案命名**
   - 避免特殊字元
   - 使用英文或數字
   - 例如：`Report_2024.docx` ✅
   - 避免：`報告@#$%.docx` ❌

3. **批次轉換**
   - 可一次上傳多個檔案
   - Bot 會逐一處理

---

## 📞 仍然無法解決？

如果按照上述步驟仍無法解決，請提供以下資訊：

1. **系統資訊**
   - Windows 版本
   - 已安裝的軟體（Office/LibreOffice）
   - 軟體版本

2. **錯誤訊息**
   - Discord 中的完整錯誤訊息截圖
   - Bot 終端機的錯誤輸出

3. **測試結果**
   - 手動測試 LibreOffice 的結果
   - 檔案資訊（大小、格式）

4. **Bot 終端機輸出**
   ```
   查看 Bot 執行時的輸出，特別是包含：
   🔄 嘗試使用 Microsoft Office...
   🔄 嘗試使用 docx2pdf...
   🔄 嘗試使用 LibreOffice...
   ```

---

## ✅ 成功範例

轉換成功時，你會看到：

```
用戶上傳: Report.docx + @Bot

Bot 回應:
📄 正在處理 Report.docx，請稍候...

Bot 回應:
✅ 轉換完成！Report.docx → Report.pdf
使用方法: LibreOffice
[附件: Report.pdf]
```

終端機輸出：
```
🔄 嘗試使用 Microsoft Office...
   ⚠️ Office 錯誤: ...
🔄 嘗試使用 docx2pdf...
   ⚠️ docx2pdf 錯誤: ...
🔄 嘗試使用 LibreOffice...
✅ 成功轉換: Report.docx → Report.pdf (使用 LibreOffice)
```

---

## 📚 相關連結

- [LibreOffice 官網](https://www.libreoffice.org/)
- [LibreOffice 下載](https://www.libreoffice.org/download/download/)
- [Microsoft Office](https://www.office.com/)
- [Discord Bot 開發文件](https://discord.com/developers/docs)

---

**最後更新：** 2025-10-16
**版本：** 2.0


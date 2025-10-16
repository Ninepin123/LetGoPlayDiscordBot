# 🚀 檔案轉換功能 - 快速開始

## 📝 三步驟啟用轉換功能

### 步驟 1：安裝 Python 套件

```bash
pip install -r requirements.txt
```

這會安裝：
- `aiohttp` - 檔案下載
- `comtypes` - Windows Office API
- `docx2pdf` - DOCX 轉換
- `python-pptx` - PPTX 處理

### 步驟 2：安裝轉換工具（選一個）

#### 選項 A：LibreOffice（推薦 - 免費）✅

1. 前往 https://www.libreoffice.org/download/download/
2. 下載 Windows 版本
3. 執行安裝程式
4. 使用預設安裝路徑
5. 完成安裝

#### 選項 B：Microsoft Office

如果你已經有 Office 授權，確保：
- 已安裝 Word 和 PowerPoint
- Office 已啟用（非試用版）

### 步驟 3：重新啟動 Bot

```bash
python main.py
```

---

## ✅ 驗證安裝

在 Discord 中：

```
@YourBot
```

Bot 會回覆系統狀態：

```
📄 檔案轉換助手

支援格式：
✅ .doc
✅ .docx
✅ .pptx

系統狀態：
✅ Microsoft Office
✅ LibreOffice
```

至少要有一個 ✅ 才能使用！

---

## 🎯 使用方式

### 基本使用

1. 上傳檔案（.doc, .docx, .pptx）
2. 在訊息中 `@YourBot`
3. 等待轉換完成
4. 下載 PDF

### 範例

```
[上傳] Report.docx
訊息：@YourBot 幫我轉換

Bot 回覆：
📄 正在處理 Report.docx，請稍候...

Bot 回覆：
✅ 轉換完成！Report.docx → Report.pdf
使用方法: LibreOffice
[附件: Report.pdf]
```

---

## ❓ 常見問題

### Q: 轉換失敗怎麼辦？

**A:** 確認以下事項：
1. ✅ 已安裝 LibreOffice 或 Office
2. ✅ 已安裝 Python 套件
3. ✅ 檔案格式正確（.doc/.docx/.pptx）
4. ✅ 檔案大小 < 8MB

如果還是失敗，查看 [疑難排解指南](./TROUBLESHOOTING.md)

### Q: 支援哪些格式？

**A:** 
- ✅ `.doc` - Word 舊格式
- ✅ `.docx` - Word 新格式
- ✅ `.pptx` - PowerPoint
- ❌ `.xlsx` - Excel（未來支援）

### Q: 可以批次轉換嗎？

**A:** 可以！一次上傳多個檔案即可。

### Q: 需要授權嗎？

**A:** 
- **LibreOffice** - 完全免費，無需授權 ✅
- **Microsoft Office** - 需要有效授權

### Q: 轉換需要多久？

**A:** 
- 小檔案（< 1MB）：5-10 秒
- 中檔案（1-5MB）：10-30 秒
- 大檔案（> 5MB）：30 秒以上

---

## 🎯 推薦配置

### 最簡單的方式（推薦）

```
1. 安裝 LibreOffice（免費）
2. pip install -r requirements.txt
3. python main.py
```

✅ 完全免費
✅ 5 分鐘完成
✅ 穩定可靠

---

## 📊 功能比較

| 功能 | LibreOffice | Microsoft Office |
|------|-------------|------------------|
| 費用 | ✅ 免費 | ❌ 需授權 |
| DOCX 轉換 | ✅ | ✅ |
| PPTX 轉換 | ✅ | ✅ |
| 轉換品質 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 安裝容易度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 跨平台 | ✅ | ❌ Windows only |

---

## 🔗 快速連結

- 📥 [下載 LibreOffice](https://www.libreoffice.org/download/download/)
- 📚 [完整說明文件](./FILE_CONVERTER_README.md)
- 🔧 [疑難排解指南](./TROUBLESHOOTING.md)
- 💬 [Discord Bot 文件](https://discord.com/developers/docs)

---

## 📝 完整安裝腳本（Windows）

```bash
# 1. 安裝 Python 套件
pip install -r requirements.txt

# 2. 下載並安裝 LibreOffice（手動）
# 前往 https://www.libreoffice.org/download/download/

# 3. 驗證安裝
"C:\Program Files\LibreOffice\program\soffice.exe" --version

# 4. 啟動 Bot
python main.py
```

---

**就這麼簡單！🎉**

有任何問題請查看 [疑難排解指南](./TROUBLESHOOTING.md)


# 🚀 Phase 4 Quick Start Guide

## What's New?
**Conditional Logic (If/Then/Else)** for ThreatFlow workflows!

---

## 🎯 Quick Test (5 Minutes)

### **1. Start Services**
```bash
# Terminal 1: Middleware (if not running)
cd ~/COLLEGE/ThreatFlow/threatflow-middleware
venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8030

# Terminal 2: Frontend
cd ~/COLLEGE/ThreatFlow/threatflow-frontend
npm start
```

### **2. Create Test File**
```bash
# EICAR malware test file
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > ~/eicar.txt
```

### **3. Build Workflow (UI)**
1. Open: `http://localhost:3000`
2. Drag nodes in this order:
   - **File Upload** (blue)
   - **ClamAV** analyzer (green)
   - **Conditional** node (orange) ⬅️ **NEW!**
   - **PE_Info** analyzer (green)

3. Connect:
   - File → ClamAV
   - ClamAV → Conditional (left input)
   - Conditional → PE_Info (use **green TRUE handle**)

### **4. Execute**
1. Click **Execute** button
2. Upload `~/eicar.txt`
3. Watch magic happen! ✨

### **5. Expected Result**
```json
{
  "success": true,
  "has_conditionals": true,
  "executed_stages": [0, 1],  // Both stages ran!
  "skipped_stages": [],
  "message": "Conditional workflow executed: 2 of 2 stages"
}
```

**Why?** EICAR is detected as malicious → TRUE branch executes PE_Info!

---

## 🎨 Visual Guide

### **Conditional Node**
```
        ┌─────────────┐
        │      ◊      │
   ●────│ Is Malicious? │────● ✓ True (green)
        │  from: ClamAV│────● ✗ False (red)
        └─────────────┘
```

### **Example Workflow**
```
📤 File
 └→ 🛡️ ClamAV
     └→ 🔀 Is Malicious?
         ├─ ✓ TRUE → 🛡️ PE_Info
         └─ ✗ FALSE → (skip)
```

---

## 📋 Condition Types

| Type | Description | Example |
|------|-------------|---------|
| `verdict_malicious` | Is file malicious? | ClamAV detects virus |
| `verdict_suspicious` | Is file suspicious? | Heuristic detection |
| `verdict_clean` | Is file clean? | No threats found |
| `analyzer_success` | Did analyzer complete? | No errors/timeouts |
| `analyzer_failed` | Did analyzer fail? | Timeout or error |
| `custom_field` | Custom JSON field check | Check specific value |

---

## 🔧 Troubleshooting

### **Problem:** Conditional node not in palette
**Solution:** Check `NodePalette.tsx` has conditional item

### **Problem:** Cannot connect to conditional
**Solution:** Use LEFT handle for input, RIGHT handles for outputs

### **Problem:** Condition always FALSE
**Solution:** Check backend logs for condition evaluation

### **Problem:** TypeScript errors in VS Code
**Solution:** Restart TypeScript server (`Ctrl+Shift+P` → "Restart TS Server")

---

## 📁 Files Changed

**Backend:**
- ✅ `app/models/workflow.py`
- ✅ `app/services/workflow_parser.py`
- ✅ `app/services/intelowl_service.py`
- ✅ `app/routers/execute.py`

**Frontend:**
- ✅ `src/components/Canvas/CustomNodes/ConditionalNode.tsx` (NEW)
- ✅ `src/components/Canvas/CustomNodes/ConditionalNode.css` (NEW)
- ✅ `src/components/Canvas/WorkflowCanvas.tsx`
- ✅ `src/components/Sidebar/NodePalette.tsx`
- ✅ `src/utils/nodeFactory.ts`

---

## 🧪 Quick Verification

```bash
# Backend models
cd ~/COLLEGE/ThreatFlow/threatflow-middleware
venv/bin/python3 -c "from app.models.workflow import NodeType, ConditionType; print('✅' if hasattr(NodeType, 'CONDITIONAL') else '❌')"

# Frontend files
cd ~/COLLEGE/ThreatFlow/threatflow-frontend
test -f src/components/Canvas/CustomNodes/ConditionalNode.tsx && echo "✅ ConditionalNode.tsx" || echo "❌ Missing"
test -f src/components/Canvas/CustomNodes/ConditionalNode.css && echo "✅ ConditionalNode.css" || echo "❌ Missing"

# Middleware running
curl -s http://localhost:8030/docs | grep -q "FastAPI" && echo "✅ Middleware running" || echo "❌ Not running"
```

---

## 📚 Documentation

- **Full Guide:** `Docs/README_PHASE-4.md` (5,000+ lines)
- **Summary:** `Docs/PHASE-4-SUMMARY.md` (This overview)
- **Quick Start:** `Docs/PHASE-4-QUICKSTART.md` (This file)

---

## 🎓 Advanced Examples

### **Malware Deep Dive**
```
File → ClamAV → Is Malicious?
                  ├─ TRUE → PE_Info → Capa_Info → Yara
                  └─ FALSE → File_Info (basic scan only)
```

### **File Type Router**
```
File → File_Info → Is PE?
                     ├─ TRUE → PE_Info + PE_Authenticode
                     └─ FALSE → Is PDF?
                                  ├─ TRUE → PDF_Info
                                  └─ FALSE → Strings_Info
```

---

## ✨ Key Features

- ✅ Visual conditional nodes
- ✅ True/False branch outputs
- ✅ 6 condition types
- ✅ Multi-stage execution
- ✅ Automatic skipping of unmet conditions
- ✅ Backwards compatible with linear workflows

---

## 🎉 That's It!

You now have **conditional logic** in ThreatFlow!

Build intelligent workflows that adapt based on analysis results! 🚀

---

**Need Help?** Check full documentation in `Docs/README_PHASE-4.md`

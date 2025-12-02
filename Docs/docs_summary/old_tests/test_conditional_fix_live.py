#!/usr/bin/env python3
"""
Live test script to verify conditional routing fix
Run this after starting the backend server
"""

import json
import sys

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def main():
    print_section("CONDITIONAL ROUTING FIX - VERIFICATION GUIDE")
    
    print("\n📋 **EXPECTED BEHAVIOR**:")
    print("  1. Backend should skip stages with empty analyzers")
    print("  2. Backend should evaluate conditions with 'negate' flag")
    print("  3. Backend should log which result nodes are targeted")
    print("  4. Frontend should only update result nodes in executed branches")
    
    print_section("BACKEND LOGS TO LOOK FOR")
    
    print("\n✅ **GOOD SIGNS (What you SHOULD see)**:")
    print("""
    📋 Stage 0: Initial stage, executing analyzers=['ClamAV']
    ▶️  Stage 0: Executing with analyzers=['ClamAV']
    ✅ Stage 0 completed successfully
    
    🔀 Stage 1: Condition 'verdict_malicious' evaluated to True, target_nodes=['result-5']
    ✅ Stage 1: Result-only (no analyzers), routing to ['result-5']
    
    🔀 Stage 2: Condition 'NOT verdict_malicious' evaluated to False, target_nodes=['result-6']
    ⏭️  Stage 2: SKIPPED (condition not met), would have routed to ['result-6']
    """)
    
    print("\n❌ **BAD SIGNS (What you should NOT see anymore)**:")
    print("""
    ERROR - IntelOwl API error: 400 Client Error: Bad Request
    Details: {'errors': {'detail': ['No Analyzers and Connectors can be run after filtering']}}
    
    WARNING - Condition validation failed: ["Condition must have 'source_analyzer' field"]
    
    Stage 1: Condition evaluated to True  [WITHOUT target_nodes info]
    Stage 2: Condition evaluated to False [WITHOUT target_nodes info]
    """)
    
    print_section("TESTING CHECKLIST")
    
    print("\n**Test 1: Upload MALICIOUS file (e.g., eicar_variant.txt)**")
    print("  Expected:")
    print("    - Stage 0 (ClamAV): Executes ✅")
    print("    - Stage 1 (TRUE branch → result-5): Executes ✅")
    print("    - Stage 2 (FALSE branch → result-6): Skipped ⏭️")
    print("  Frontend:")
    print("    - Result node 'result-5': Shows ClamAV results ✅")
    print("    - Result node 'result-6': Shows 'Branch not executed' ✅")
    
    print("\n**Test 2: Upload CLEAN file (e.g., simple text file)**")
    print("  Expected:")
    print("    - Stage 0 (ClamAV): Executes ✅")
    print("    - Stage 1 (TRUE branch → result-5): Skipped ⏭️")
    print("    - Stage 2 (FALSE branch → result-6): Executes ✅")
    print("  Frontend:")
    print("    - Result node 'result-5': Shows 'Branch not executed' ✅")
    print("    - Result node 'result-6': Shows ClamAV results ✅")
    
    print_section("KEY FIXES APPLIED")
    
    print("""
1. ✅ Backend skips stages with empty analyzers (result-only stages)
   - File: intelowl_service.py, Line ~625
   - Fix: Check if analyzers list is empty before submission
   
2. ✅ Backend handles 'negate' flag for FALSE branches
   - File: intelowl_service.py, Line ~678
   - Fix: Check for 'negate' flag and invert condition result
   
3. ✅ Parser preserves 'source_analyzer' in negated conditions
   - File: workflow_parser.py, Line ~236
   - Fix: Copy condition dict and add 'negate' flag instead of wrapping
   
4. ✅ Backend logs target nodes for routing
   - File: intelowl_service.py, Line ~617
   - Fix: Include target_nodes in log messages
   
5. ✅ Frontend distribution uses routing metadata
   - File: useWorkflowExecution.ts, Line ~305
   - Fix: Pass stage_routing and has_conditionals to distributeResultsToResultNodes
    """)
    
    print_section("QUICK TEST COMMAND")
    
    print("""
# Terminal 1: Start backend (if not already running)
cd /home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware
source venv/bin/activate
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8030

# Terminal 2: Start frontend (if not already running)
cd /home/anonymous/COLLEGE/ThreatFlow/threatflow-frontend
npm start

# Browser: Open http://localhost:3000
1. Create workflow: File → ClamAV → Conditional → Result (TRUE) + Result (FALSE)
2. Upload eicar_variant.txt (malicious)
3. Click Execute
4. Check BOTH backend logs AND frontend result nodes
5. Repeat with clean file
    """)
    
    print_section("SUCCESS CRITERIA")
    
    print("""
✅ No more "No Analyzers and Connectors" errors
✅ No more "Condition must have 'source_analyzer'" warnings
✅ Clear log messages showing which stages execute/skip
✅ Only ONE result node shows data per execution
✅ Other result node shows "Branch not executed"
    """)
    
    print("\n" + "="*80)
    print("  Ready to test! Start the servers and try the workflow.")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()

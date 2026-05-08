#!/bin/bash
# A9-A12データセット確認スクリプト

echo "=== A9-A12 Dataset Verification ==="
echo ""

# A9: OpenMathInstruct-1
echo "1. Checking A9: OpenMathInstruct-1..."
python3 << 'EOF'
try:
    from datasets import load_dataset
    ds = load_dataset('nvidia/OpenMathInstruct-1', split='train[:1]')
    print(f"  ✓ Dataset found")
    print(f"  Keys: {list(ds[0].keys())}")
    print(f"  Sample: {ds[0]}")
except Exception as e:
    print(f"  ✗ Error: {e}")
EOF

echo ""

# A10: MathCodeInstruct
echo "2. Checking A10: MathCodeInstruct..."
python3 << 'EOF'
try:
    from datasets import load_dataset
    ds = load_dataset('MathLLMs/MathCodeInstruct', split='train[:1]')
    print(f"  ✓ Dataset found")
    print(f"  Keys: {list(ds[0].keys())}")
    print(f"  Sample: {ds[0]}")
except Exception as e:
    print(f"  ✗ Error: {e}")
EOF

echo ""

# A11: VisCode-200K (複数の候補を試行)
echo "3. Checking A11: VisCode-200K..."
for dataset_name in "viscode/VisCode-200K" "VisCode/VisCode-200K" "microsoft/VisCode-200K"; do
    echo "  Trying: $dataset_name"
    python3 << EOF
try:
    from datasets import load_dataset
    ds = load_dataset('$dataset_name', split='train[:1]')
    print(f"    ✓ Dataset found: $dataset_name")
    print(f"    Keys: {list(ds[0].keys())}")
    print(f"    Sample: {ds[0]}")
except Exception as e:
    print(f"    ✗ Not found: {e}")
EOF
done

echo ""

# A12: OpenCodeInstruct
echo "4. Checking A12: OpenCodeInstruct..."
python3 << 'EOF'
try:
    from datasets import load_dataset
    ds = load_dataset('m-a-p/OpenCodeInstruct', split='train[:1]')
    print(f"  ✓ Dataset found")
    print(f"  Keys: {list(ds[0].keys())}")
    print(f"  Sample: {ds[0]}")
except Exception as e:
    print(f"  ✗ Error: {e}")
EOF

echo ""
echo "=== Verification Complete ==="

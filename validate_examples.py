import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(PROJECT_ROOT))

from src.worker.config import ConfigLoader, WorkerConfig

def validate_all():
    examples_dir = PROJECT_ROOT / "exemplos"
    files = list(examples_dir.glob("*.json"))
    
    print(f"Found {len(files)} JSON files in {examples_dir}")
    
    success_count = 0
    errors = []

    for file_path in files:
        print(f"Validating {file_path.name}...", end=" ")
        try:
            loader = ConfigLoader(str(file_path))
            config = loader.load()
            # Extra check: try to build the engine to verify logical consistency (e.g. agent refs)
            from src.worker.engine import WorkflowEngine
            engine = WorkflowEngine(config)
            engine.build()
            print("✅ OK")
            success_count += 1
        except Exception as e:
            print("❌ FAILED")
            errors.append(f"{file_path.name}: {str(e)}")

    print("\n--- Summary ---")
    print(f"Total: {len(files)}")
    print(f"Success: {success_count}")
    print(f"Failed: {len(errors)}")
    
    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"- {err}")

if __name__ == "__main__":
    validate_all()

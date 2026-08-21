import traceback
import sys

sys.path.insert(0, '../Langraph_Agent')

try:
    from main import ProductSearchOrchestrator
    orchestrator = ProductSearchOrchestrator()
except Exception as e:
    traceback.print_exc()

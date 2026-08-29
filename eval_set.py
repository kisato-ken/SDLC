import sys
import os

# Ensure src is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from sdlc_immune.evals.benchmark import run_evaluation, EVAL_BENCHMARK_SCENARIOS

if __name__ == "__main__":
    report = run_evaluation()
    print("=" * 60)
    print("      SDLC IMMUNE SYSTEM -- 25-SCENARIO EVAL BENCHMARK")
    print("=" * 60)
    print(f"Total Scenarios : {report['total_scenarios']}")
    print(f"Agreement Rate  : {report['agreement_rate']}%")
    print(f"Precision       : {report['precision']}%")
    print(f"Recall          : {report['recall']}%")
    print(f"Confusion Matrix: {report['confusion_matrix']}")
    print("=" * 60)

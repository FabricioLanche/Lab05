import argparse
import os
import sys
from typing import Dict

from external_hashing import external_hash_group_by
from heap_file import DepartmentRecord, export_to_heap


def ensure_heap_file(heap_path: str, csv_input: str, page_size: int) -> None:
    if os.path.exists(heap_path):
        return

    if not os.path.exists(csv_input):
        raise FileNotFoundError(
            f"No se encontro heap file en '{heap_path}' y tampoco CSV de entrada en '{csv_input}'."
        )

    print(f"[INFO] Heap file no encontrado. Exportando desde CSV: {csv_input}")
    export_to_heap(csv_input, heap_path, DepartmentRecord.RECORD_FORMAT, page_size)


def run_external_hashing(heap_path: str, page_size: int, buffer_size: int) -> Dict[str, int]:
    metrics = external_hash_group_by(
        heap_path=heap_path,
        page_size=page_size,
        buffer_size=buffer_size,
        group_key="from_date",
    )
    return metrics


def print_groupby_result(result_map: Dict[str, int], limit: int | None = None) -> None:
    items = sorted(result_map.items(), key=lambda kv: kv[0])
    if limit is not None and limit > 0:
        items = items[:limit]

    print("\nfrom_date,count")
    for from_date, count_value in items:
        print(f"{from_date},{count_value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Muestra el resultado de GROUP BY from_date usando external_hashing.py."
    )
    parser.add_argument("--heap-path", default="data/department_employee.bin")
    parser.add_argument("--csv-input", default="data_input/department_employee.csv")
    parser.add_argument("--page-size", type=int, default=4096)
    parser.add_argument("--buffer-size", type=int, default=65536)
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Cantidad maxima de filas a mostrar (0 = mostrar todas).",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    ensure_heap_file(args.heap_path, args.csv_input, args.page_size)

    print("[INFO] Ejecutando external hashing...")
    metrics = run_external_hashing(args.heap_path, args.page_size, args.buffer_size)
    result_map = metrics["result"]

    print("\n=== METRICAS ===")
    print(f"partitions_created: {metrics['partitions_created']}")
    print(f"pages_read        : {metrics['pages_read']}")
    print(f"pages_written     : {metrics['pages_written']}")
    print(f"time_phase1_sec   : {metrics['time_phase1_sec']:.4f}")
    print(f"time_phase2_sec   : {metrics['time_phase2_sec']:.4f}")
    print(f"time_total_sec    : {metrics['time_total_sec']:.4f}")
    print(f"group_count       : {len(result_map)}")

    print_groupby_result(result_map, None if args.limit == 0 else args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())

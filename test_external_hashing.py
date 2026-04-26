import os
from pathlib import Path

from heap_file import export_to_heap, get_heap_metadata, count_pages
from external_hashing import external_hash_group_by


def setup_data():
    """Export CSV files to binary heap format."""
    print("=" * 70)
    print("STEP 1: Exporting CSV to Heap Files")
    print("=" * 70)
    
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    page_size = 4096
    
    # Export employee table
    employee_csv = "employee .csv"
    employee_bin = "data/employee.bin"
    if os.path.exists(employee_csv):
        print(f"\n📤 Exporting {employee_csv} → {employee_bin}")
        export_to_heap(employee_csv, employee_bin, "employee", page_size)
        metadata = get_heap_metadata(employee_bin)
        pages = count_pages(employee_bin, page_size)
        print(f"   ✓ Pages: {pages}")
        print(f"   ✓ Record size: {metadata['record_size']} bytes")
        print(f"   ✓ Estimated records: {pages * (page_size - 4) // metadata['record_size']}")
    else:
        print(f"❌ File not found: {employee_csv}")
    
    # Export department_employee table
    dept_emp_csv = "department_employee.csv"
    dept_emp_bin = "data/department_employee.bin"
    if os.path.exists(dept_emp_csv):
        print(f"\n📤 Exporting {dept_emp_csv} → {dept_emp_bin}")
        export_to_heap(dept_emp_csv, dept_emp_bin, "department_employee", page_size)
        metadata = get_heap_metadata(dept_emp_bin)
        pages = count_pages(dept_emp_bin, page_size)
        print(f"   ✓ Pages: {pages}")
        print(f"   ✓ Record size: {metadata['record_size']} bytes")
        print(f"   ✓ Estimated records: {pages * (page_size - 4) // metadata['record_size']}")
    else:
        print(f"❌ File not found: {dept_emp_csv}")
    
    return data_dir


def test_external_hashing(heap_path: str):
    """Test External Hashing GROUP BY with different buffer sizes."""
    print("\n" + "=" * 95)
    print("STEP 2: Testing External Hashing (GROUP BY)")
    print("=" * 95)
    
    if not os.path.exists(heap_path):
        print(f"❌ Heap file not found: {heap_path}")
        return
    
    page_size = 4096
    group_key = "from_date"
    buffer_sizes = [65536, 131072, 262144]  # 64KB, 128KB, 256KB
    
    print(f"\nGrouping by: {group_key}")
    print(f"Page size: {page_size} bytes")
    
    # Detailed table with I/O statistics
    print("\n" + "─" * 130)
    print(f"{'Buffer':^12} | {'B-1':^4} | {'Phase 1':^10} | {'Phase 2':^10} | {'Total':^10} | {'Pages':^20} | {'Total':^8}")
    print(f"{'Size':^12} | {'Part':^4} | {'Time (s)':^10} | {'Time (s)':^10} | {'Time (s)':^10} | {'Read / Write':^20} | {'I/O':^8}")
    print("─" * 130)
    
    results = []
    for buffer_size in buffer_sizes:
        b_pages = max(buffer_size // page_size, 1)
        k = max(b_pages - 1, 1)
        
        result = external_hash_group_by(heap_path, page_size, buffer_size, group_key)
        
        buffer_kb = buffer_size / 1024
        pages_read = result['pages_read']
        pages_written = result['pages_written']
        total_pages = pages_read + pages_written
        
        print(f"{buffer_kb:6.0f} KB   | {k:4d} | {result['time_phase1_sec']:10.4f} | "
              f"{result['time_phase2_sec']:10.4f} | {result['time_total_sec']:10.4f} | "
              f"{pages_read:6d} / {pages_written:6d}   | {total_pages:8d}")
        
        results.append(result)
    
    print("─" * 130)
    
    # Statistics summary
    print("\n📊 ESTADÍSTICAS DE I/O:")
    print("-" * 95)
    print(f"{'Buffer Size':^20} | {'Particiones':^15} | {'Lectura (pag.)':^20} | {'Escritura (pag.)':^20}")
    print("-" * 95)
    
    for i, result in enumerate(results):
        buffer_kb = buffer_sizes[i] / 1024
        b_pages = max(buffer_sizes[i] // page_size, 1)
        k = max(b_pages - 1, 1)
        print(f"{buffer_kb:6.0f} KB           | {k:15d} | {result['pages_read']:20d} | {result['pages_written']:20d}")
    
    print("-" * 95)
    
    # Show sample results
    print(f"\n✓ Resultado del último test (Buffer 256KB):")
    print(f"  Total de grupos únicos: {len(result['result'])}")
    print(f"\n  Primeros 10 grupos (muestra):")
    for i, (group_value, count) in enumerate(list(result['result'].items())[:10], 1):
        print(f"    {i:2d}. {group_value}: {count:6d} registros")
    
    if len(result['result']) > 10:
        print(f"    ... y {len(result['result']) - 10} grupos más")
    
    return results


def main():
    """Main entry point."""
    print("\n" + "=" * 95)
    print("Lab05: External Hashing para GROUP BY")
    print("=" * 95)
    
    # Step 1: Setup data
    try:
        setup_data()
    except Exception as e:
        print(f"❌ Error during data setup: {e}")
        return
    
    # Step 2: Test External Hashing
    dept_emp_bin = "data/department_employee.bin"
    if os.path.exists(dept_emp_bin):
        try:
            test_external_hashing(dept_emp_bin)
        except Exception as e:
            print(f"❌ Error during external hashing: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

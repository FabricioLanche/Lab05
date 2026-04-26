import os
from pathlib import Path
from heap_file import export_to_heap, get_heap_metadata, count_pages
from external_hashing import external_hash_group_by
from external_file import external_sort

def setup_data():
    """Exporta CSVs a heap files si no existen."""
    print("=" * 100)
    print("PASO 0: Verificar datos")
    print("=" * 100)
    
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    page_size = 4096
    
    # Verificar department_employee
    dept_emp_bin = "data/department_employee.bin"
    if not os.path.exists(dept_emp_bin):
        print(f"\n📤 Exportando department_employee.csv → {dept_emp_bin}")
        export_to_heap("department_employee.csv", dept_emp_bin, "department_employee", page_size)
    
    metadata = get_heap_metadata(dept_emp_bin)
    pages = count_pages(dept_emp_bin, page_size)
    print(f"✓ department_employee: {pages} páginas, {metadata['record_size']} bytes/record")
    
    # Verificar employee
    employee_bin = "data/employee.bin"
    if not os.path.exists(employee_bin):
        print(f"\n📤 Exportando employee.csv → {employee_bin}")
        export_to_heap("employee .csv", employee_bin, "employee", page_size)
    
    if os.path.exists(employee_bin):
        metadata = get_heap_metadata(employee_bin)
        pages = count_pages(employee_bin, page_size)
        print(f"✓ employee: {pages} páginas, {metadata['record_size']} bytes/record")
    else:
        print(f"⚠ employee.bin no disponible")
    
    return data_dir


def run_performance_analysis():
    """Ejecuta análisis de rendimiento para ambos algoritmos."""
    print("\n" + "=" * 100)
    print("SECCIÓN 2.4: ANÁLISIS DE RENDIMIENTO")
    print("=" * 100)
    
    page_size = 4096
    buffer_sizes = [65536, 131072, 262144]  # 64KB, 128KB, 256KB
    
    # Datos para la tabla 2.4
    results_hashing = []
    results_sorting = []
    
    # =========================================================================
    # PARTE A: EXTERNAL HASHING (GROUP BY en department_employee)
    # =========================================================================
    print("\n" + "─" * 100)
    print("EXTERNAL HASHING: GROUP BY from_date")
    print("─" * 100)
    
    dept_emp_bin = "data/department_employee.bin"
    if os.path.exists(dept_emp_bin):
        group_key = "from_date"
        print(f"\n{'Buffer Size':^20} | {'B (pags)':^10} | {'Particiones':^12} | {'Phase 1 (s)':^12} | {'Phase 2 (s)':^12} | {'Total (s)':^12} | {'I/O (pags)':^12}")
        print("─" * 100)
        
        for buffer_size in buffer_sizes:
            b_pages = max(buffer_size // page_size, 1)
            k = max(b_pages - 1, 1)
            
            result = external_hash_group_by(dept_emp_bin, page_size, buffer_size, group_key)
            
            buffer_kb = buffer_size / 1024
            total_io = result['pages_read'] + result['pages_written']
            
            print(f"{buffer_kb:6.0f} KB ({b_pages:2d})   | {b_pages:10d} | {k:12d} | {result['time_phase1_sec']:12.4f} | {result['time_phase2_sec']:12.4f} | {result['time_total_sec']:12.4f} | {total_io:12d}")
            
            results_hashing.append({
                'buffer_size': buffer_kb,
                'b_pages': b_pages,
                'particiones': k,
                'tiempo_fase1': result['time_phase1_sec'],
                'tiempo_fase2': result['time_phase2_sec'],
                'tiempo_total': result['time_total_sec'],
                'pages_read': result['pages_read'],
                'pages_written': result['pages_written'],
                'total_io': total_io
            })
    
    # =========================================================================
    # PARTE B: EXTERNAL SORTING (ORDER BY hire_date en employee)
    # =========================================================================
    print("\n" + "─" * 100)
    print("EXTERNAL SORTING: ORDER BY hire_date")
    print("─" * 100)
    
    employee_bin = "data/employee.bin"
    if os.path.exists(employee_bin):
        sort_key = "hire_date"
        output_dir = Path("data/sorted_analysis")
        output_dir.mkdir(exist_ok=True)
        
        print(f"\n{'Buffer Size':^20} | {'B (pags)':^10} | {'Runs':^12} | {'Phase 1 (s)':^12} | {'Phase 2 (s)':^12} | {'Total (s)':^12} | {'I/O (pags)':^12}")
        print("─" * 100)
        
        for i, buffer_size in enumerate(buffer_sizes):
            b_pages = max(buffer_size // page_size, 1)
            
            output_path = output_dir / f"sorted_{i:02d}.bin"
            result = external_sort(employee_bin, str(output_path), page_size, buffer_size, sort_key)
            
            buffer_kb = buffer_size / 1024
            total_io = result['pages_read'] + result['pages_written']
            
            print(f"{buffer_kb:6.0f} KB ({b_pages:2d})   | {b_pages:10d} | {result['runs_generated']:12d} | {result['time_phase1_sec']:12.4f} | {result['time_phase2_sec']:12.4f} | {result['time_total_sec']:12.4f} | {total_io:12d}")
            
            results_sorting.append({
                'buffer_size': buffer_kb,
                'b_pages': b_pages,
                'runs': result['runs_generated'],
                'tiempo_fase1': result['time_phase1_sec'],
                'tiempo_fase2': result['time_phase2_sec'],
                'tiempo_total': result['time_total_sec'],
                'pages_read': result['pages_read'],
                'pages_written': result['pages_written'],
                'total_io': total_io
            })
    else:
        print("⚠ employee.bin no disponible para external sort")
    
    return results_hashing, results_sorting


def generate_table_2_4(results_hashing, results_sorting):
    print("\n" + "=" * 100)
    print("TABLA 2.4 - ANÁLISIS DE RENDIMIENTO (para copiar al PDF)")
    print("=" * 100)
    
    # Tabla EXTERNAL HASHING
    print("\n📊 TABLA 2.4.1: EXTERNAL HASHING (GROUP BY from_date en department_employee)")
    print("─" * 100)
    print(f"{'BUFFER_SIZE':^15} | {'B (pages)':^15} | {'Partitions':^15} | {'Time Phase 1':^15} | {'Time Phase 2':^15} | {'Total Time':^15} | {'I/O Total':^15}")
    print("─" * 100)
    
    for r in results_hashing:
        print(f"{r['buffer_size']:6.0f} KB      | {r['b_pages']:15d} | {r['particiones']:15d} | {r['tiempo_fase1']:15.4f} | {r['tiempo_fase2']:15.4f} | {r['tiempo_total']:15.4f} | {r['total_io']:15d}")
    
    print("─" * 100)
    
    # Tabla EXTERNAL SORTING
    if results_sorting:
        print("\n📊 TABLA 2.4.2: EXTERNAL SORTING (ORDER BY hire_date en employee)")
        print("─" * 100)
        print(f"{'BUFFER_SIZE':^15} | {'B (pages)':^15} | {'Runs Generated':^15} | {'Time Phase 1':^15} | {'Time Phase 2':^15} | {'Total Time':^15} | {'I/O Total':^15}")
        print("─" * 100)
        
        for r in results_sorting:
            print(f"{r['buffer_size']:6.0f} KB      | {r['b_pages']:15d} | {r['runs']:15d} | {r['tiempo_fase1']:15.4f} | {r['tiempo_fase2']:15.4f} | {r['tiempo_total']:15.4f} | {r['total_io']:15d}")
        
        print("─" * 100)

def main():
    print("\n" + "=" * 100)
    print("LAB05: ANÁLISIS DE RENDIMIENTO (Pregunta 2.4)")
    print("=" * 100)
    
    # Paso 1: Datos
    try:
        setup_data()
    except Exception as e:
        print(f"❌ Error en setup: {e}")
        return
    
    # Paso 2: Ejecutar análisis
    try:
        results_hashing, results_sorting = run_performance_analysis()
    except Exception as e:
        print(f"❌ Error en análisis: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Paso 3: Generar tabla
    try:
        generate_table_2_4(results_hashing, results_sorting)
    except Exception as e:
        print(f"❌ Error generando tabla: {e}")
        return
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()

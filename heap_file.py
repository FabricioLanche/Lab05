import struct
import csv
import os
from dataclasses import dataclass

@dataclass
class EmployeeRecord:
    PAGE_ID: int
    EMPLOYEE_ID: int
    BIRTH_DATE: str
    FIRST_NAME: str
    LAST_NAME: str 
    GENDER: chr
    HIRE_DATE: str
    RECORD_FORMAT: str = '2i20s20s20sc20s'
    RECORD_SIZE: int = struct.calcsize(RECORD_FORMAT)

@dataclass
class DepartmentRecord:
    PAGE_ID: int
    EMPLOYEE_ID: int
    DEPARTMENT_ID: str
    FROM_DATE: str
    TO_DATE: str
    RECORD_FORMAT: str = '2i10s20s20s'
    RECORD_SIZE: int = struct.calcsize(RECORD_FORMAT)

# Exporta un CSV a un heap file binario paginado.
def export_to_heap(csv_path: str, heap_path: str, record_format: str, page_size: int):
    output_dir = os.path.dirname(heap_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    record_size = struct.calcsize(record_format)
    records_per_page = page_size // record_size
    
    if record_format == EmployeeRecord.RECORD_FORMAT:
        def transform(r, p_id):
            return (p_id, int(r[0]), r[1].encode('utf-8')[:20], r[2].encode('utf-8')[:20], 
                    r[3].encode('utf-8')[:20], r[4].encode('utf-8')[:1], r[5].encode('utf-8')[:20])
    elif record_format == DepartmentRecord.RECORD_FORMAT:
        def transform(r, p_id):
            return (p_id, int(r[0]), r[1].encode('utf-8')[:10], r[2].encode('utf-8')[:20], 
                    r[3].encode('utf-8')[:20])
    
    print("===[Configuración de la exportación]===",
          f"\nCSV de entrada: [{csv_path}]",
          f"\nHeap file de salida: [{heap_path}]",
          f"\nFormato de registro: [{record_format}]",
          f"\nTamaño de página: [{page_size}Bytes]",
          f"\nRegistros por página: [{records_per_page}]",
          end="\n\n")
    
    with (
        open(csv_path, mode='r') as csv_file,
        open(heap_path, mode='wb') as bin_file
        ):
        reader = csv.reader(csv_file, delimiter=',')
        current_page_records = []
        page_id = 0
        
        for row in reader:
            formatted_row = transform(row, page_id)
            current_page_records.append(formatted_row)
            
            if len(current_page_records) == records_per_page:
                bytes_written = 0
                for rec in current_page_records:
                    data = struct.pack(record_format, *rec)
                    bin_file.write(data)
                    bytes_written += len(data)
                    
                padding = page_size - bytes_written
                if padding > 0:
                    bin_file.write(b'\x00' * padding)
                
                page_id += 1
                current_page_records = []

        if current_page_records:
            bytes_written = 0
            for rec in current_page_records:
                data = struct.pack(record_format, *rec)
                bin_file.write(data)
                bytes_written += len(data)
            
            padding = page_size - bytes_written
            if padding > 0:
                bin_file.write(b'\x00' * padding)
    print(f"Exportación completada, se han escrito [{page_id + 1}] páginas", end="\n\n")

# Lee una página del heap file y retorna sus registros.
def read_page(heap_path: str, page_id: int, record_format: str, page_size: int) -> list[tuple]:
    record_size = struct.calcsize(record_format)
    records = []
    if not os.path.exists(heap_path): return []

    with open(heap_path, 'rb') as bin_file:
        bin_file.seek(page_id * page_size)
        page_data = bin_file.read(page_size)
        for i in range(0, len(page_data) - record_size + 1, record_size):
            chunk = page_data[i:i+record_size]
            if len(chunk) < record_size:
                break
            if chunk == b'\x00' * record_size: break
            records.append(struct.unpack(record_format, chunk))
    return records

# Escribe una lista de registros en la página indicada.
def write_page(heap_path: str, page_id: int, records: list[tuple], record_format: str, page_size: int):
    mode = 'rb+' if os.path.exists(heap_path) else 'wb'
    with open(heap_path, mode) as bin_file:
        bin_file.seek(page_id * page_size)
        bytes_written = 0
        for rec in records:
            data = struct.pack(record_format, *rec)
            bin_file.write(data)
            bytes_written += len(data)
        
        padding = page_size - bytes_written
        if padding > 0:
            bin_file.write(b'\x00' * padding)

# Retorna el número total de páginas del heap file.
def count_pages(heap_path: str, page_size: int) -> int:
    if not os.path.exists(heap_path): return 0
    return os.path.getsize(heap_path) // page_size
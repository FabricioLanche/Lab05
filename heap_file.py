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

@dataclass
class DepartmentRecord:
    PAGE_ID: int
    EMPLOYEE_ID: int
    DEPARMENT_ID: str
    FROM_DATE: str
    TO_DATE: str

class HeapFile:
    EMPLOYEE_RECORD_FORMAT = '2i20s20s20sc20s'
    DEPARTMENT_RECORD_FORMAT = '2i10s20s20s'
    
    # Exporta un CSV a un heap file binario paginado.
    def export_to_heap(self, csv_path: str, heap_path: str, record_format: str, page_size_KB: int):
        page_size = page_size_KB * 1024
        record_size = struct.calcsize(record_format)
        records_per_page = page_size // record_size
        
        if record_format == self.EMPLOYEE_RECORD_FORMAT:
            def transform(r, p_id):
                return (p_id, int(r[0]), r[1].encode('utf-8')[:20], r[2].encode('utf-8')[:20], 
                        r[3].encode('utf-8')[:20], r[4].encode('utf-8')[:1], r[5].encode('utf-8')[:20])
        elif record_format == self.DEPARTMENT_RECORD_FORMAT:
            def transform(r, p_id):
                return (p_id, int(r[0]), r[1].encode('utf-8')[:10], r[2].encode('utf-8')[:20], 
                        r[3].encode('utf-8')[:20])
        
        print(f"Exportando [{csv_path}] a [{heap_path}] con formato [{record_format}] y tamaño de página [{page_size_KB}KB]...")
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

    # Lee una página del heap file y retorna sus registros.
    def read_page(self, heap_path: str, page_id: int, record_format: str, page_size_kb: int) -> list[tuple]:
        page_size = page_size_kb * 1024
        record_size = struct.calcsize(record_format)
        records = []
        if not os.path.exists(heap_path): return []

        with open(heap_path, 'rb') as bin_file:
            bin_file.seek(page_id * page_size)
            page_data = bin_file.read(page_size)
            for i in range(0, page_size - record_size + 1, record_size):
                chunk = page_data[i:i+record_size]
                if chunk == b'\x00' * record_size: break
                records.append(struct.unpack(record_format, chunk))
        return records

    # Escribe una lista de registros en la página indicada.
    def write_page(self, heap_path: str, page_id: int, records: list[tuple], record_format: str, page_size_KB: int):
        mode = 'rb+' if os.path.exists(heap_path) else 'wb'
        with open(heap_path, mode) as bin_file:
            bin_file.seek(page_id * page_size_KB * 1024)
            bytes_written = 0
            for rec in records:
                data = struct.pack(record_format, *rec)
                bin_file.write(data)
                bytes_written += len(data)
            
            padding = page_size_KB * 1024 - bytes_written
            if padding > 0:
                bin_file.write(b'\x00' * padding)

    # Retorna el número total de páginas del heap file.
    def count_pages(self, heap_path: str, page_size_KB: int) -> int:
        if not os.path.exists(heap_path): return 0
        return os.path.getsize(heap_path) // (page_size_KB * 1024)
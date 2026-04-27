import os
import tempfile
import time
import hashlib
from heap_file import (
    DepartmentRecord,
    count_pages,
    read_page,
    write_page,
)

_DEPARTMENT_FIELDS = [
    "page_id",
    "employee_id",
    "department_id",
    "from_date",
    "to_date",
]

def _normalize_field_name(field_name: str) -> str:
    return field_name.strip().casefold().replace(" ", "_")


def _resolve_group_index(fieldnames: list[str], group_key: str) -> int:
    #Encuentra el indice de la columna a agrupar
    
    #Filtrado y normalizacion de nombres de campos
    normalized_group_key = _normalize_field_name(group_key)
    normalized_map = {
        _normalize_field_name(field_name): index 
        for index, field_name in enumerate(fieldnames)
    }
    if "department_id" in normalized_map and "deparment_id" not in normalized_map:
        normalized_map["deparment_id"] = normalized_map["department_id"]

    if normalized_group_key in normalized_map:
        return normalized_map[normalized_group_key]

    raise ValueError(
        f"Group key '{group_key}' was not found in schema fields: {', '.join(fieldnames)}"
    )

def _hash_value(value: object) -> int:
    return int(hashlib.md5(str(value).strip().encode()).hexdigest(), 16)

def _to_text(value: object) -> str:
    if isinstance(value, bytes):
        return value.rstrip(b"\x00").decode("utf-8", errors="ignore")
    return str(value).strip()

def _record_capacity(page_size: int, record_size: int) -> int:
    capacity = page_size // record_size
    if capacity <= 0:
        raise ValueError("Invalid page_size/record_size combination")
    return capacity


def _build_metadata() -> dict:
    return {
        "record_format": DepartmentRecord.RECORD_FORMAT,
        "record_size": DepartmentRecord.RECORD_SIZE,
        "fields": _DEPARTMENT_FIELDS,
    }


def _chunk_records(records: list[tuple], chunk_size: int):
    for start in range(0, len(records), chunk_size):
        yield records[start : start + chunk_size]

#Fase 1: Particionamiento
# Ademas de retornar la lista de rutas de particiones, se retornara tambien la 
# cantidad de paginas leidas y escritas durante esta fase, necesarias para la fase 3
# Asimismo, para la fase 2 se retorna el metadata del heap file para evitar leer nuevamente
def partition_data(
    heap_path: str,
    page_size: int,
    buffer_size: int,
    group_key: str,
) -> tuple[list[str], int, int, dict]:
    metadata = _build_metadata()

    group_index = _resolve_group_index(metadata["fields"], group_key)
    capacity = _record_capacity(page_size, metadata["record_size"])

    # Numero de particiones = B - 1 (one buffer for input, k for output)
    b_pages = max(buffer_size // page_size, 1)
    k_partitions = max(b_pages - 1, 1)

    total_pages = count_pages(heap_path, page_size)
    
    pages_read = 0
    pages_written = 0

    # Crear archivos temporales para el particionamiento
    partition_files: list[list[tuple]] = [[] for _ in range(k_partitions)]
    partition_paths: list[str] = []
    
    for i in range(k_partitions):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".dat", prefix=f"ehash_part_{i}_")
        temp_file.close()
        partition_paths.append(temp_file.name)
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

    # Fase 1: Leer todas las páginas y distribuir registros a las particiones
    for page_id in range(total_pages):
        records = read_page(heap_path, page_id, metadata["record_format"], page_size)
        pages_read += 1
        
        for record in records:
            group_value = record[group_index]
            partition_id = _hash_value(group_value) % k_partitions
            partition_files[partition_id].append(record)

    # Escribir los archivos de partición a disco
    for partition_id, records in enumerate(partition_files):
        for page_id, chunk in enumerate(_chunk_records(records, capacity)):
            write_page(
                partition_paths[partition_id],
                page_id,
                chunk,
                metadata["record_format"],
                page_size
            )
            pages_written += 1

    return partition_paths, pages_read, pages_written, metadata

# Fase 2: Construcción y Agregación
#Ademas del diccionario de valores para el group by, retorna la cantidad
# de paginas leidas (no escribe ninguna pagia -> pages_written = 0)
# No se utiliza el atributo buffer_size en esta fase, ya que cada particion cabe completamente 
# en memoria (asegurado por la Fase 1)

def aggregate_partitions(
    partition_paths: list[str], page_size: int, buffer_size: int, group_key: str, metadata: dict) -> tuple[dict, int]:
    
    group_index = _resolve_group_index(metadata["fields"], group_key)

    result: dict[str, int] = {}
    pages_read = 0

    # Procesar cada particion
    for partition_path in partition_paths:
        if not os.path.exists(partition_path) or os.path.getsize(partition_path) == 0:
            continue

        total_pages = count_pages(partition_path, page_size)
         # Leer pagina a pagina y agregar directamente al resultado

        for page_id in range(total_pages):
            for record in read_page(partition_path, page_id, metadata["record_format"], page_size):
                group_value = _to_text(record[group_index])
                result[group_value] = result.get(group_value, 0) + 1
            pages_read += 1

    return result, pages_read


def external_hash_group_by(
    heap_path: str,
    page_size: int,
    buffer_size: int,
    group_key: str,
) -> dict:
    start_total = time.perf_counter()

    # Fase 1: Particionamiento
    start_phase1 = time.perf_counter()
    partition_paths, pages_read_phase1, pages_written_phase1, metadata = partition_data(
        heap_path,
        page_size,
        buffer_size,
        group_key,
    )
    time_phase1 = time.perf_counter() - start_phase1

    # Fase 2: Construcción y Agregación
    start_phase2 = time.perf_counter()
    result, pages_read_phase2 = aggregate_partitions(
        partition_paths,
        page_size,
        buffer_size,
        group_key,
        metadata,
    )
    time_phase2 = time.perf_counter() - start_phase2

    time_total = time.perf_counter() - start_total

    # Limpiar archivos de partición
    for partition_path in partition_paths:
        if os.path.exists(partition_path):
            os.unlink(partition_path)

    return {
        "result": result,
        "partitions_created": len(partition_paths),
        "pages_read": pages_read_phase1 + pages_read_phase2,
        "pages_written": pages_written_phase1,
        "time_phase1_sec": time_phase1,
        "time_phase2_sec": time_phase2,
        "time_total_sec": time_total,
    }
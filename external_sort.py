import os
import math
import heapq
import shutil
import tempfile
from datetime import datetime
from heap_file import (
    EmployeeRecord,
    export_to_heap,
    read_page,
    write_page,
    count_pages,
)

RECORD_FORMAT = EmployeeRecord.RECORD_FORMAT
RECORD_SIZE = EmployeeRecord.RECORD_SIZE

SORT_KEY_INDEX = {
    "hire_date": 6,
    "birth_date": 2,
    "employee_id": 1,
    "first_name": 3,
    "last_name": 4,
}

def _get_sort_val(record: tuple, sort_key: str):
    val = record[SORT_KEY_INDEX[sort_key]]
    return val.rstrip(b'\x00') if isinstance(val, bytes) else val

class HeapEntry:
    def __init__(self, val, run_idx, rec):
        self.val = val
        self.run_idx = run_idx
        self.rec = rec
    def __lt__(self, other):
        return self.val < other.val

def generate_runs(heap_path: str, page_size: int, buffer_size: int, sort_key: str = "hire_date") -> tuple[list[str], int, int]:
    B = buffer_size // page_size
    records_per_page = page_size // RECORD_SIZE
    total_pages = count_pages(heap_path, page_size)
    num_runs = math.ceil(total_pages / B)
    run_paths = []
    pages_read = 0
    pages_written = 0
    
    page_cursor = 0
    while len(run_paths) < num_runs and page_cursor < total_pages:
        records_in_ram = []
        pages_loaded = 0
        while pages_loaded < B and page_cursor < total_pages:
            page_records = read_page(heap_path, page_cursor, RECORD_FORMAT, page_size)
            if page_records:
                pages_read += 1
            records_in_ram.extend(page_records)
            page_cursor += 1
            pages_loaded += 1

        records_in_ram.sort(key=lambda r: _get_sort_val(r, sort_key))

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
        tmp.close()
        run_paths.append(tmp.name)

        run_page_id = 0
        for i in range(0, len(records_in_ram), records_per_page):
            chunk = records_in_ram[i: i + records_per_page]
            write_page(tmp.name, run_page_id, chunk, RECORD_FORMAT, page_size)
            pages_written += 1
            run_page_id += 1

    return run_paths, pages_read, pages_written


def __merge_run_group(group_paths: list[str], output_path: str, page_size: int, sort_key: str = "hire_date") -> tuple[int, int]:
    records_per_page = page_size // RECORD_SIZE
    pages_read = 0
    pages_written = 0

    run_state = {}
    for idx, path in enumerate(group_paths):
        buf = read_page(path, 0, RECORD_FORMAT, page_size)
        if buf:
            pages_read += 1
        run_state[idx] = {"buf": buf, "buf_pos": 0, "page_cursor": 1, "path": path}

    heap = []
    for idx in range(len(group_paths)):
        state = run_state[idx]
        if state["buf"]:
            rec = state["buf"][0]
            state["buf_pos"] = 1
            heapq.heappush(heap, HeapEntry(_get_sort_val(rec, sort_key), idx, rec))

    output_buf = []
    current_out_page_id = 0

    while heap:
        entry = heapq.heappop(heap)
        run_idx, rec = entry.run_idx, entry.rec
        output_buf.append(rec)

        if len(output_buf) == records_per_page:
            write_page(output_path, current_out_page_id, output_buf, RECORD_FORMAT, page_size)
            pages_written += 1
            current_out_page_id += 1
            output_buf = []

        state = run_state[run_idx]
        if state["buf_pos"] < len(state["buf"]):
            next_rec = state["buf"][state["buf_pos"]]
            state["buf_pos"] += 1
            heapq.heappush(heap, HeapEntry(_get_sort_val(next_rec, sort_key), run_idx, next_rec))
        else:
            next_page = read_page(state["path"], state["page_cursor"], RECORD_FORMAT, page_size)
            if next_page:
                pages_read += 1
                state["buf"] = next_page
                state["buf_pos"] = 1
                state["page_cursor"] += 1
                heapq.heappush(heap, HeapEntry(_get_sort_val(next_page[0], sort_key), run_idx, next_page[0]))

    if output_buf:
        write_page(output_path, current_out_page_id, output_buf, RECORD_FORMAT, page_size)
        pages_written += 1

    return pages_read, pages_written


def multiway_merge(run_paths: list[str], output_path: str, page_size: int, buffer_size: int, sort_key: str = "hire_date") -> tuple[int, int]:
    B = buffer_size // page_size
    fan_in = B - 1
    pages_read = 0
    pages_written = 0

    if not run_paths:
        open(output_path, "wb").close()
        return pages_read, pages_written

    if fan_in < 2 and len(run_paths) > 1:
        raise ValueError("buffer_size demasiado pequeño: se requieren al menos 3 páginas para hacer merge multiway")

    current_runs = list(run_paths)
    while len(current_runs) > 1:
        next_runs = []
        for i in range(0, len(current_runs), fan_in):
            group = current_runs[i:i + fan_in]
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
            tmp.close()

            group_read, group_written = __merge_run_group(group, tmp.name, page_size, sort_key)
            pages_read += group_read
            pages_written += group_written
            next_runs.append(tmp.name)

            for path in group:
                os.remove(path)

        current_runs = next_runs

    final_run = current_runs[0]
    if os.path.abspath(final_run) != os.path.abspath(output_path):
        shutil.move(final_run, output_path)

    return pages_read, pages_written


def external_sort(heap_path: str, output_path: str, page_size: int, buffer_size: int, sort_key: str = "hire_date") -> dict:
    t0 = datetime.now()
    run_paths, phase1_pages_read, phase1_pages_written = generate_runs(heap_path, page_size, buffer_size, sort_key)
    t1 = datetime.now()

    phase2_pages_read, phase2_pages_written = multiway_merge(run_paths, output_path, page_size, buffer_size, sort_key)
    t2 = datetime.now()

    pages_read = phase1_pages_read + phase2_pages_read
    pages_written = phase1_pages_written + phase2_pages_written

    return {
        "runs_generated": len(run_paths),
        "pages_read": pages_read,
        "pages_written": pages_written,
        "time_phase1_sec": (t1 - t0).total_seconds(),
        "time_phase2_sec": (t2 - t1).total_seconds(),
        "time_total_sec": (t2 - t0).total_seconds(),
    }

if __name__ == "__main__":
    export_to_heap("data_input/employee.csv", "data/employee.bin", EmployeeRecord.RECORD_FORMAT, 4096)
    heap_path = "data/employee.bin"
    output_path = "data/employee_sorted.bin"
    page_size = 4096
    buffer_size = 65536
    metrics = external_sort(heap_path, output_path, page_size, buffer_size)
    print(metrics)
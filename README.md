# Lab05: External Algorithms - External Hashing y External Sorting

## Descripción

Implementación educativa de dos algoritmos de **memoria externa** en Python que simulan restricciones severas de RAM (buffer limitado a 64KB, 128KB, 256KB):

1. **External Hashing** - Resuelve `GROUP BY` en datos que no caben en memoria
2. **External Sorting** - Ordena grandes datasets usando Two-Phase Multiway Merge Sort (TPMMS)

---

## External Hashing: Conceptos Clave

### ¿Qué hace?
Implementa un **GROUP BY** distribuido en dos fases cuando los datos no caben en RAM:

- **Fase 1 (Particionamiento)**: Lee el archivo página a página, aplica función hash `h_p(group_key) % k` para distribuir registros en `k` particiones temporales en disco
- **Fase 2 (Agregación)**: Para cada partición, carga en memoria, construye tabla hash con `h_r(group_key)`, acumula `COUNT(*)`


### Ejemplo:
```python
from external_hashing import external_hash_group_by

result = external_hash_group_by(
    'data/department_employee.bin',  # Archivo binario paginado
    page_size=4096,
    buffer_size=65536,               # 64KB
    group_key='from_date'            # Agrupar por
)

# Retorna:
{
    'result': {fecha: count, ...},  # Resultado del GROUP BY
    'pages_read': 5230,              # Páginas leídas (ambas fases)
    'pages_written': 2618,           # Páginas escritas (solo Fase 1)
    'time_phase1_sec': 70.2,         # Tiempo particionamiento
    'time_phase2_sec': 2.8,          # Tiempo agregación
    'time_total_sec': 73.0
}
```

---

## External Sorting (TPMMS): Conceptos Clave

### ¿Qué hace?
Implementa un **ORDER BY** distribuido usando **Two-Phase Multiway Merge Sort (TPMMS)** cuando los datos no caben en RAM:

- **Fase 1 (Generación de Runs)**: Lee el archivo página a página en buffers de B páginas, ordena cada buffer en memoria con sort convencional, escribe resultados como "runs" ordenados a archivos temporales. Genera `ceil(total_pages / B)` runs
- **Fase 2 (Multiway Merge)**: Realiza k-way merge iterativo (k = B-1) sobre los runs. Si hay más de k runs, hace pasadas múltiples combinando grupos de k runs hasta obtener un solo archivo ordenado

### Ejemplo:
```python
from external_file import external_sort

result = external_sort(
    'data/employee.bin',           # Archivo binario paginado
    'data/employee_sorted.bin',    # Output ordenado
    page_size=4096,
    buffer_size=65536,             # 64KB
    sort_key='hire_date'           # Ordenar por
)

# Retorna:
{
    'runs_generated': 417,          # Número de runs en Fase 1
    'pages_read': 53344,            # Páginas leídas (ambas fases)
    'pages_written': 53344,         # Páginas escritas (ambas fases)
    'time_phase1_sec': 156.26,      # Tiempo generación de runs
    'time_phase2_sec': 482.84,      # Tiempo multiway merge
    'time_total_sec': 639.10
}
```

### Diferencia Clave vs External Hashing:
| Aspecto | External Hashing | External Sorting |
|---|---|---|
| Problema | GROUP BY | ORDER BY |
| Fase 1 | Hash distribution → k particiones | Sort & write → ceil(N/B) runs |
| Fase 2 | Aggregate en memoria | k-way merge iterativo |
| Escalabilidad | Lineal en datos | O(N log(N/B)) comparaciones |
| Overhead Fase 1 | Bajo (solo hash) | Alto (sort en memoria) |
| Overhead Fase 2 | Bajo (simple aggregation) | Alto (k-way heap merge) |

---

## Cómo Usar

### **1. Ejecutar Análisis Completo (Ambos Algoritmos)**

```powershell
python performance_analysis.py
```

---

### External Hashing (department_employee, 334009 registros)

| Buffer Size | B | Particiones | Phase 1 (s) | Phase 2 (s) | Total (s) | I/O (pags) |
|---|---|---|---|---|---|---|
| 64 KB | 16 | 15 | 1.55 | 0.40 | 1.95 | 14226 |
| 128 KB | 32 | 31 | 1.52 | 0.38 | 1.91 | 14242 |
| 256 KB | 64 | 63 | 1.48 | 0.35 | 1.83 | 14278 |


### External Sorting (employee, ~480K registros)

| Buffer Size | B | Runs | Phase 1 (s) | Phase 2 (s) | Total (s) | I/O (pags) |
|---|---|---|---|---|---|---|
| 64 KB | 16 | 408 | 0.75 | 3.26 | 4.01 | 52184 |
| 128 KB | 32 | 204 | 0.85 | 2.53 | 3.38 | 39138 |
| 256 KB | 64 | 102 | 0.82 | 2.29 | 3.11 | 39138 |

---

## Interpretación de Resultados

### External Hashing - Análisis
- **Phase 1 (Particionamiento)** disminuye ligeramente al aumentar el buffer (1.55s -> 1.48s), aunque crece el número de particiones (15 -> 63).
- **Phase 2 (Agregación)** se mantiene baja y también disminuye levemente (0.40s -> 0.35s).
- **I/O Total** permanece casi constante y con variación pequeña (14226 -> 14278 páginas).
- **Conclusión**: En este escenario de `GROUP BY from_date`, hashing mantiene buen escalamiento y menor tiempo total.

### External Sorting - Análisis
- **Phase 1** es baja y relativamente estable (0.75s, 0.85s, 0.82s).
- **Phase 2 (Multiway Merge)** sigue siendo la fase dominante, pero mejora al aumentar el buffer (3.26s -> 2.29s).
- **Runs generados** se reducen a la mitad al duplicar buffer (408 -> 204 -> 102), consistente con TPMMS.
- **I/O Total** baja de 52184 a 39138 páginas y luego se estabiliza.
- **Conclusión**: Sorting mejora con más memoria, especialmente por menor costo de merge y menos runs.

---

### **Para la generación de gráficas: Instalar Matplotlib**

```powershell
pip install matplotlib
```
**Última actualización**: Abril 2026  
**Profesor**: Heider Sánchez (UTEC)  
**Curso**: Base de Datos II
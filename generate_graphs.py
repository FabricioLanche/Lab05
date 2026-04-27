import matplotlib.pyplot as plt
from pathlib import Path

# DATOS DE TABLA: EXTERNAL HASHING

HASHING_DATA = {
    'buffer_sizes_kb': [64, 128, 256],      # Buffer Size (KB)
    'tiempo_total': [1.9502, 1.9066, 1.8268],     # Total Time (s)
    'tiempo_fase1': [1.5506, 1.5234, 1.4756],      # Time Phase 1 (s)
    'tiempo_fase2': [0.3996, 0.3833, 0.3512],      # Time Phase 2 (s)
    'io_total': [14226, 14242, 14278],             # I/O Total (pages)
    'particiones': [15, 31, 63],                   # Partitions (k = B-1)
}

# DATOS DE TABLA: EXTERNAL SORTING

SORTING_DATA = {
    'buffer_sizes_kb': [64, 128, 256],      # Buffer Size (KB)
    'tiempo_total': [4.0109, 3.3836, 3.1057],       # Total Time (s)
    'tiempo_fase1': [0.7461, 0.8534, 0.8168],       # Time Phase 1 (s)
    'tiempo_fase2': [3.2648, 2.5302, 2.2888],       # Time Phase 2 (s)
    'io_total': [52184, 39138, 39138],              # I/O Total (pages)
    'runs_generated': [408, 204, 102],              # Runs Generated
}


# INSTRUCCIONES PARA ACTUALIZAR DATOS:
#
#1. Ejecuta: python performance_analysis.py
#2. Cuando termine, copia las TABLAS de la consola
#3. Reemplaza los valores en HASHING_DATA y SORTING_DATA arriba
#4. Luego ejecuta: python generate_graphs.py

def generate_all_graphs():
    
    output_dir = Path("graphs")
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 100)
    print("GENERANDO GRÁFICAS A PARTIR DE DATOS TABULARES")
    print("=" * 100)
    
    # Validar que hay datos de Hashing
    if not HASHING_DATA['tiempo_total'] or None in HASHING_DATA['tiempo_total']:
        print("⚠ Datos de External Hashing incompletos. Actualiza HASHING_DATA arriba.")
        return
    
    # GRÁFICA 1: COMPARACIÓN DE TIEMPO TOTAL
    print("\n📊 Gráfica 1: Comparación de Tiempo Total vs BUFFER_SIZE")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(HASHING_DATA['buffer_sizes_kb'], HASHING_DATA['tiempo_total'], 
            'o-', linewidth=3, markersize=12, label='External Hashing', 
            color='#FF6B6B', markeredgewidth=2, markeredgecolor='darkred')
    
    if SORTING_DATA['tiempo_total'] and None not in SORTING_DATA['tiempo_total']:
        ax.plot(SORTING_DATA['buffer_sizes_kb'], SORTING_DATA['tiempo_total'], 
                's-', linewidth=3, markersize=12, label='External Sorting', 
                color='#4ECDC4', markeredgewidth=2, markeredgecolor='darkblue')
    
    ax.set_xlabel('BUFFER_SIZE (KB)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Tiempo Total (segundos)', fontsize=13, fontweight='bold')
    ax.set_title('Lab05: Comparación de Tiempo Total - Ambos Algoritmos', 
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.4, linestyle='--')
    ax.legend(fontsize=12, loc='best')
    ax.set_xticks(HASHING_DATA['buffer_sizes_kb'])
    
    plt.tight_layout()
    graph_path = output_dir / "01_comparacion_tiempo_total.png"
    plt.savefig(str(graph_path), dpi=300, bbox_inches='tight')
    print(f"✅ Guardado: {graph_path}")
    plt.close()
    
    # GRÁFICA 2: DESGLOSE POR FASES
    print("📊 Gráfica 2: Desglose de Tiempos por Fase")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Lab05: Desglose de Tiempos por Fase', fontsize=16, fontweight='bold')
    
    # Gráfica 2.1: Hashing
    ax = axes[0]
    x = range(len(HASHING_DATA['buffer_sizes_kb']))
    width = 0.35
    
    bars1 = ax.bar([i - width/2 for i in x], HASHING_DATA['tiempo_fase1'], width, 
                   label='Phase 1 (Partitioning)', color='#95E1D3')
    bars2 = ax.bar([i + width/2 for i in x], HASHING_DATA['tiempo_fase2'], width, 
                   label='Phase 2 (Aggregation)', color='#F38181')
    
    ax.set_xlabel('BUFFER_SIZE (KB)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Tiempo (segundos)', fontsize=11, fontweight='bold')
    ax.set_title('External Hashing: Desglose por Fase', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'{int(b)} KB' for b in HASHING_DATA['buffer_sizes_kb']])
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Gráfica 2.2: Sorting
    if SORTING_DATA['tiempo_fase1'] and None not in SORTING_DATA['tiempo_fase1']:
        ax = axes[1]
        bars1 = ax.bar([i - width/2 for i in x], SORTING_DATA['tiempo_fase1'], width, 
                       label='Phase 1 (Run Generation)', color='#AA96DA')
        bars2 = ax.bar([i + width/2 for i in x], SORTING_DATA['tiempo_fase2'], width, 
                       label='Phase 2 (Multiway Merge)', color='#FCBAD3')
        
        ax.set_xlabel('BUFFER_SIZE (KB)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Tiempo (segundos)', fontsize=11, fontweight='bold')
        ax.set_title('External Sorting: Desglose por Fase', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([f'{int(b)} KB' for b in SORTING_DATA['buffer_sizes_kb']])
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
    else:
        ax = axes[1]
        ax.text(0.5, 0.5, 'Esperando datos de External Sorting...', 
                ha='center', va='center', fontsize=12, transform=ax.transAxes)
        ax.set_title('External Sorting: Desglose por Fase', fontsize=12, fontweight='bold')
        ax.axis('off')
    
    plt.tight_layout()
    graph_path = output_dir / "02_desglose_fases.png"
    plt.savefig(str(graph_path), dpi=300, bbox_inches='tight')
    print(f"✅ Guardado: {graph_path}")
    plt.close()
    
    print("\n" + "=" * 100)
    print("✅ GRÁFICAS GENERADAS EN: graphs/")
    print("=" * 100)
    print("""
Archivos creados:
1. 01_comparacion_tiempo_total.png  ← Comparación tiempo total
2. 02_desglose_fases.png            ← Desglose por fases
""")


def main():
    print("\n" + "=" * 100)
    print("Generador de Gráficas - Lab05 Sección 2.4")
    print("=" * 100)
    
    # Validar datos
    if not HASHING_DATA['tiempo_total'] or None in HASHING_DATA['tiempo_total']:
        print("\n⚠️  ATENCIÓN:")
        print("   Los datos de HASHING_DATA no están completos.")
        print("   ")
        print("   INSTRUCCIONES:")
        print("   1. Ejecuta: python performance_analysis.py")
        print("   2. Cuando termine, copia los datos de la TABLA 2.4.1 (External Hashing)")
        print("   3. Reemplaza los valores en HASHING_DATA arriba en este archivo")
        print("   4. (Opcional) Si termina external sort, también reemplaza SORTING_DATA")
        print("   5. Luego ejecuta: python generate_graphs.py")
        print("\n")
        return
    
    try:
        generate_all_graphs()
    except Exception as e:
        print(f"❌ Error generando gráficas: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    main()

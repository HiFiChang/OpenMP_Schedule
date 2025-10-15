import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def plot_schedule_comparison_combined(df):
    """
    绘制不同调度策略（使用默认块大小）与基线的性能对比图。
    左侧 loop1，右侧 loop2。
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    loop_names = ['loop1_time_s', 'loop2_time_s']
    loop_titles = ['Loop 1', 'Loop 2']
    
    for idx, (loop_name, loop_title) in enumerate(zip(loop_names, loop_titles)):
        ax = axes[idx]
        
        # 筛选出 'default' 块大小和 'baseline' 的数据
        default_df = df[df['chunk_size'] == 'default']
        baseline_df = df[df['schedule'] == 'baseline']
        
        print(f"\n=== Debugging {loop_name} ===")
        print(f"Default chunk data shape: {default_df.shape}")
        print(f"Baseline data shape: {baseline_df.shape}")
        
        # 绘制不同调度策略的性能曲线
        for schedule in ['static', 'dynamic', 'guided']:
            schedule_df = default_df[default_df['schedule'] == schedule].sort_values('N')
            if not schedule_df.empty:
                ax.plot(schedule_df['N'], schedule_df[loop_name], marker='o', linestyle='-', 
                       label=f'{schedule.capitalize()}', linewidth=2)
                print(f"{schedule} data points: {len(schedule_df)}")

        # 绘制基线
        baseline_df = baseline_df.sort_values('N')
        if not baseline_df.empty:
            ax.plot(baseline_df['N'], baseline_df[loop_name], marker='x', linestyle='--', 
                   label='Baseline (1 thread)', linewidth=2, markersize=10)
            print(f"Baseline data points: {len(baseline_df)}")

        ax.set_title(f'{loop_title}: Schedule Comparison', fontsize=12, fontweight='bold')
        ax.set_xlabel('Matrix Size (N)', fontsize=11)
        ax.set_ylabel('Time (s)', fontsize=11)
        
        # 获取所有唯一的 N 值并设置为 x 轴刻度
        n_values = sorted(df['N'].unique())
        ax.set_xticks(n_values)
        ax.set_xticklabels([str(n) for n in n_values], rotation=45)
        
        ax.legend(fontsize=9)
        ax.grid(True, which="both", ls="--", alpha=0.5)
    
    plt.tight_layout()
    
    # 保存图表
    output_filename = 'schedule_comparison_combined.png'
    plt.savefig(output_filename, dpi=150)
    print(f"\nGenerated plot: {output_filename}")
    plt.close()

def plot_chunk_size_comparison_combined(df, schedule_type='dynamic'):
    """
    针对给定的调度策略，绘制不同块大小的性能对比图。
    左侧 loop1，右侧 loop2。
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    loop_names = ['loop1_time_s', 'loop2_time_s']
    loop_titles = ['Loop 1', 'Loop 2']
    
    for idx, (loop_name, loop_title) in enumerate(zip(loop_names, loop_titles)):
        ax = axes[idx]
        
        # 筛选出特定调度策略的数据
        schedule_df = df[df['schedule'] == schedule_type].copy()
        
        # 将 chunk_size 转换为数值类型以便排序和绘图
        schedule_df['chunk_size'] = pd.to_numeric(schedule_df['chunk_size'], errors='coerce')
        schedule_df.dropna(subset=['chunk_size'], inplace=True)
        schedule_df['chunk_size'] = schedule_df['chunk_size'].astype(int)

        print(f"\n=== Chunk size comparison for {schedule_type} - {loop_name} ===")
        print(f"Available chunk sizes: {sorted(schedule_df['chunk_size'].unique())}")

        # 绘制不同块大小的性能曲线
        for chunk_size in sorted(schedule_df['chunk_size'].unique()):
            chunk_df = schedule_df[schedule_df['chunk_size'] == chunk_size].sort_values('N')
            ax.plot(chunk_df['N'], chunk_df[loop_name], marker='o', linestyle='-', 
                   label=f'Chunk: {chunk_size}', linewidth=2)
            print(f"Chunk size {chunk_size} data points: {len(chunk_df)}")

        # 叠加绘制默认块大小（不显式设置 chunk）的一条线
        default_df = df[(df['schedule'] == schedule_type) & (df['chunk_size'] == 'default')].copy()
        if not default_df.empty:
            default_df = default_df.sort_values('N')
            ax.plot(default_df['N'], default_df[loop_name], marker='s', linestyle='--',
                    color='tab:gray', label='Default chunk', linewidth=2, markersize=6)
            print(f"Default chunk data points: {len(default_df)}")

        ax.set_title(f'{loop_title}: {schedule_type.capitalize()} Schedule - Chunk Size Impact', 
                    fontsize=12, fontweight='bold')
        ax.set_xlabel('Matrix Size (N)', fontsize=11)
        ax.set_ylabel('Time (s)', fontsize=11)
        
        # 获取所有唯一的 N 值并设置为 x 轴刻度
        n_values = sorted(df['N'].unique())
        ax.set_xticks(n_values)
        ax.set_xticklabels([str(n) for n in n_values], rotation=45)
        
        ax.legend(title='Chunk Size', fontsize=9)
        ax.grid(True, which="both", ls="--", alpha=0.5)
    
    plt.tight_layout()

    # 保存图表
    output_filename = f'chunk_size_comparison_{schedule_type}_combined.png'
    plt.savefig(output_filename, dpi=150)
    print(f"\nGenerated plot: {output_filename}")
    plt.close()

def main():
    """
    主函数，用于读取数据并生成所有图表。
    """
    # 加载数据，优先使用 results 目录中的文件
    csv_files = ['results/schedule_by_n_results.csv', 'schedule_by_n_results.csv']
    df = None
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            print(f"Successfully loaded data from: {csv_file}")
            break
        except FileNotFoundError:
            continue
    
    if df is None:
        print("Error: Could not find 'schedule_by_n_results.csv' in current directory or results/ directory.")
        return

    # 设置绘图风格
    sns.set_theme(style="whitegrid")

    # --- 生成图表 ---

    # 图1: 调度策略对比 (左loop1, 右loop2)
    plot_schedule_comparison_combined(df)

    # 图2: 块大小影响 (左loop1, 右loop2) - dynamic schedule
    plot_chunk_size_comparison_combined(df, schedule_type='dynamic')

if __name__ == '__main__':
    main()

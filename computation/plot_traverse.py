import matplotlib.pyplot as plt

def plot_traverse(df):
    fig, ax = plt.subplots(figsize=(10, 8))
    groups = df.groupby('Group')
    
    for name, group in groups:
        ax.plot(group['Final_E'], group['Final_N'], marker='o', label=f"Layer: {name}")
        for _, row in group.iterrows():
            ax.text(row['Final_E'], row['Final_N'], f" {row['code']}", fontsize=7, alpha=0.7)

    ax.set_aspect('equal')
    ax.set_xlabel('Easting')
    ax.set_ylabel('Northing')
    ax.legend(loc='upper right', fontsize='small')
    ax.grid(True, linestyle=':', alpha=0.5)
    plt.title("Survey Plan - Feature Grouping View")
    return fig

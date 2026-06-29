import darkdetect
import matplotlib.pyplot as plt

def set_plt_colors():
    """Настройка цветов matplotlib в зависимости от темы системы"""
    bg = '#2b2b2b' if darkdetect.isDark() else 'white'
    fg = 'white' if darkdetect.isDark() else '#2b2b2b'

    plt.rcParams['figure.facecolor'] = bg
    plt.rcParams['axes.facecolor'] = bg
    plt.rcParams['text.color'] = fg
    plt.rcParams['axes.labelcolor'] = fg
    plt.rcParams['xtick.color'] = fg
    plt.rcParams['ytick.color'] = fg
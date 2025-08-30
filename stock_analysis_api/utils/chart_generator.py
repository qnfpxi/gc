# K线图绘制模块
import io
import base64
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
from matplotlib import font_manager
import warnings

# 忽略matplotlib警告
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

logger = logging.getLogger(__name__)

class ChartGenerator:
    """K线图生成器"""
    
    def __init__(self):
        self.setup_matplotlib()
        self.default_style = self.create_custom_style()
    
    def setup_matplotlib(self):
        """设置matplotlib环境"""
        # 设置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 设置图形参数
        plt.rcParams['figure.dpi'] = 100
        plt.rcParams['savefig.dpi'] = 300
        plt.rcParams['figure.facecolor'] = 'white'
    
    def create_custom_style(self) -> Dict[str, Any]:
        """创建自定义样式"""
        return mpf.make_mpf_style(
            base_mpl_style='default',
            marketcolors=mpf.make_marketcolors(
                up='#ff4444',      # 红色上涨
                down='#00aa00',    # 绿色下跌
                edge='inherit',
                wick={'up': '#ff4444', 'down': '#00aa00'},
                volume='in'
            ),
            mavcolors=['#1f77b4', '#ff7f0e', '#2ca02c'],  # 均线颜色
            facecolor='#f8f9fa',
            figcolor='#ffffff',
            gridcolor='#e0e0e0',
            gridstyle='-',
            y_on_right=True
        )
    
    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """准备K线图数据"""
        if df.empty:
            raise ValueError("数据为空，无法绘制K线图")
        
        # 确保必要的列存在
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"缺少必要的列: {missing_cols}")
        
        # 设置日期索引
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        elif 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df.set_index('trade_date', inplace=True)
        
        # 确保索引是日期类型
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # 数据清洗
        df = df.dropna(subset=required_cols)
        
        # 确保数据类型正确
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 按日期排序
        df = df.sort_index()
        
        return df
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        try:
            # 移动平均线
            df['MA5'] = df['close'].rolling(window=5).mean()
            df['MA10'] = df['close'].rolling(window=10).mean()
            df['MA20'] = df['close'].rolling(window=20).mean()
            df['MA60'] = df['close'].rolling(window=60).mean()
            
            # 布林带
            df['BB_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
            df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
            
            # MACD
            exp1 = df['close'].ewm(span=12).mean()
            exp2 = df['close'].ewm(span=26).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
            df['MACD_hist'] = df['MACD'] - df['MACD_signal']
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # 成交量移动平均
            df['Volume_MA5'] = df['volume'].rolling(window=5).mean()
            df['Volume_MA10'] = df['volume'].rolling(window=10).mean()
            
        except Exception as e:
            logger.warning(f"计算技术指标时出错: {e}")
        
        return df
    
    def generate_kline_chart(
        self,
        df: pd.DataFrame,
        symbol: str,
        title: Optional[str] = None,
        chart_type: str = 'candle',
        show_volume: bool = True,
        show_indicators: bool = True,
        figsize: Tuple[int, int] = (16, 12),
        return_base64: bool = True
    ) -> str:
        """
        生成K线图
        
        Args:
            df: 股票数据DataFrame
            symbol: 股票代码
            title: 图表标题
            chart_type: 图表类型 ('candle', 'ohlc', 'line')
            show_volume: 是否显示成交量
            show_indicators: 是否显示技术指标
            figsize: 图形大小
            return_base64: 是否返回base64编码的图片
            
        Returns:
            base64编码的图片字符串或文件路径
        """
        try:
            # 准备数据
            df = self.prepare_data(df.copy())
            
            if show_indicators:
                df = self.calculate_technical_indicators(df)
            
            # 设置图表标题
            if not title:
                start_date = df.index[0].strftime('%Y-%m-%d')
                end_date = df.index[-1].strftime('%Y-%m-%d')
                title = f'{symbol} K线图 ({start_date} ~ {end_date})'
            
            # 准备绘图参数
            plot_params = {
                'type': chart_type,
                'style': self.default_style,
                'title': title,
                'ylabel': '价格',
                'ylabel_lower': '成交量' if show_volume else None,
                'figsize': figsize,
                'tight_layout': True,
                'scale_padding': {'left': 0.3, 'top': 0.8, 'right': 1.0, 'bottom': 0.8}
            }
            
            # 添加移动平均线
            addplot_list = []
            
            if show_indicators:
                # 移动平均线
                ma_colors = ['blue', 'orange', 'green', 'red']
                ma_periods = [5, 10, 20, 60]
                
                for i, period in enumerate(ma_periods):
                    ma_col = f'MA{period}'
                    if ma_col in df.columns and not df[ma_col].isna().all():
                        addplot_list.append(
                            mpf.make_addplot(
                                df[ma_col],
                                color=ma_colors[i % len(ma_colors)],
                                width=1.2,
                                alpha=0.8,
                                label=f'MA{period}'
                            )
                        )
                
                # 布林带
                if all(col in df.columns for col in ['BB_upper', 'BB_lower']):
                    addplot_list.extend([
                        mpf.make_addplot(
                            df['BB_upper'],
                            color='purple',
                            linestyle='--',
                            alpha=0.6,
                            width=1
                        ),
                        mpf.make_addplot(
                            df['BB_lower'],
                            color='purple',
                            linestyle='--',
                            alpha=0.6,
                            width=1
                        )
                    ])
                
                # MACD (在单独的子图中)
                if 'MACD' in df.columns:
                    addplot_list.extend([
                        mpf.make_addplot(
                            df['MACD'],
                            panel=1,
                            color='blue',
                            secondary_y=False,
                            ylabel='MACD'
                        ),
                        mpf.make_addplot(
                            df['MACD_signal'],
                            panel=1,
                            color='red',
                            secondary_y=False
                        ),
                        mpf.make_addplot(
                            df['MACD_hist'],
                            panel=1,
                            type='bar',
                            color='gray',
                            alpha=0.6,
                            secondary_y=False
                        )
                    ])
                
                # RSI (在单独的子图中)
                if 'RSI' in df.columns:
                    addplot_list.append(
                        mpf.make_addplot(
                            df['RSI'],
                            panel=2,
                            color='purple',
                            ylabel='RSI',
                            ylim=(0, 100)
                        )
                    )
            
            if addplot_list:
                plot_params['addplot'] = addplot_list
            
            # 设置成交量
            if show_volume and 'volume' in df.columns:
                plot_params['volume'] = True
                plot_params['volume_panel'] = 1 if show_indicators else 1
            
            # 生成图表
            if return_base64:
                # 保存到内存缓冲区
                buf = io.BytesIO()
                mpf.plot(df, **plot_params, savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)
                
                # 转换为base64
                img_base64 = base64.b64encode(buf.read()).decode('utf-8')
                buf.close()
                
                return f"data:image/png;base64,{img_base64}"
            else:
                # 直接显示或保存文件
                mpf.plot(df, **plot_params)
                return "Chart generated successfully"
                
        except Exception as e:
            logger.error(f"生成K线图时出错: {e}", exc_info=True)
            raise ValueError(f"生成K线图失败: {str(e)}")
    
    def generate_comparison_chart(
        self,
        data_dict: Dict[str, pd.DataFrame],
        title: str = "股票对比图",
        figsize: Tuple[int, int] = (16, 10)
    ) -> str:
        """
        生成多股票对比图
        
        Args:
            data_dict: 股票数据字典 {symbol: DataFrame}
            title: 图表标题
            figsize: 图形大小
            
        Returns:
            base64编码的图片字符串
        """
        try:
            plt.figure(figsize=figsize)
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
            
            for i, (symbol, df) in enumerate(data_dict.items()):
                if df.empty:
                    continue
                
                df = self.prepare_data(df.copy())
                
                # 计算收益率（归一化）
                normalized_price = (df['close'] / df['close'].iloc[0]) * 100
                
                plt.plot(
                    df.index,
                    normalized_price,
                    label=symbol,
                    color=colors[i % len(colors)],
                    linewidth=2
                )
            
            plt.title(title, fontsize=16, fontweight='bold')
            plt.xlabel('日期', fontsize=12)
            plt.ylabel('相对收益率 (%)', fontsize=12)
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # 转换为base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            buf.close()
            plt.close()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"生成对比图时出错: {e}", exc_info=True)
            raise ValueError(f"生成对比图失败: {str(e)}")
    
    def generate_comprehensive_chart(
        self,
        df: pd.DataFrame,
        symbol: str,
        figsize: Tuple[int, int] = (16, 16)
    ) -> str:
        """
        生成综合分析图表（K线图+技术分析合并）
        
        Args:
            df: 股票数据DataFrame
            symbol: 股票代码
            figsize: 图形大小
            
        Returns:
            base64编码的图片字符串
        """
        try:
            df = self.prepare_data(df.copy())
            df = self.calculate_technical_indicators(df)
            
            # 使用mplfinance生成综合图表
            addplot_list = []
            
            # 添加移动平均线
            ma_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
            ma_periods = [5, 10, 20, 60]
            
            for i, period in enumerate(ma_periods):
                ma_col = f'MA{period}'
                if ma_col in df.columns and not df[ma_col].isna().all():
                    addplot_list.append(
                        mpf.make_addplot(
                            df[ma_col],
                            color=ma_colors[i],
                            width=1.5,
                            alpha=0.8
                        )
                    )
            
            # 添加布林带
            if all(col in df.columns for col in ['BB_upper', 'BB_lower']):
                addplot_list.extend([
                    mpf.make_addplot(
                        df['BB_upper'],
                        color='purple',
                        linestyle='--',
                        alpha=0.6,
                        width=1
                    ),
                    mpf.make_addplot(
                        df['BB_lower'],
                        color='purple',
                        linestyle='--',
                        alpha=0.6,
                        width=1
                    )
                ])
            
            # MACD (在子图1中)
            if 'MACD' in df.columns:
                addplot_list.extend([
                    mpf.make_addplot(
                        df['MACD'],
                        panel=1,
                        color='blue',
                        ylabel='MACD'
                    ),
                    mpf.make_addplot(
                        df['MACD_signal'],
                        panel=1,
                        color='red'
                    ),
                    mpf.make_addplot(
                        df['MACD_hist'],
                        panel=1,
                        type='bar',
                        color='gray',
                        alpha=0.6
                    )
                ])
            
            # RSI (在子图2中)
            if 'RSI' in df.columns:
                addplot_list.append(
                    mpf.make_addplot(
                        df['RSI'],
                        panel=2,
                        color='purple',
                        ylabel='RSI'
                    )
                )
            
            # 设置图表标题
            start_date = df.index[0].strftime('%Y-%m-%d')
            end_date = df.index[-1].strftime('%Y-%m-%d')
            title = f'{symbol} 综合技术分析 ({start_date} ~ {end_date})'
            
            # 生成图表
            buf = io.BytesIO()
            mpf.plot(
                df,
                type='candle',
                style=self.default_style,
                addplot=addplot_list,
                volume=True,
                title=title,
                ylabel='价格',
                ylabel_lower='成交量',
                figsize=figsize,
                savefig=dict(fname=buf, format='png', bbox_inches='tight')
            )
            buf.seek(0)
            
            # 转换为base64
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            buf.close()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"生成综合分析图时出错: {e}", exc_info=True)
            raise ValueError(f"生成综合分析图失败: {str(e)}")
    
    def generate_technical_analysis_chart(
        self,
        df: pd.DataFrame,
        symbol: str,
        figsize: Tuple[int, int] = (16, 14)
    ) -> str:
        """
        生成技术分析综合图表
        
        Args:
            df: 股票数据DataFrame
            symbol: 股票代码
            figsize: 图形大小
            
        Returns:
            base64编码的图片字符串
        """
        try:
            df = self.prepare_data(df.copy())
            df = self.calculate_technical_indicators(df)
            
            # 创建子图
            fig, axes = plt.subplots(4, 1, figsize=figsize, 
                                   gridspec_kw={'height_ratios': [3, 1, 1, 1]})
            
            # 主K线图
            ax1 = axes[0]
            
            # 绘制K线
            for i in range(len(df)):
                color = '#ff4444' if df['close'].iloc[i] >= df['open'].iloc[i] else '#00aa00'
                ax1.plot([i, i], [df['low'].iloc[i], df['high'].iloc[i]], color=color, linewidth=1)
                ax1.plot([i, i], [df['open'].iloc[i], df['close'].iloc[i]], color=color, linewidth=4)
            
            # 移动平均线
            for period, color in [(5, 'blue'), (10, 'orange'), (20, 'green'), (60, 'red')]:
                ma_col = f'MA{period}'
                if ma_col in df.columns:
                    ax1.plot(range(len(df)), df[ma_col], color=color, label=f'MA{period}', alpha=0.8)
            
            ax1.set_title(f'{symbol} 技术分析图', fontsize=14, fontweight='bold')
            ax1.set_ylabel('价格', fontsize=12)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 成交量
            ax2 = axes[1]
            colors = ['#ff4444' if df['close'].iloc[i] >= df['open'].iloc[i] else '#00aa00' 
                     for i in range(len(df))]
            ax2.bar(range(len(df)), df['volume'], color=colors, alpha=0.6)
            ax2.set_ylabel('成交量', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # MACD
            ax3 = axes[2]
            if 'MACD' in df.columns:
                ax3.plot(range(len(df)), df['MACD'], color='blue', label='MACD')
                ax3.plot(range(len(df)), df['MACD_signal'], color='red', label='Signal')
                ax3.bar(range(len(df)), df['MACD_hist'], color='gray', alpha=0.6, label='Histogram')
                ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
                ax3.set_ylabel('MACD', fontsize=12)
                ax3.legend()
                ax3.grid(True, alpha=0.3)
            
            # RSI
            ax4 = axes[3]
            if 'RSI' in df.columns:
                ax4.plot(range(len(df)), df['RSI'], color='purple', label='RSI')
                ax4.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='超买线')
                ax4.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='超卖线')
                ax4.set_ylabel('RSI', fontsize=12)
                ax4.set_ylim(0, 100)
                ax4.legend()
                ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 转换为base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            buf.close()
            plt.close()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"生成技术分析图时出错: {e}", exc_info=True)
            raise ValueError(f"生成技术分析图失败: {str(e)}")

# 全局实例
chart_generator = ChartGenerator()

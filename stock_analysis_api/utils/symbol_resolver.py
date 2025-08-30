# 股票代码/名称解析器
import re
from typing import Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class SymbolResolver:
    """股票代码/名称解析器"""
    
    def __init__(self):
        # 常见股票名称到代码的映射
        self.name_to_code = {
            # A股主要股票
            "中国平安": "601318",
            "贵州茅台": "600519",
            "招商银行": "600036",
            "五粮液": "000858",
            "美的集团": "000333",
            "中国银行": "601988",
            "工商银行": "601398",
            "建设银行": "601939",
            "农业银行": "601288",
            "中国石油": "601857",
            "中国石化": "600028",
            "中国移动": "600941",
            "中国联通": "600050",
            "中国电信": "601728",
            "腾讯控股": "00700",  # 港股
            "阿里巴巴": "09988",  # 港股
            "比亚迪": "002594",
            "宁德时代": "300750",
            "立讯精密": "002475",
            "海康威视": "002415",
            "恒瑞医药": "600276",
            "药明康德": "603259",
            "迈瑞医疗": "300760",
            "爱尔眼科": "300015",
            "东方财富": "300059",
            "同花顺": "300033",
            "格力电器": "000651",
            "海尔智家": "600690",
            "万科A": "000002",
            "保利发展": "600048",
            "中国建筑": "601668",
            "中国中车": "601766",
            "三一重工": "600031",
            "中联重科": "000157",
            "紫金矿业": "601899",
            "山东黄金": "600547",
            "中金公司": "601995",
            "华泰证券": "601688",
            "中信证券": "600030",
            "国泰君安": "601211",
            "平安银行": "000001",
            "兴业银行": "601166",
            "浦发银行": "600000",
            "民生银行": "600016",
            "光大银行": "601818",
            "华夏银行": "600015",
            "中信银行": "601998",
            "交通银行": "601328"
        }
        
        # 代码到名称的反向映射
        self.code_to_name = {v: k for k, v in self.name_to_code.items()}
    
    def parse_input(self, input_str: str) -> Tuple[Optional[str], Optional[float]]:
        """
        解析输入字符串，提取股票代码/名称和价格
        
        Args:
            input_str: 输入字符串，如 "中国平安 59.88" 或 "601318 59.88"
            
        Returns:
            (symbol, price) 元组
        """
        try:
            # 清理输入
            input_str = input_str.strip()
            
            # 尝试匹配 "股票名称/代码 价格" 格式
            patterns = [
                r'^(.+?)\s+(\d+\.?\d*)$',  # 名称/代码 + 空格 + 价格
                r'^(.+?)\s*[,，]\s*(\d+\.?\d*)$',  # 名称/代码 + 逗号 + 价格
                r'^(.+?)\s*[:：]\s*(\d+\.?\d*)$',  # 名称/代码 + 冒号 + 价格
            ]
            
            for pattern in patterns:
                match = re.match(pattern, input_str)
                if match:
                    symbol_part = match.group(1).strip()
                    price_part = float(match.group(2))
                    
                    # 解析股票代码/名称
                    resolved_symbol = self.resolve_symbol(symbol_part)
                    if resolved_symbol:
                        return resolved_symbol, price_part
            
            # 如果没有匹配到价格，尝试只解析股票代码/名称
            resolved_symbol = self.resolve_symbol(input_str)
            if resolved_symbol:
                return resolved_symbol, None
                
            return None, None
            
        except Exception as e:
            logger.error(f"解析输入失败: {input_str}, 错误: {e}")
            return None, None
    
    def resolve_symbol(self, symbol_input: str) -> Optional[str]:
        """
        解析股票代码或名称
        
        Args:
            symbol_input: 股票代码或名称
            
        Returns:
            标准化的股票代码
        """
        symbol_input = symbol_input.strip()
        
        # 1. 如果是纯数字代码，直接返回
        if re.match(r'^\d{6}$', symbol_input):  # 6位数字代码
            return symbol_input
        
        # 2. 如果是港股代码格式 (5位数字)
        if re.match(r'^\d{5}$', symbol_input):
            return symbol_input
        
        # 3. 如果是带前缀的代码 (如 SH600036, SZ000001)
        prefix_match = re.match(r'^(SH|SZ|HK)(\d+)$', symbol_input.upper())
        if prefix_match:
            return prefix_match.group(2)
        
        # 4. 查找名称映射
        if symbol_input in self.name_to_code:
            return self.name_to_code[symbol_input]
        
        # 5. 模糊匹配股票名称
        for name, code in self.name_to_code.items():
            if symbol_input in name or name in symbol_input:
                return code
        
        # 6. 如果都没匹配到，返回原始输入（可能是不在映射表中的代码）
        return symbol_input if symbol_input else None
    
    def get_stock_name(self, symbol: str) -> Optional[str]:
        """
        根据股票代码获取股票名称
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票名称
        """
        return self.code_to_name.get(symbol)
    
    def add_stock_mapping(self, name: str, code: str):
        """
        添加新的股票名称代码映射
        
        Args:
            name: 股票名称
            code: 股票代码
        """
        self.name_to_code[name] = code
        self.code_to_name[code] = name
    
    def validate_input_format(self, input_str: str) -> Dict[str, any]:
        """
        验证输入格式并提供建议
        
        Args:
            input_str: 输入字符串
            
        Returns:
            验证结果和建议
        """
        result = {
            "valid": False,
            "symbol": None,
            "price": None,
            "suggestions": []
        }
        
        symbol, price = self.parse_input(input_str)
        
        if symbol and price:
            result["valid"] = True
            result["symbol"] = symbol
            result["price"] = price
            result["stock_name"] = self.get_stock_name(symbol)
        else:
            # 提供格式建议
            result["suggestions"] = [
                "请使用格式: 股票名称 价格 (如: 中国平安 59.88)",
                "请使用格式: 股票代码 价格 (如: 601318 59.88)",
                "支持的分隔符: 空格、逗号、冒号",
                "示例: 中国平安 59.88, 601318,59.88, 贵州茅台:2680.00"
            ]
        
        return result

# 全局解析器实例
symbol_resolver = SymbolResolver()

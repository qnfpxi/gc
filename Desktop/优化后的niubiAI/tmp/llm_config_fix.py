"""LLMConfig类修复版本，添加get_backup_api_key方法。"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    """LLM模型配置。"""

    model_name: str
    api_url: str
    backup_urls: Optional[List[str]] = Field(default_factory=list)
    api_key_service: str  # 服务器名称，用于从安全管理器获取密钥
    backup_api_keys: Optional[List[str]] = Field(default_factory=list)
    enabled: bool = True
    priority: int = 1
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 30

    def get_api_key(self) -> Optional[str]:
        """获取API密钥。"""
        # 从环境变量获取API密钥
        import os
        # 如果api_key_service就是环境变量名，直接使用
        if self.api_key_service.endswith('_API_KEY'):
            return os.getenv(self.api_key_service)
        # 否则按照旧格式查找
        return os.getenv(f"{self.api_key_service.upper()}_API_KEY") or os.getenv("PRIMARY_API_KEY")

    def get_backup_url(self, index: int) -> Optional[str]:
        """获取备用URL。"""
        if not self.backup_urls or index >= len(self.backup_urls):
            return None
        return self.backup_urls[index]
    
    def get_backup_api_key(self, index: int) -> Optional[str]:
        """获取备用API密钥。
        
        Args:
            index: 备用API密钥索引
            
        Returns:
            备用API密钥，如果不存在则返回None
        """
        if not self.backup_api_keys or index >= len(self.backup_api_keys):
            return None
        
        import os
        backup_key = self.backup_api_keys[index]
        
        # 如果备用密钥是环境变量名，从环境变量获取
        if backup_key.endswith('_API_KEY'):
            return os.getenv(backup_key)
        
        # 否则按照旧格式查找
        return os.getenv(f"{backup_key.upper()}_API_KEY") or backup_key

    @field_validator("api_key_service")
    @classmethod
    def validate_api_key_service(cls, v):
        """验证API密钥服务名称。."""
        if not v:
            raise ValueError("API key service name is required")
        return v
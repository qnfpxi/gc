import asyncio
import hashlib
import io
import logging
import logging.handlers # For RotatingFileHandler
import os
import sys
import zlib # For compression
import msgpack # For efficient serialization
import time # For sleep in retries
from abc import ABC, abstractmethod # For data source abstraction and analysis modules
from datetime import datetime, timedelta
from functools import wraps, lru_cache # For decorator and in-memory caching
from typing import Any, Dict, List, Optional, Tuple, Union, Type

import akshare as ak
import ccxt
import numpy as np
import pandas as pd
import redis
import requests
import tushare as ts
import urllib3
import yfinance as yf
from fastapi import FastAPI, Header, HTTPException, Query, status, Response
from pydantic import BaseModel, Field, ValidationError # For API response models
from dynaconf import Dynaconf, settings as dynaconf_settings # For configuration management
from jinja2 import Environment, FileSystemLoader, select_autoescape # For template rendering
from pathlib import Path # For template directory

# Tenacity for robust retries
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_result,
    before_sleep_log,
    wait_fixed # For specific fixed waits
)
import aiohttp # For async HTTP requests

# Prometheus client for metrics
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest
except ImportError:
    # Define dummy classes if prometheus_client is not installed
    Counter = lambda *args, **kwargs: type('DummyCounter', (object,), {'inc': lambda *a, **kw: None})()
    Histogram = lambda *args, **kwargs: type('DummyHistogram', (object,), {'time': lambda *a, **kw: lambda f: f})()
    Gauge = lambda *args, **kwargs: type('DummyGauge', (object,), {'set': lambda *a, **kw: None, 'inc': lambda *a, **kw: None, 'dec': lambda *a, **kw: None})()
    generate_latest = lambda: b''
    logging.warning("prometheus_client is not installed, monitoring will be disabled. Please run 'pip install prometheus_client'.")

# Update version identifier
_VERSION_IDENTIFIER_ = "STOCK_ANALYSIS_API_V7.5.0_OPTIMIZED"
print(f"--- Diagnostic: Loading stock_analysis_api.py version: {_VERSION_IDENTIFIER_} ---")

# --- 1. Configuration Management (Dynaconf) ---
# Dynaconf will load settings from config.yaml, .env, and environment variables
settings = Dynaconf(
    envvar_prefix="STOCK_API",
    settings_files=['config.yaml', '.env'],
    environments=True,  # Enable environment-specific settings
    load_dotenv=True,   # Load .env file
    # Default values for common settings if not found in files/env
    defaults={
        "TUSHARE_TOKEN": "",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": 6379,
        "REDIS_PASSWORD": None,
        "VALID_AUTH_TOKENS": None,
        "LOG_LEVEL": "INFO",
        "LOG_FILE": "stock_api.log",
        "LOG_FILE_MAX_BYTES": 10 * 1024 * 1024, # 10 MB
        "LOG_FILE_BACKUP_COUNT": 5,
        "PREHEAT_TOP_N_STOCKS": 0, # Number of top stocks to preheat, 0 to disable
        # Default app_params structure (can be overridden by config.yaml)
        "APP_PARAMS": {
            "version": "1.0.0",
            "A": {
                "ma_periods": {'short': 5, 'medium': 20},
                "macd_params": {'fast': 12, 'slow': 26, 'signal': 9},
                "momentum_period": 20,
                "volatility_period": 20,
                "rsi_period": 14,
                "bollinger_period": 20,
                "bollinger_std": 2,
                "volume_ma_periods": {'short': 5, 'medium': 20},
                "atr_period": 14,
                "k_pattern_window": 20,
                "stoch_k_period": 14,
                "stoch_d_period": 3,
                "cache_ttl": 3600 * 12, # Historical K-line cache 12 hours
                "result_cache_ttl": 14400, # Analysis result cache 4 hours
                "data_days": 60, # Default historical data days
                "batch_size": 10, # Fixed batch size for Tushare/Akshare API calls
                "batch_pause_time": 0.5, # Pause time between batches (seconds)
                "max_stocks_for_preheat": 5000, # Max stocks to preheat for global data
                "name_map_cache_ttl": 3600 * 24, # Stock name map cache 1 day
                "fina_indicator_cache_ttl": 3600 * 24 * 180, # Financial indicator cache 180 days (approx 6 months)
                "moneyflow_dc_cache_ttl": 3600 * 24, # Individual stock money flow (DC) cache 1 day
                "moneyflow_ind_ths_cache_ttl": 3600 * 6, # Industry money flow (THS) cache 6 hours
                "stk_factor_pro_cache_ttl": 3600 * 48, # Stock technical factor cache 2 days
                "limit_list_d_cache_ttl": 3600 * 48, # Daily limit-up/down statistics cache 2 days
                "stk_limit_cache_ttl": 3600 * 48, # Daily limit-up/down price cache 2 days
                "ak_spot_on_demand_ttl": 60, # Akshare real-time spot data on-demand, short cache 1 minute
                "top_inst_cache_ttl": 3600 * 24, # Dragon-Tiger list institutional trade details cache 1 day
                "hm_list_cache_ttl": 3600 * 24 * 30, # Hot money list cache 30 days
                "ths_member_cache_ttl": 604800, # THS concept members cache 7 days
                "ths_hot_cache_ttl": 3600 * 24, # THS hot list cache 1 day
                "cyq_chips_cache_ttl": 3600 * 24 # Daily chip distribution cache 1 day
            },
            "HK": {"data_days": 180, "cache_ttl": 3600 * 4},
            "US": {"data_days": 180, "cache_ttl": 3600 * 4},
            "JP": {"data_days": 180, "cache_ttl": 3600 * 4},
            "IN": {"data_days": 180, "cache_ttl": 3600 * 4},
            "CRYPTO": {"ma_periods": {'short': 3, 'medium': 10}, "data_days": 180, "cache_ttl": 3600 * 1},
            "ETF": {"data_days": 180, "cache_ttl": 3600 * 4},
            "LOF": {"data_days": 180, "cache_ttl": 3600 * 4}
        },
        "SUMMARY_RULES": [ # Default summary rules if not in config.yaml
            {"condition": "limit_status == 'LIMIT_UP'", "summary_phrase": "该股票今日涨停，市场情绪高涨，短期趋势良好。", "priority": 1},
            {"condition": "limit_status == 'LIMIT_DOWN'", "summary_phrase": "该股票今日跌停，存在较大下行风险，建议规避。", "priority": 1},
            {"condition": "latest_price is not None and MA_medium is not None and latest_price > MA_medium * 1.05 and MACD_Hist is not None and MACD_Hist > 0.1", "summary_phrase": "股价站稳中长期均线，MACD柱线为正，显示看涨倾向，可关注。", "priority": 2},
            {"condition": "latest_price is not None and MA_medium is not None and latest_price < MA_medium * 0.95 and MACD_Hist is not None and MACD_Hist < -0.1", "summary_phrase": "股价跌破中长期均线，MACD柱线为负，短期承压，需警惕风险。", "priority": 2},
            {"condition": "main_net_amount_dc is not None and main_net_amount_dc > 5000", "summary_phrase": "主力资金大额流入，表明有机构看好，值得留意。", "priority": 3},
            {"condition": "main_net_amount_dc is not None and main_net_amount_dc < -5000", "summary_phrase": "主力资金大额流出，短期抛压较大，谨慎观望。", "priority": 3},
            {"condition": "revenue_yoy is not None and revenue_yoy > 20 and np_yoy is not None and np_yoy > 20", "summary_phrase": "公司营收和净利润均实现高速增长，基本面强劲，具备长期投资价值。", "priority": 4},
            {"condition": "PB_ratio is not None and PB_ratio < 1.2", "summary_phrase": "PB估值较低，可能存在被低估的情况，可适当关注。", "priority": 5},
            {"condition": "True", "summary_phrase": "当前市场情况复杂，建议中性观望，等待更明确信号。", "priority": 999}
        ],
        "ANALYSIS_MODULES": { # Default analysis module configuration
            "TechnicalAnalyzer": {"enabled": True, "priority": 1, "dependencies": []},
            "FundamentalAnalyzer": {"enabled": True, "priority": 2, "dependencies": ["TechnicalAnalyzer"]},
            "MarketSentimentAnalyzer": {"enabled": True, "priority": 3, "dependencies": []},
            "IndustryConceptAnalyzer": {"enabled": True, "priority": 4, "dependencies": []},
            "CostAnalyzer": {"enabled": True, "priority": 5, "dependencies": ["TechnicalAnalyzer", "MarketSentimentAnalyzer"]}
        },
        "TEMPLATE_SETTINGS": {
            "template_dir": "templates",
            "default_template": "analysis_report_template.html",
            "languages": {
                "zh": "zh",
                "en": "en"
            }
        }
    }
)

# Access app_params via settings.APP_PARAMS
app_params = settings.get('APP_PARAMS') # <--- Changed this line
template_settings = settings.get('TEMPLATE_SETTINGS') # <--- Changed this line

# --- 2. Logging Configuration ---
def setup_logging():
    """Configures logging for the application."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Clear existing handlers to prevent duplicate logs if called multiple times
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.handlers.RotatingFileHandler(
                settings.LOG_FILE,
                maxBytes=settings.LOG_FILE_MAX_BYTES,
                backupCount=settings.LOG_FILE_BACKUP_COUNT
            ),
            logging.StreamHandler()
        ]
    )
    # Set log level for specific libraries if needed (e.g., to suppress verbose output)
    logging.getLogger('uvicorn').setLevel(log_level)
    logging.getLogger('uvicorn.access').setLevel(log_level)
    logging.getLogger('aiohttp').setLevel(logging.WARNING) # Suppress verbose aiohttp logs
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('tenacity').setLevel(logging.DEBUG) # Keep tenacity logs for debugging retries

setup_logging() # Call setup_logging at startup
logger = logging.getLogger(__name__)

# --- 3. Custom Exceptions and Retry Decorators ---
class APIError(HTTPException):
    """Custom exception for API-specific errors with error codes."""
    def __init__(self, status_code: int, detail: str, error_code: str = "UNKNOWN_ERROR"):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        logger.error(f"APIError [{error_code}]: {detail}")

# Common exceptions for retries
_common_retry_exceptions_tuple = (
    ConnectionError,
    requests.exceptions.RequestException,
    requests.exceptions.Timeout,
    requests.exceptions.HTTPError,
    requests.exceptions.ConnectionError,
    requests.exceptions.ChunkedEncodingError,
    urllib3.exceptions.ProtocolError,
    asyncio.TimeoutError,
    redis.exceptions.ConnectionError,
    aiohttp.ClientError # Add aiohttp client errors for direct HTTP calls
)

_akshare_exception_class = None
try:
    from akshare.exceptions import AkShareException as _AkShareExceptionClass
    _akshare_exception_class = _AkShareExceptionClass
except ImportError:
    logger.warning("Failed to import AkShareException from akshare.exceptions, will not be included in retry exceptions. This may prevent automatic retries for some Akshare-specific errors.")
_akshare_retry_exceptions = list(_common_retry_exceptions_tuple)
if _akshare_exception_class:
    _akshare_retry_exceptions.append(_AkShareExceptionClass)
AKSHARE_RETRY_EXCEPTIONS = tuple(_akshare_retry_exceptions)

TUSHARE_RETRY_EXCEPTIONS = _common_retry_exceptions_tuple + (ValueError, Exception,) # ValueError for Tushare specific data errors

# Retry decorators with exponential backoff and logging
# Increased initial wait for Tushare to be more conservative with rate limits
akshare_retry_decorator = retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=2, max=10), # Exponential backoff: 2s, 4s, 8s
    retry=retry_if_exception_type(AKSHARE_RETRY_EXCEPTIONS), 
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.INFO, exc_info=True)
)
tushare_retry_decorator = retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=3, max=15), # Exponential backoff: 3s, 6s, 12s
    retry=retry_if_exception_type(TUSHARE_RETRY_EXCEPTIONS), 
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.INFO, exc_info=True)
)
yf_retry_decorator = retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=1, max=5), 
    retry=retry_if_exception_type(_common_retry_exceptions_tuple), 
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.INFO, exc_info=True)
)
ccxt_retry_decorator = retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=1, max=5), 
    retry=retry_if_exception_type(_common_retry_exceptions_tuple), 
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.INFO, exc_info=True)
)

# Centralized Error Handling Decorator (Enhanced Error Logging)
def handle_api_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        data_source_name = kwargs.get('data_source_name', 'UNKNOWN') # For Prometheus
        method_name = func.__name__ # For Prometheus
        
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            data_source_response_time.labels(data_source=data_source_name, method=method_name).observe(time.time() - start_time)
            data_source_call_frequency.labels(data_source=data_source_name, method=method_name, status='success').inc()
            return result
        except APIError: # Re-raise custom APIError directly
            data_source_call_frequency.labels(data_source=data_source_name, method=method_name, status='failed').inc()
            raise
        except _akshare_exception_class as e:
            logger.error(f"Akshare error in {method_name} (symbol: {kwargs.get('symbol', 'N/A')}, symbols: {kwargs.get('symbols', 'N/A')}): {e}", exc_info=True)
            api_errors_counter.labels(error_code="AKSHARE_ERROR", data_source=data_source_name).inc()
            data_source_call_frequency.labels(data_source=data_source_name, method=method_name, status='failed').inc()
            raise APIError(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Akshare Error: {e}", "AKSHARE_ERROR")
        except (requests.exceptions.RequestException, aiohttp.ClientError) as e:
            logger.error(f"Network error in {method_name} (symbol: {kwargs.get('symbol', 'N/A')}, symbols: {kwargs.get('symbols', 'N/A')}): {e}", exc_info=True)
            api_errors_counter.labels(error_code="NETWORK_ERROR", data_source=data_source_name).inc()
            data_source_call_frequency.labels(data_source=data_source_name, method=method_name, status='failed').inc()
            raise APIError(status.HTTP_503_SERVICE_UNAVAILABLE, f"Network Error: {e}", "NETWORK_ERROR")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis connection error in {method_name} (symbol: {kwargs.get('symbol', 'N/A')}, symbols: {kwargs.get('symbols', 'N/A')}): {e}", exc_info=True)
            api_errors_counter.labels(error_code="REDIS_CONNECTION_ERROR", data_source=data_source_name).inc()
            data_source_call_frequency.labels(data_source=data_source_name, method=method_name, status='failed').inc()
            raise APIError(status.HTTP_503_SERVICE_UNAVAILABLE, f"Redis Connection Error: {e}", "REDIS_CONNECTION_ERROR")
        except Exception as e: # Catch all other unexpected errors
            logger.critical(f"An unexpected error occurred in {method_name} (symbol: {kwargs.get('symbol', 'N/A')}, symbols: {kwargs.get('symbols', 'N/A')}): {e}", exc_info=True)
            api_errors_counter.labels(error_code="UNEXPECTED_ERROR", data_source=data_source_name).inc()
            data_source_call_frequency.labels(data_source=data_source_name, method=method_name, status='failed').inc()
            raise APIError(status.HTTP_500_INTERNAL_SERVER_ERROR, f"An unexpected error occurred: {e}", "UNEXPECTED_ERROR")
    return wrapper

# --- 4. Prometheus Metrics ---
api_request_counter = Counter('stock_api_requests_total', 'Total API requests')
api_response_time_histogram = Histogram('stock_api_response_time_seconds', 'API response time in seconds')
api_errors_counter = Counter('stock_api_errors_total', 'Total API errors', ['error_code', 'data_source'])
data_source_response_time = Histogram('stock_api_data_source_response_time_seconds', 'Data source response time in seconds', ['data_source', 'method'])
data_source_call_frequency = Counter('stock_api_data_source_calls_total', 'Total data source calls', ['data_source', 'method', 'status'])
cache_hit_ratio_gauge = Gauge('stock_api_cache_hit_ratio', 'Cache hit ratio for data sources', ['data_source'])
data_completeness_counter = Counter('stock_api_data_completeness_errors_total', 'Data completeness errors', ['module', 'field'])
tushare_quota_gauge = Gauge('stock_api_tushare_daily_quota_remaining', 'Tushare daily quota remaining')

# --- 5. Redis Client Initialization ---
redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
    db=0,
    socket_connect_timeout=5, # Connection timeout
    socket_timeout=5 # Read/write timeout
)

# --- 6. Data Serialization and Deserialization ---
def serialize_dataframe(df: pd.DataFrame) -> bytes:
    """Serializes a pandas DataFrame to msgpack format and then compresses it."""
    if df is None or df.empty:
        return zlib.compress(msgpack.packb({}, use_bin_type=True)) # Return compressed empty dict
    packed_data = msgpack.packb(df.to_dict(orient='records'), use_bin_type=True)
    return zlib.compress(packed_data)

def deserialize_dataframe(data: bytes) -> pd.DataFrame:
    """De-serializes and decompresses data back into a pandas DataFrame."""
    if not data:
        return pd.DataFrame() # Return empty DataFrame if no data
    decompressed_data = zlib.decompress(data)
    unpacked_data = msgpack.unpackb(decompressed_data, raw=False)
    if not unpacked_data:
        return pd.DataFrame()
    return pd.DataFrame(unpacked_data)

# --- 7. Incremental Cache Operations (Redis Hash) ---
async def cache_dataframe_incremental(redis_client: redis.Redis, key_prefix: str, df: pd.DataFrame, ttl: int):
    """
    Caches a DataFrame incrementally into a Redis Hash.
    Each row becomes a field in the Hash, keyed by its 'date' or 'trade_date'.
    Also sets a TTL for the main key.
    """
    if df is None or df.empty:
        logger.debug(f"Skipping incremental cache for empty DataFrame: {key_prefix}")
        return

    # Determine the date column name
    date_col = 'trade_date' if 'trade_date' in df.columns else 'date'
    if date_col not in df.columns:
        logger.warning(f"DataFrame for {key_prefix} has no 'date' or 'trade_date' column. Cannot perform incremental caching.")
        return

    try:
        # Use a Redis pipeline for efficiency
        pipe = redis_client.pipeline()
        
        # Iterate over DataFrame rows and set each as a hash field
        for index, row in df.iterrows():
            # Convert row to dictionary, ensure it's JSON serializable
            row_dict = row.to_dict()
            # Convert any non-serializable types (e.g., Timestamp, NaT)
            for k, v in row_dict.items():
                if pd.isna(v):
                    row_dict[k] = None # Convert NaN to None
                elif isinstance(v, (datetime, pd.Timestamp)):
                    row_dict[k] = v.strftime('%Y%m%d %H:%M:%S') # Convert datetime to string
                elif isinstance(v, np.generic): # Handle numpy types
                    row_dict[k] = v.item()

            # Key for the hash field will be the date
            field_key = str(row_dict[date_col])
            pipe.hset(key_prefix, field_key, msgpack.packb(row_dict, use_bin_type=True))
        
        # Set TTL for the entire hash key
        pipe.expire(key_prefix, ttl)
        
        # Execute pipeline in a thread, as redis-py operations are blocking
        await asyncio.to_thread(pipe.execute) 
        logger.debug(f"Incrementally cached {len(df)} records for {key_prefix} with TTL {ttl}.")
    except Exception as e:
        logger.error(f"Failed to incrementally cache {key_prefix}: {e}", exc_info=True)

async def load_cached_dataframe_incremental(redis_client: redis.Redis, key_prefix: str) -> Optional[pd.DataFrame]:
    """
    Loads a DataFrame from a Redis Hash, assuming it was stored incrementally.
    """
    try:
        # Fetch all fields from the hash
        raw_records = await asyncio.to_thread(redis_client.hgetall, key_prefix)
        
        records = []
        if raw_records:
            for field_key, packed_value in raw_records.items():
                try:
                    record = msgpack.unpackb(packed_value, raw=False)
                    # Attempt to convert date strings back to datetime objects
                    if 'trade_date' in record and isinstance(record['trade_date'], str):
                        try:
                            record['trade_date'] = datetime.strptime(record['trade_date'].split(' ')[0], '%Y%m%d')
                        except ValueError:
                            pass # Keep as string if parsing fails
                    elif 'date' in record and isinstance(record['date'], str):
                        try:
                            record['date'] = datetime.strptime(record['date'].split(' ')[0], '%Y%m%d')
                        except ValueError:
                            pass # Keep as string if parsing fails
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Failed to unpack record from {key_prefix} (field: {field_key}): {e}")
            
            # Sort records by date if possible
            if records and any('trade_date' in r and isinstance(r['trade_date'], datetime) for r in records):
                records.sort(key=lambda x: x.get('trade_date', datetime.min))
            elif records and any('date' in r and isinstance(r['date'], datetime) for r in records):
                records.sort(key=lambda x: x.get('date', datetime.min))

        if records:
            df = pd.DataFrame(records)
            # Ensure date columns are datetime objects after loading
            if 'trade_date' in df.columns:
                df['trade_date'] = pd.to_datetime(df['trade_date'], errors='coerce')
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            logger.debug(f"Loaded {len(df)} records from incremental cache for {key_prefix}.")
            cache_hit_ratio_gauge.labels(data_source=key_prefix.split(':')[0]).inc() # Increment cache hit
            return df
        else:
            logger.debug(f"No records found in incremental cache for {key_prefix}.")
            return None # No data found
    except Exception as e:
        logger.error(f"Failed to load incremental cache for {key_prefix}: {e}", exc_info=True)
        return None

# --- 8. Data Source Abstraction ---
class DataSource(ABC):
    """Abstract base class for all data sources."""
    def __init__(self, data_source_name: str):
        self.data_source_name = data_source_name

    @abstractmethod
    async def fetch_daily(self, symbol: str, start_date: str, end_date: str, is_fund: bool = False) -> pd.DataFrame:
        """Fetches daily historical data for a given symbol."""
        pass

    @abstractmethod
    async def fetch_fundamentals(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Fetches fundamental data for given symbols."""
        pass

    @abstractmethod
    async def fetch_moneyflow(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Fetches money flow data for given symbols."""
        pass

    @abstractmethod
    async def fetch_spot_data(self, symbols: Union[str, List[str]]) -> pd.DataFrame:
        """Fetches real-time spot data for given symbols (or 'global')."""
        pass

class TushareDataSource(DataSource):
    _instance = None
    _initialized = False
    session: Optional[aiohttp.ClientSession] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not TushareDataSource._initialized:
            super().__init__("Tushare")
            self.pro = ts.pro_api(settings.TUSHARE_TOKEN)
            TushareDataSource._initialized = True
            logger.info("TushareDataSource initialized.")

    @classmethod
    async def get_session(cls) -> aiohttp.ClientSession:
        if cls.session is None or cls.session.closed:
            cls.session = aiohttp.ClientSession()
            logger.info("Created new aiohttp client session for TushareDataSource.")
        return cls.session

    @tushare_retry_decorator
    @handle_api_errors
    async def _call_tushare_api(self, api_name: str, **kwargs) -> pd.DataFrame:
        """Helper to call Tushare API asynchronously using aiohttp."""
        # Tushare's pro_api is synchronous, so we run it in a thread
        # We also need to get the quota info before making the call
        
        # Get current quota info
        try:
            quota_info = await asyncio.to_thread(self.pro.query, 'api_quota')
            if not quota_info.empty:
                daily_quota_remaining = quota_info[quota_info['api_name'] == api_name]['remain_cnt'].iloc[0]
                tushare_quota_gauge.set(daily_quota_remaining)
                logger.debug(f"Tushare API '{api_name}' daily quota remaining: {daily_quota_remaining}")
                if daily_quota_remaining <= 10: # Threshold for warning
                    logger.warning(f"Tushare API '{api_name}' quota is running low: {daily_quota_remaining} remaining.")
                if daily_quota_remaining <= 0:
                    raise APIError(status.HTTP_429_TOO_MANY_REQUESTS, f"Tushare API '{api_name}' quota exhausted.", "TUSHARE_QUOTA_EXHAUSTED")
        except Exception as e:
            logger.warning(f"Failed to get Tushare API quota for '{api_name}': {e}")
            # Continue without quota check if check fails, but log it

        logger.debug(f"Calling Tushare API: {api_name} with kwargs: {kwargs}")
        df = await asyncio.to_thread(self.pro.query, api_name, **kwargs)
        if df.empty:
            logger.warning(f"Tushare API '{api_name}' returned empty DataFrame for kwargs: {kwargs}")
        return df

    @tushare_retry_decorator
    @handle_api_errors
    async def fetch_daily(self, symbol: str, start_date: str, end_date: str, is_fund: bool = False) -> pd.DataFrame:
        """Fetches daily historical data from Tushare."""
        logger.info(f"Fetching daily data for {symbol} from Tushare (start={start_date}, end={end_date}, is_fund={is_fund})...")
        if is_fund:
            df = await self._call_tushare_api('fund_daily', ts_code=symbol, start_date=start_date, end_date=end_date)
        else:
            # For A-shares, this is fine. For HK/US, we'll rely on DataSourceManager to route to YFinance.
            df = await self._call_tushare_api('daily', ts_code=symbol, start_date=start_date, end_date=end_date)
        return standardize_hist_data(df, "Tushare", symbol)

    @tushare_retry_decorator
    @handle_api_errors
    async def fetch_fundamentals(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """
        Fetches fundamental data (fina_indicator_vip) from Tushare for multiple symbols.
        Prioritizes fina_indicator_vip for full market data, falls back to individual calls if needed.
        """
        logger.info(f"Fetching fundamental data for {symbols} from Tushare (start={start_date}, end={end_date})...")
        all_fina_data = {}
        
        # Attempt to use fina_indicator_vip for full market data if available and enabled
        try:
            latest_quarter_end_date = pd.to_datetime(end_date).to_period('Q').end_time.strftime('%Y%m%d')
            
            logger.info(f"Attempting to fetch all market fundamental data via fina_indicator_vip for {latest_quarter_end_date}...")
            full_market_fina_df = await self._call_tushare_api('fina_indicator_vip', end_date=latest_quarter_end_date)
            
            if not full_market_fina_df.empty:
                logger.info(f"Successfully fetched {len(full_market_fina_df)} records via fina_indicator_vip.")
                for symbol in symbols:
                    symbol_data = full_market_fina_df[full_market_fina_df['ts_code'] == symbol]
                    if not symbol_data.empty:
                        all_fina_data[symbol] = standardize_fina_data(symbol_data, "Tushare", symbol)
                    else:
                        logger.warning(f"No fina_indicator_vip data found for {symbol} on {latest_quarter_end_date}.")
            else:
                logger.warning("fina_indicator_vip returned empty data. Falling back to individual calls.")
                # Fallback to individual calls if VIP data is empty
                for symbol in symbols:
                    df = await self._call_tushare_api('fina_indicator', ts_code=symbol, start_date=start_date, end_date=end_date)
                    all_fina_data[symbol] = standardize_fina_data(df, "Tushare", symbol)

        except Exception as e:
            logger.warning(f"Failed to fetch fundamental data via fina_indicator_vip: {e}. Falling back to individual calls.", exc_info=True)
            # Fallback to individual calls if VIP call fails
            for symbol in symbols:
                df = await self._call_tushare_api('fina_indicator', ts_code=symbol, start_date=start_date, end_date=end_date)
                all_fina_data[symbol] = standardize_fina_data(df, "Tushare", symbol)
        
        return all_fina_data

    @tushare_retry_decorator
    @handle_api_errors
    async def fetch_moneyflow(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Fetches money flow data (moneyflow_dc) from Tushare for multiple symbols."""
        logger.info(f"Fetching money flow data for {symbols} from Tushare (start={start_date}, end={end_date})...")
        all_moneyflow_data = {}
        batch_size = app_params.A.batch_size
        batch_pause_time = app_params.A.batch_pause_time

        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i + batch_size]
            tasks = []
            for symbol in batch_symbols:
                tasks.append(self._call_tushare_api('moneyflow_dc', ts_code=symbol, start_date=start_date, end_date=end_date))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for symbol, result in zip(batch_symbols, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to fetch moneyflow_dc for {symbol}: {result}")
                    all_moneyflow_data[symbol] = pd.DataFrame() # Return empty DataFrame on error
                else:
                    all_moneyflow_data[symbol] = standardize_moneyflow_data(result, "Tushare", symbol)
            
            if i + batch_size < len(symbols):
                await asyncio.sleep(batch_pause_time) # Pause between batches

        return all_moneyflow_data

    @handle_api_errors
    async def fetch_spot_data(self, symbols: Union[str, List[str]]) -> pd.DataFrame:
        """Tushare does not provide real-time spot data directly. This method is a placeholder."""
        logger.warning("TushareDataSource does not support real-time spot data. Returning empty DataFrame.")
        return pd.DataFrame() # Tushare doesn't have a direct equivalent for real-time spot data

class AkshareDataSource(DataSource):
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not AkshareDataSource._initialized:
            super().__init__("Akshare")
            AkshareDataSource._initialized = True
            logger.info("AkshareDataSource initialized.")

    @akshare_retry_decorator
    @handle_api_errors
    async def fetch_daily(self, symbol: str, start_date: str, end_date: str, is_fund: bool = False) -> pd.DataFrame:
        """Fetches daily historical data from Akshare."""
        logger.info(f"Fetching daily data for {symbol} from Akshare (start={start_date}, end={end_date}, is_fund={is_fund})...")
        try:
            if is_fund:
                # Akshare fund data might have different interfaces, using stock_zh_a_hist as a general fallback
                # You might need to find a specific Akshare fund interface if available
                df = await asyncio.to_thread(ak.stock_zh_a_hist, symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
            else:
                df = await asyncio.to_thread(ak.stock_zh_a_hist, symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
            return standardize_hist_data(df, "Akshare", symbol)
        except Exception as e:
            logger.error(f"Akshare fetch_daily for {symbol} failed: {e}", exc_info=True)
            return pd.DataFrame()

    @akshare_retry_decorator
    @handle_api_errors
    async def fetch_fundamentals(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """
        Fetches fundamental data from Akshare.
        Akshare often provides financial data per company or per report.
        This attempts to get latest financial report for each symbol.
        """
        logger.info(f"Fetching fundamental data for {symbols} from Akshare (start={start_date}, end={end_date})...")
        all_fina_data = {}
        for symbol in symbols:
            try:
                # Akshare financial data often comes from specific reports, e.g., 'stock_financial_report_sina'
                # This is a simplified example; you might need to find the exact Akshare API for comprehensive financial indicators.
                # For now, let's use a proxy like 'stock_financial_analysis_indicator_em' if it fits.
                # Or, if we want a specific company's latest report:
                # df_fina = await asyncio.to_thread(ak.stock_financial_analysis_indicator_em, symbol=symbol)
                # This needs to be adapted based on the exact Akshare API that provides the desired financial metrics.
                # As a fallback, we'll try 'stock_financial_indicator_em' which gives a list of indicators.
                
                df_fina = await asyncio.to_thread(ak.stock_financial_indicator_em, symbol=symbol)
                if not df_fina.empty:
                    # Filter by date range if necessary and standardize
                    df_fina['report_date'] = pd.to_datetime(df_fina['报告日期'])
                    df_fina = df_fina[(df_fina['report_date'] >= pd.to_datetime(start_date)) & 
                                      (df_fina['report_date'] <= pd.to_datetime(end_date))]
                    all_fina_data[symbol] = standardize_fina_data(df_fina, symbol)
                else:
                    logger.warning(f"Akshare fundamental data for {symbol} is empty.")
                    all_fina_data[symbol] = pd.DataFrame()
            except Exception as e:
                logger.error(f"Akshare fetch_fundamentals for {symbol} failed: {e}", exc_info=True)
                all_fina_data[symbol] = pd.DataFrame()
        return all_fina_data

    @akshare_retry_decorator
    @handle_api_errors
    async def fetch_moneyflow(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Fetches money flow data from Akshare."""
        logger.info(f"Fetching money flow data for {symbols} from Akshare (start={start_date}, end={end_date})...")
        all_moneyflow_data = {}
        for symbol in symbols:
            try:
                # Akshare provides 'stock_individual_fund_flow' for money flow
                df = await asyncio.to_thread(ak.stock_individual_fund_flow, stock=symbol, start_date=start_date, end_date=end_date)
                all_moneyflow_data[symbol] = standardize_moneyflow_data(df, "Akshare", symbol)
            except Exception as e:
                logger.error(f"Akshare fetch_moneyflow for {symbol} failed: {e}", exc_info=True)
                all_moneyflow_data[symbol] = pd.DataFrame()
        return all_moneyflow_data

    @akshare_retry_decorator
    @handle_api_errors
    async def fetch_spot_data(self, symbols: Union[str, List[str]]) -> pd.DataFrame:
        """Fetches real-time spot data from Akshare."""
        logger.info(f"Fetching spot data for {symbols} from Akshare...")
        try:
            if symbols == "global": # Fetch all A-share spot data
                df = await asyncio.to_thread(ak.stock_zh_a_spot)
            elif isinstance(symbols, list): # Fetch specific symbols
                # Akshare's stock_zh_a_spot doesn't directly support querying by list of symbols.
                # We fetch all and filter, or make individual calls if performance allows.
                df = await asyncio.to_thread(ak.stock_zh_a_spot)
                df = df[df['代码'].isin(symbols)]
            else: # Assume single symbol
                df = await asyncio.to_thread(ak.stock_zh_a_spot)
                df = df[df['代码'] == symbols]

            return standardize_spot_data(df, "Akshare", symbols)
        except Exception as e:
            logger.error(f"Akshare fetch_spot_data for {symbols} failed: {e}", exc_info=True)
            return pd.DataFrame()

class YFinanceDataSource(DataSource):
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not YFinanceDataSource._initialized:
            super().__init__("YFinance")
            YFinanceDataSource._initialized = True
            logger.info("YFinanceDataSource initialized.")

    @yf_retry_decorator
    @handle_api_errors
    async def fetch_daily(self, symbol: str, start_date: str, end_date: str, is_fund: bool = False) -> pd.DataFrame:
        """Fetches daily historical data from Yahoo Finance."""
        logger.info(f"Fetching daily data for {symbol} from YFinance (start={start_date}, end={end_date}, is_fund={is_fund})...")
        try:
            # yfinance uses datetime objects for start/end dates
            yf_start_date = datetime.strptime(start_date, '%Y%m%d')
            yf_end_date = datetime.strptime(end_date, '%Y%m%d') + timedelta(days=1) # yfinance end date is exclusive

            # For funds/ETFs, yfinance handles them similarly to stocks
            df = await asyncio.to_thread(yf.download, symbol, start=yf_start_date, end=yf_end_date, progress=False)
            
            if df.empty:
                logger.warning(f"YFinance returned empty DataFrame for {symbol}.")
                return pd.DataFrame()
            
            return standardize_hist_data(df, "YFinance", symbol)
        except Exception as e:
            logger.error(f"YFinance fetch_daily for {symbol} failed: {e}", exc_info=True)
            return pd.DataFrame()

    @handle_api_errors
    async def fetch_fundamentals(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Fetches fundamental data from Yahoo Finance."""
        logger.info(f"Fetching fundamental data for {symbols} from YFinance (start={start_date}, end={end_date})...")
        all_fina_data = {}
        for symbol in symbols:
            try:
                ticker = await asyncio.to_thread(yf.Ticker, symbol)
                # yfinance provides various financial statements (income_stmt, balance_sheet, cash_flow)
                # and key statistics. We need to combine these to form a "fundamental" DataFrame.
                
                # For simplicity, let's fetch income statement and balance sheet
                income_stmt = await asyncio.to_thread(getattr, ticker, 'income_stmt')
                balance_sheet = await asyncio.to_thread(getattr, ticker, 'balance_sheet')

                if income_stmt is not None and not income_stmt.empty:
                    # income_stmt is usually transposed, make sure columns are dates
                    income_stmt = income_stmt.T.reset_index().rename(columns={'index': 'report_date'})
                    income_stmt['report_date'] = pd.to_datetime(income_stmt['report_date'])
                    income_stmt = income_stmt.sort_values(by='report_date', ascending=True)
                else:
                    income_stmt = pd.DataFrame()

                if balance_sheet is not None and not balance_sheet.empty:
                    balance_sheet = balance_sheet.T.reset_index().rename(columns={'index': 'report_date'})
                    balance_sheet['report_date'] = pd.to_datetime(balance_sheet['report_date'])
                    balance_sheet = balance_sheet.sort_values(by='report_date', ascending=True)
                else:
                    balance_sheet = pd.DataFrame()

                # Combine relevant data (this requires careful mapping and selection of metrics)
                # For now, we'll just return the income statement as a placeholder for fundamental data
                # You'll need to expand this to include more metrics and combine them appropriately.
                combined_df = income_stmt # Placeholder
                if not combined_df.empty:
                    # Filter by date range
                    combined_df = combined_df[(combined_df['report_date'] >= pd.to_datetime(start_date)) & 
                                              (combined_df['report_date'] <= pd.to_datetime(end_date))]
                    all_fina_data[symbol] = standardize_fina_data(combined_df, "YFinance", symbol)
                else:
                    logger.warning(f"YFinance fundamental data for {symbol} is empty.")
                    all_fina_data[symbol] = pd.DataFrame()

            except Exception as e:
                logger.error(f"YFinance fetch_fundamentals for {symbol} failed: {e}", exc_info=True)
                all_fina_data[symbol] = pd.DataFrame()
        return all_fina_data

    @handle_api_errors
    async def fetch_moneyflow(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Yahoo Finance does not provide direct money flow data like Tushare/Akshare."""
        logger.warning("YFinanceDataSource does not support direct money flow data. Returning empty DataFrame.")
        return {symbol: pd.DataFrame() for symbol in symbols}

    @handle_api_errors
    async def fetch_spot_data(self, symbols: Union[str, List[str]]) -> pd.DataFrame:
        """Fetches real-time spot data from Yahoo Finance."""
        logger.info(f"Fetching spot data for {symbols} from YFinance...")
        try:
            if isinstance(symbols, str):
                symbols = [symbols] # Convert single symbol to list
            
            data = []
            for symbol in symbols:
                ticker = await asyncio.to_thread(yf.Ticker, symbol)
                info = await asyncio.to_thread(getattr, ticker, 'fast_info') # Faster info
                if info:
                    data.append({
                        '代码': symbol,
                        '最新价': info.get('lastPrice'),
                        '涨跌幅': info.get('regularMarketChangePercent'),
                        '成交额': info.get('regularMarketVolume'),
                        '名称': info.get('longName') or info.get('shortName')
                        # Add other relevant fields
                    })
            
            df = pd.DataFrame(data)
            return standardize_spot_data(df, "YFinance", symbols)
        except Exception as e:
            logger.error(f"YFinance fetch_spot_data for {symbols} failed: {e}", exc_info=True)
            return pd.DataFrame()

class CCXTDataSource(DataSource):
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not CCXTDataSource._initialized:
            super().__init__("CCXT")
            # Initialize a common exchange (e.g., Binance) or make it configurable
            self.exchange = ccxt.binance({
                'enableRateLimit': True, # Enable built-in rate limiter
                'options': {
                    'defaultType': 'future', # Or 'spot', 'margin' depending on common use case
                },
            })
            # Load markets (synchronous call, do it once)
            asyncio.run(asyncio.to_thread(self.exchange.load_markets))
            CCXTDataSource._initialized = True
            logger.info("CCXTDataSource initialized with Binance.")

    @ccxt_retry_decorator
    @handle_api_errors
    async def fetch_daily(self, symbol: str, start_date: str, end_date: str, is_fund: bool = False) -> pd.DataFrame:
        """Fetches daily historical data (OHLCV) from CCXT for cryptocurrencies."""
        logger.info(f"Fetching daily data for {symbol} from CCXT (start={start_date}, end={end_date})...")
        try:
            # CCXT expects milliseconds timestamp
            since = int(datetime.strptime(start_date, '%Y%m%d').timestamp() * 1000)
            limit = None # Fetch all available data within range
            
            # Fetch OHLCV data ('1d' for daily)
            ohlcv = await asyncio.to_thread(self.exchange.fetch_ohlcv, symbol, '1d', since, limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms').dt.strftime('%Y%m%d')
            df = df.set_index('date').sort_index()
            
            # Filter by end_date
            df_filtered = df[df.index <= end_date]

            return standardize_hist_data(df_filtered, "CCXT", symbol)
        except Exception as e:
            logger.error(f"CCXT fetch_daily for {symbol} failed: {e}", exc_info=True)
            return pd.DataFrame()

    @handle_api_errors
    async def fetch_fundamentals(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """CCXT does not provide traditional fundamental data for cryptocurrencies."""
        logger.warning("CCXTDataSource does not support fundamental data. Returning empty DataFrame.")
        return {symbol: pd.DataFrame() for symbol in symbols}

    @handle_api_errors
    async def fetch_moneyflow(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """CCXT does not provide direct money flow data."""
        logger.warning("CCXTDataSource does not support money flow data. Returning empty DataFrame.")
        return {symbol: pd.DataFrame() for symbol in symbols}

    @handle_api_errors
    async def fetch_spot_data(self, symbols: Union[str, List[str]]) -> pd.DataFrame:
        """Fetches real-time spot data for cryptocurrencies from CCXT."""
        logger.info(f"Fetching spot data for {symbols} from CCXT...")
        try:
            if isinstance(symbols, str):
                symbols = [symbols] # Convert single symbol to list
            
            data = []
            for symbol in symbols:
                ticker = await asyncio.to_thread(self.exchange.fetch_ticker, symbol)
                if ticker:
                    data.append({
                        '代码': ticker.get('symbol'),
                        '最新价': ticker.get('last'),
                        '涨跌幅': ticker.get('percentage'),
                        '成交额': ticker.get('quoteVolume'), # Or 'volume' for base volume
                        '名称': ticker.get('symbol') # Crypto symbols are usually self-descriptive
                    })
            
            df = pd.DataFrame(data)
            return standardize_spot_data(df, "CCXT", symbols)
        except Exception as e:
            logger.error(f"CCXT fetch_spot_data for {symbols} failed: {e}", exc_info=True)
            return pd.DataFrame()

# --- 9. Data Source Registry and Manager ---
class DataSourceRegistry:
    """Manages available data sources and their priorities."""
    def __init__(self):
        self.sources: Dict[str, List[Tuple[DataSource, int]]] = {} # {market_type: [(instance, priority)]}

    def register_source(self, market_type: str, source_instance: DataSource, priority: int = 0):
        """Registers a data source for a given market type."""
        if market_type not in self.sources:
            self.sources[market_type] = []
        self.sources[market_type].append((source_instance, priority))
        # Sort by priority (lower number means higher priority)
        self.sources[market_type].sort(key=lambda x: x[1])
        logger.info(f"Registered data source: {source_instance.data_source_name} for market {market_type} with priority {priority}.")

    def get_sources(self, market_type: str) -> List[DataSource]:
        """Returns a list of data sources for a given market type, ordered by priority."""
        return [source for source, _ in self.sources.get(market_type, [])]

class DataSourceManager:
    """
    Manages data fetching across multiple data sources with fallback logic.
    """
    def __init__(self, registry: DataSourceRegistry):
        self.registry = registry

    @handle_api_errors
    async def get_data(self, method_name: str, market_type: str, symbols: Union[str, List[str]], **kwargs) -> Any:
        """
        Attempts to fetch data using registered data sources for a given market type,
        falling back to lower priority sources on failure.
        """
        sources = self.registry.get_sources(market_type)
        if not sources:
            raise APIError(status.HTTP_404_NOT_FOUND, f"No data sources registered for market type: {market_type}", "NO_DATA_SOURCE")

        for source in sources:
            logger.debug(f"Attempting to fetch data from {source.data_source_name} for market {market_type} using method {method_name}...")
            try:
                # Dynamically call the method on the data source instance
                fetch_method = getattr(source, method_name, None)
                if fetch_method:
                    result = await fetch_method(symbols=symbols, **kwargs, data_source_name=source.data_source_name)
                    if result is not None and (isinstance(result, pd.DataFrame) and not result.empty or isinstance(result, dict) and any(not df.empty for df in result.values())):
                        logger.info(f"Successfully fetched data from {source.data_source_name} for {market_type}.")
                        return result
                    else:
                        logger.warning(f"{source.data_source_name} returned empty or invalid data for {market_type} using method {method_name}. Attempting fallback.")
                else:
                    logger.warning(f"Data source {source.data_source_name} does not have method {method_name}. Attempting fallback.")
            except APIError as e:
                logger.warning(f"Data source {source.data_source_name} failed for {market_type} with APIError: {e.detail}. Attempting fallback.", exc_info=True)
            except Exception as e:
                logger.warning(f"Data source {source.data_source_name} failed for {market_type} with unexpected error: {e}. Attempting fallback.", exc_info=True)
        
        raise APIError(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to fetch data for {market_type} using method {method_name} from all available sources.", "DATA_FETCH_FAILED")

# Initialize registry and register data sources
data_source_registry = DataSourceRegistry()
data_source_registry.register_source("A", TushareDataSource(), priority=1)
data_source_registry.register_source("A", AkshareDataSource(), priority=2) # Akshare as fallback for A-shares
data_source_registry.register_source("HK", YFinanceDataSource(), priority=1) # YFinance for Hong Kong stocks
data_source_registry.register_source("US", YFinanceDataSource(), priority=1) # YFinance for US stocks
data_source_registry.register_source("JP", YFinanceDataSource(), priority=1) # YFinance for Japanese stocks
data_source_registry.register_source("IN", YFinanceDataSource(), priority=1) # YFinance for Indian stocks
data_source_registry.register_source("CRYPTO", CCXTDataSource(), priority=1) # CCXT for cryptocurrencies
data_source_registry.register_source("ETF", TushareDataSource(), priority=1) # Tushare for ETFs (fund_daily)
data_source_registry.register_source("LOF", TushareDataSource(), priority=1) # Tushare for LOFs (fund_daily)

data_source_manager = DataSourceManager(data_source_registry)

# --- 10. Data Standardization Functions ---
def standardize_hist_data(df: pd.DataFrame, source: str, symbol: str) -> pd.DataFrame:
    """Standardizes historical data DataFrame columns."""
    if df.empty:
        logger.warning(f"Standardize historical data: Input DataFrame from {source} for {symbol} is empty.")
        return pd.DataFrame(columns=["date", "open", "close", "high", "low", "volume"])

    standard_cols = ["date", "open", "close", "high", "low", "volume"]
    
    if source == "Tushare":
        df = df.rename(columns={
            'trade_date': 'date', 'open': 'open', 'close': 'close', 
            'high': 'high', 'low': 'low', 'vol': 'volume'
        })
        df['date'] = pd.to_datetime(df['date'])
    elif source == "Akshare":
        df = df.rename(columns={
            '日期': 'date', '开盘': 'open', '收盘': 'close', 
            '最高': 'high', '最低': 'low', '成交量': 'volume'
        })
        df['date'] = pd.to_datetime(df['date'])
    elif source == "YFinance":
        # yfinance columns are already 'Open', 'Close', 'High', 'Low', 'Volume'
        df = df.rename(columns={
            'Open': 'open', 'Close': 'close', 'High': 'high', 
            'Low': 'low', 'Volume': 'volume'
        })
        df['date'] = df.index # Date is in index
        df['date'] = pd.to_datetime(df['date'])
    elif source == "CCXT":
        # CCXT already has 'date', 'open', 'close', 'high', 'low', 'volume'
        df['date'] = pd.to_datetime(df['date']) # Ensure it's datetime
    else:
        logger.warning(f"Unknown data source '{source}' for historical data standardization.")
        return pd.DataFrame(columns=standard_cols)

    # Ensure numeric types and handle missing columns
    for col in ["open", "close", "high", "low", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = np.nan # Add missing column as NaN
            logger.warning(f"Missing column '{col}' for {symbol} from {source} historical data.")

    return df[standard_cols].dropna(subset=["date", "close"]).sort_values(by="date").reset_index(drop=True)

def standardize_fina_data(df: pd.DataFrame, source: str, symbol: str) -> pd.DataFrame:
    """Standardizes financial indicator data."""
    if df.empty:
        logger.warning(f"Standardize financial data: Input DataFrame from {source} for {symbol} is empty.")
        return pd.DataFrame(columns=["report_date", "revenue", "np_yoy", "gross_margin", "roe", "eps", "pb", "pe"])

    standard_cols = ["report_date", "revenue", "np_yoy", "gross_margin", "roe", "eps", "pb", "pe"]
    
    if source == "Tushare":
        df = df.rename(columns={
            'end_date': 'report_date', 
            'total_revenue': 'revenue', 
            'np_yoy': 'np_yoy', 
            'gross_margin': 'gross_margin', 
            'roe': 'roe', 
            'basic_eps': 'eps',
            'pb': 'pb', # Tushare provides PB
            'pe': 'pe' # Tushare provides PE
        })
        df['report_date'] = pd.to_datetime(df['report_date'])
    elif source == "Akshare":
        # Akshare financial indicator fields need careful mapping
        # This is a simplified mapping based on common Akshare financial APIs.
        df = df.rename(columns={
            '报告日期': 'report_date',
            '营业总收入': 'revenue',
            '净利润同比增长率': 'np_yoy',
            '销售毛利率': 'gross_margin',
            '净资产收益率': 'roe',
            '基本每股收益': 'eps',
            '市净率': 'pb',
            '市盈率': 'pe'
        })
        df['report_date'] = pd.to_datetime(df['report_date'])
    elif source == "YFinance":
        # YFinance income_stmt and balance_sheet need manual mapping
        # This is a very simplified example. You'd need to map YFinance specific fields
        # to your standard names.
        df = df.rename(columns={
            'Report Period': 'report_date', # Placeholder, depends on how you combine
            'Total Revenue': 'revenue',
            'Net Income Growth': 'np_yoy', # Placeholder
            'Gross Profit': 'gross_margin', # This is absolute, not margin. Needs calculation.
            'Return On Equity': 'roe', # Placeholder
            'Basic EPS': 'eps', # Placeholder
            'Price Book Value': 'pb', # Placeholder
            'Trailing P/E': 'pe' # Placeholder
        })
        # For YFinance, report_date might be the index or a specific column
        if 'report_date' not in df.columns and isinstance(df.index, pd.DatetimeIndex):
            df['report_date'] = df.index
        df['report_date'] = pd.to_datetime(df['report_date'])
        
        # Calculate gross_margin if 'Gross Profit' and 'Total Revenue' are available
        if 'Gross Profit' in df.columns and 'revenue' in df.columns and not df['revenue'].empty and not df['Gross Profit'].empty:
            df['gross_margin'] = (pd.to_numeric(df['Gross Profit'], errors='coerce') / pd.to_numeric(df['revenue'], errors='coerce')) * 100
        else:
            df['gross_margin'] = np.nan # Set to NaN if not calculable
            logger.warning(f"Could not calculate gross_margin for {symbol} from YFinance.")

        # Handle YFinance specific fields for PB/PE (often in ticker.info or ticker.fast_info)
        # These are usually single values, not time series. You might need to integrate them
        # from the overall analysis results rather than per-report financial data.
        # For now, ensure they are in the dataframe if they can be extracted.
        if 'pb' not in df.columns: df['pb'] = np.nan
        if 'pe' not in df.columns: df['pe'] = np.nan
        if 'eps' not in df.columns: df['eps'] = np.nan
        if 'roe' not in df.columns: df['roe'] = np.nan
        if 'np_yoy' not in df.columns: df['np_yoy'] = np.nan

    else:
        logger.warning(f"Unknown data source '{source}' for financial data standardization.")
        return pd.DataFrame(columns=standard_cols)

    for col in ["revenue", "np_yoy", "gross_margin", "roe", "eps", "pb", "pe"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = np.nan
            logger.warning(f"Missing column '{col}' for {symbol} from {source} financial data.")

    return df[standard_cols].dropna(subset=["report_date"]).sort_values(by="report_date").reset_index(drop=True)

def standardize_moneyflow_data(df: pd.DataFrame, source: str, symbol: str) -> pd.DataFrame:
    """Standardizes money flow data."""
    if df.empty:
        logger.warning(f"Standardize moneyflow data: Input DataFrame from {source} for {symbol} is empty.")
        return pd.DataFrame(columns=["date", "main_net_amount", "retail_net_amount"])

    standard_cols = ["date", "main_net_amount", "retail_net_amount"]

    if source == "Tushare":
        df = df.rename(columns={
            'trade_date': 'date', 
            'buy_sm_vol': 'buy_sm_vol', 'buy_sm_amount': 'buy_sm_amount',
            'sell_sm_vol': 'sell_sm_vol', 'sell_sm_amount': 'sell_sm_amount',
            'buy_md_vol': 'buy_md_vol', 'buy_md_amount': 'buy_md_amount',
            'sell_md_vol': 'sell_md_vol', 'sell_md_amount': 'sell_md_amount',
            'buy_lg_vol': 'buy_lg_vol', 'buy_lg_amount': 'buy_lg_amount',
            'sell_lg_vol': 'sell_lg_vol', 'sell_lg_amount': 'sell_lg_amount',
            'buy_elg_vol': 'buy_elg_vol', 'buy_elg_amount': 'buy_elg_amount',
            'sell_elg_vol': 'sell_elg_vol', 'sell_elg_amount': 'sell_elg_amount',
            'net_mf_amount': 'net_mf_amount' # 总净流入
        })
        df['date'] = pd.to_datetime(df['date'])
        # Calculate main_net_amount (super_large + large net inflow)
        df['main_net_amount'] = (df['buy_elg_amount'] - df['sell_elg_amount']) + \
                                (df['buy_lg_amount'] - df['sell_lg_amount'])
        # Calculate retail_net_amount (small + medium net inflow)
        df['retail_net_amount'] = (df['buy_sm_amount'] - df['sell_sm_amount']) + \
                                  (df['buy_md_amount'] - df['sell_md_amount'])
    elif source == "Akshare":
        df = df.rename(columns={
            '日期': 'date',
            '主力净流入': 'main_net_amount',
            '散户净流入': 'retail_net_amount'
        })
        df['date'] = pd.to_datetime(df['date'])
    else:
        logger.warning(f"Unknown data source '{source}' for money flow data standardization.")
        return pd.DataFrame(columns=standard_cols)

    for col in ["main_net_amount", "retail_net_amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = np.nan
            logger.warning(f"Missing column '{col}' for {symbol} from {source} moneyflow data.")

    return df[standard_cols].dropna(subset=["date"]).sort_values(by="date").reset_index(drop=True)

def standardize_spot_data(df: pd.DataFrame, source: str, symbols: Union[str, List[str]]) -> pd.DataFrame:
    """Standardizes real-time spot data."""
    if df.empty:
        logger.warning(f"Standardize spot data: Input DataFrame from {source} for {symbols} is empty.")
        return pd.DataFrame(columns=["symbol", "name", "latest_price", "change_pct", "volume"])

    standard_cols = ["symbol", "name", "latest_price", "change_pct", "volume"]

    if source == "Akshare":
        df = df.rename(columns={
            '代码': 'symbol',
            '名称': 'name',
            '最新价': 'latest_price',
            '涨跌幅': 'change_pct',
            '成交额': 'volume' # Note: Akshare's '成交额' is usually amount, not volume. Adjust if needed.
        })
    elif source == "YFinance":
        df = df.rename(columns={
            '代码': 'symbol',
            '名称': 'name',
            '最新价': 'latest_price',
            '涨跌幅': 'change_pct',
            '成交额': 'volume'
        })
    elif source == "CCXT":
        df = df.rename(columns={
            '代码': 'symbol',
            '名称': 'name',
            '最新价': 'latest_price',
            '涨跌幅': 'change_pct',
            '成交额': 'volume'
        })
    else:
        logger.warning(f"Unknown data source '{source}' for spot data standardization.")
        return pd.DataFrame(columns=standard_cols)
    
    # Ensure numeric types
    for col in ["latest_price", "change_pct", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = np.nan
            logger.warning(f"Missing column '{col}' for {symbols} from {source} spot data.")

    return df[standard_cols].dropna(subset=["symbol", "latest_price"]).reset_index(drop=True)

# --- 11. Global Data Caching and Retrieval (with latest trading date logic) ---

GLOBAL_STOCK_NAME_MAP_KEY = "global:stock_name_map"
GLOBAL_LATEST_TRADE_DATE_KEY = "global:latest_trade_date"
GLOBAL_MONEYFLOW_IND_THS_KEY = "global:moneyflow_ind_ths"
GLOBAL_STK_FACTOR_PRO_KEY = "global:stk_factor_pro"
GLOBAL_LIMIT_LIST_D_KEY = "global:limit_list_d"
GLOBAL_STK_LIMIT_KEY = "global:stk_limit"
GLOBAL_TOP_INST_KEY = "global:top_inst"
GLOBAL_HM_LIST_KEY = "global:hm_list"
GLOBAL_THS_CONCEPT_MEMBERS_KEY = "global:ths_concept_members"
GLOBAL_THS_HOT_LIST_KEY = "global:ths_hot_list"
GLOBAL_CYQ_CHIPS_KEY_PREFIX = "global:cyq_chips:" # Per symbol

async def _get_latest_trading_date(redis_client: redis.Redis) -> Optional[str]:
    """
    Attempts to get the latest trading date from Redis or Tushare.
    Caches the result.
    """
    cached_date = await asyncio.to_thread(redis_client.get, GLOBAL_LATEST_TRADE_DATE_KEY)
    if cached_date:
        logger.debug(f"Loaded latest trading date from cache: {cached_date.decode()}.")
        return cached_date.decode()
    
    logger.info("Fetching latest trading date from Tushare...")
    try:
        tushare_ds = TushareDataSource()
        # Use a small date range to get the latest daily data, then extract the date
        df_latest = await tushare_ds._call_tushare_api('daily', trade_date='', start_date=(datetime.now() - timedelta(days=10)).strftime('%Y%m%d'), end_date=datetime.now().strftime('%Y%m%d'), limit=1)
        if not df_latest.empty:
            latest_date_str = df_latest['trade_date'].iloc[0]
            await asyncio.to_thread(redis_client.setex, GLOBAL_LATEST_TRADE_DATE_KEY, app_params.A.name_map_cache_ttl, latest_date_str)
            logger.info(f"Cached latest trading date: {latest_date_str}.")
            return latest_date_str
        else:
            logger.warning("Tushare daily API returned empty for latest trading date. Falling back to current date.")
            return datetime.now().strftime('%Y%m%d') # Fallback to current date
    except Exception as e:
        logger.error(f"Failed to get latest trading date from Tushare: {e}", exc_info=True)
        return datetime.now().strftime('%Y%m%d') # Fallback to current date

async def get_stock_name_map_and_cache(redis_client: redis.Redis) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Fetches stock name and industry map from cache or Tushare/Akshare.
    Caches the result.
    Returns (stock_code: stock_name), (stock_code: industry_name)
    """
    cached_data = await load_cached_dataframe_incremental(redis_client, GLOBAL_STOCK_NAME_MAP_KEY)
    if cached_data is not None and not cached_data.empty:
        stock_name_map = dict(zip(cached_data['ts_code'], cached_data['name']))
        industry_map = dict(zip(cached_data['ts_code'], cached_data['industry']))
        logger.debug("Loaded stock name and industry map from cache.")
        return stock_name_map, industry_map

    logger.info("Fetching stock name and industry map from Tushare...")
    try:
        tushare_ds = TushareDataSource()
        df_stock_basic = await tushare_ds._call_tushare_api('stock_basic', exchange='', list_status='L', fields='ts_code,symbol,name,industry,list_date')
        if not df_stock_basic.empty:
            df_stock_basic['industry'] = df_stock_basic['industry'].fillna('未知行业')
            stock_name_map = dict(zip(df_stock_basic['ts_code'], df_stock_basic['name']))
            industry_map = dict(zip(df_stock_basic['ts_code'], df_stock_basic['industry']))
            
            # Cache incrementally
            await cache_dataframe_incremental(redis_client, GLOBAL_STOCK_NAME_MAP_KEY, df_stock_basic, app_params.A.name_map_cache_ttl)
            logger.info("Cached stock name and industry map from Tushare.")
            return stock_name_map, industry_map
        else:
            logger.warning("Tushare stock_basic returned empty. Falling back to Akshare.")
    except Exception as e:
        logger.warning(f"Failed to get stock_basic from Tushare: {e}. Falling back to Akshare.", exc_info=True)

    logger.info("Fetching stock name and industry map from Akshare...")
    try:
        akshare_ds = AkshareDataSource()
        df_stock_info = await asyncio.to_thread(ak.stock_zh_a_spot_em) # Example: Eastmoney A-share spot data contains name/code
        if not df_stock_info.empty:
            df_stock_info = df_stock_info.rename(columns={'代码': 'ts_code', '名称': 'name'})
            # Akshare might not have direct industry mapping in this API, use a placeholder
            df_stock_info['industry'] = '未知行业' 
            stock_name_map = dict(zip(df_stock_info['ts_code'], df_stock_info['name']))
            industry_map = dict(zip(df_stock_info['ts_code'], df_stock_info['industry']))
            
            # Cache incrementally
            await cache_dataframe_incremental(redis_client, GLOBAL_STOCK_NAME_MAP_KEY, df_stock_info[['ts_code', 'name', 'industry']], app_params.A.name_map_cache_ttl)
            logger.info("Cached stock name and industry map from Akshare.")
            return stock_name_map, industry_map
        else:
            logger.error("Akshare stock_zh_a_spot_em returned empty for stock name map.")
    except Exception as e:
        logger.error(f"Failed to get stock name map from Akshare: {e}", exc_info=True)

    logger.error("Failed to get stock name and industry map from all sources. Returning empty maps.")
    return {}, {}

async def get_latest_trading_date(redis_client: redis.Redis) -> Optional[str]:
    """
    Gets the latest trading date, preferring cache, then Tushare.
    """
    return await _get_latest_trading_date(redis_client)

async def _get_latest_trading_date_data(redis_client: redis.Redis, key: str, ttl: int, fetch_func: callable, *args, **kwargs) -> pd.DataFrame:
    """
    Helper function to fetch global data that depends on the latest trading date.
    It tries to load from cache first. If not found or stale, it fetches for the latest
    trading date. If that fails, it tries to fetch for the previous trading date, and so on,
    up to a few attempts.
    """
    latest_trade_date_str = await get_latest_trading_date(redis_client)
    if not latest_trade_date_str:
        logger.error(f"Could not retrieve latest trading date for key: {key}. Returning empty DataFrame.")
        return pd.DataFrame()

    current_date = datetime.strptime(latest_trade_date_str, '%Y%m%d')
    
    for i in range(settings.get('MAX_DATE_FALLBACK_ATTEMPTS', 3)): # Try current date and a few previous dates
        target_date = current_date - timedelta(days=i)
        target_date_str = target_date.strftime('%Y%m%d')
        
        # Adjust key for specific date if needed (e.g., for daily changing data)
        dated_key = f"{key}:{target_date_str}" if "daily" in key or "list_d" in key else key # Example: global:limit_list_d:20230101
        
        cached_data = await load_cached_dataframe_incremental(redis_client, dated_key)
        if cached_data is not None and not cached_data.empty:
            logger.debug(f"Loaded data for {key} from cache for date {target_date_str}.")
            return cached_data
        
        logger.info(f"Fetching data for {key} for date {target_date_str} (attempt {i+1})...")
        try:
            # Pass the target_date_str to the fetch_func if it expects a date
            # Assuming fetch_func takes 'trade_date' or similar as a keyword arg
            fetch_kwargs = {**kwargs, 'trade_date': target_date_str} if 'trade_date' not in kwargs else kwargs
            df = await fetch_func(*args, **fetch_kwargs)
            
            if not df.empty:
                await cache_dataframe_incremental(redis_client, dated_key, df, ttl)
                logger.info(f"Cached data for {key} for date {target_date_str}.")
                return df
            else:
                logger.warning(f"Fetch function for {key} returned empty for date {target_date_str}.")
        except Exception as e:
            logger.warning(f"Failed to fetch data for {key} for date {target_date_str}: {e}", exc_info=True)
            # Continue to next fallback date

    logger.error(f"Failed to fetch data for {key} from all fallback dates. Returning empty DataFrame.")
    return pd.DataFrame()

async def get_moneyflow_ind_ths_data_and_cache(redis_client: redis.Redis) -> pd.DataFrame:
    """Fetches and caches money flow industry data (THS)."""
    return await _get_latest_trading_date_data(
        redis_client, 
        GLOBAL_MONEYFLOW_IND_THS_KEY, 
        app_params.A.moneyflow_ind_ths_cache_ttl, 
        lambda trade_date: asyncio.to_thread(ak.stock_money_flow_industry_ths, trade_date=trade_date)
    )

async def get_stk_factor_pro_data_and_cache(redis_client: redis.Redis) -> pd.DataFrame:
    """Fetches and caches stock factor data."""
    return await _get_latest_trading_date_data(
        redis_client, 
        GLOBAL_STK_FACTOR_PRO_KEY, 
        app_params.A.stk_factor_pro_cache_ttl, 
        lambda trade_date: TushareDataSource()._call_tushare_api('stk_factor', trade_date=trade_date)
    )

async def get_limit_list_d_data_and_cache(redis_client: redis.Redis) -> pd.DataFrame:
    """Fetches and caches daily limit-up/down statistics."""
    return await _get_latest_trading_date_data(
        redis_client, 
        GLOBAL_LIMIT_LIST_D_KEY, 
        app_params.A.limit_list_d_cache_ttl, 
        lambda trade_date: TushareDataSource()._call_tushare_api('limit_list_d', trade_date=trade_date)
    )

async def get_stk_limit_data_and_cache(redis_client: redis.Redis) -> pd.DataFrame:
    """Fetches and caches stock limit-up/down price data."""
    return await _get_latest_trading_date_data(
        redis_client, 
        GLOBAL_STK_LIMIT_KEY, 
        app_params.A.stk_limit_cache_ttl, 
        lambda trade_date: TushareDataSource()._call_tushare_api('stk_limit', trade_date=trade_date)
    )

async def get_top_inst_data_and_cache(redis_client: redis.Redis) -> pd.DataFrame:
    """Fetches and caches institutional Dragon-Tiger list data."""
    return await _get_latest_trading_date_data(
        redis_client, 
        GLOBAL_TOP_INST_KEY, 
        app_params.A.top_inst_cache_ttl, 
        lambda trade_date: TushareDataSource()._call_tushare_api('top_inst', trade_date=trade_date)
    )

async def get_hm_list_data_and_cache(redis_client: redis.Redis) -> pd.DataFrame:
    """Fetches and caches hot money list data."""
    # HM list might not be daily, so we fetch it once and cache for longer
    # Or fetch for the latest available date
    return await _get_latest_trading_date_data(
        redis_client, 
        GLOBAL_HM_LIST_KEY, 
        app_params.A.hm_list_cache_ttl, 
        lambda trade_date: asyncio.to_thread(ak.stock_hot_rank_detail_board) # Akshare hot list, might not need trade_date
    )

async def get_ths_concept_members_and_cache(redis_client: redis.Redis) -> pd.DataFrame:
    """Fetches and caches Tonghuashun concept constituent stock data."""
    # This data is usually not daily, so we fetch it once and cache for longer
    return await _get_latest_trading_date_data(
        redis_client, 
        GLOBAL_THS_CONCEPT_MEMBERS_KEY, 
        app_params.A.ths_member_cache_ttl, 
        lambda trade_date: asyncio.to_thread(ak.stock_board_ths_member_by_code) # Akshare THS concept members, does not need trade_date
    )

async def get_ths_hot_list_and_cache(redis_client: redis.Redis) -> pd.DataFrame:
    """Fetches and caches Tonghuashun hot list data."""
    # This data is usually daily, so we fetch it for the latest trading date
    return await _get_latest_trading_date_data(
        redis_client, 
        GLOBAL_THS_HOT_LIST_KEY, 
        app_params.A.ths_hot_cache_ttl, 
        lambda trade_date: asyncio.to_thread(ak.stock_board_ths_topic_info_ths) # Akshare THS hot list, does not need trade_date
    )

async def get_cyq_chips_data_and_cache_for_symbol(redis_client: redis.Redis, symbol: str) -> pd.DataFrame:
    """Fetches and caches daily chip distribution data for a specific symbol."""
    # This data is per-symbol and per-date
    key = f"{GLOBAL_CYQ_CHIPS_KEY_PREFIX}{symbol}"
    return await _get_latest_trading_date_data(
        redis_client, 
        key, 
        app_params.A.cyq_chips_cache_ttl, 
        lambda trade_date: asyncio.to_thread(ak.stock_cyq_em, symbol=symbol, date=trade_date) # Akshare chip distribution
    )

# --- 11. Analysis Modules ---
class AnalysisModule(ABC):
    """Abstract base class for all analysis modules."""
    @abstractmethod
    def analyze(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs analysis on the given data and returns results.
        Data is input from the main fetching process.
        Context is a dictionary of results from previously run modules.
        Returns a dictionary of analysis results.
        """
        pass

# Prometheus metric for analysis module execution time
analysis_module_execution_time = Histogram(
    'stock_api_analysis_module_execution_time_seconds',
    'Time taken for analysis modules to execute',
    ['module_name']
)

class TechnicalAnalyzer(AnalysisModule):
    @analysis_module_execution_time.labels(module_name='TechnicalAnalyzer').time()
    def analyze(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        stock_data = data.get('stock_data')
        market_type = data.get('market_type', 'A')
        
        if stock_data is None or stock_data.empty:
            logger.warning("TechnicalAnalyzer: Missing stock_data.")
            data_completeness_counter.labels(module='TechnicalAnalyzer', field='missing_stock_data').inc()
            return {}

        df = stock_data.copy()
        
        # Ensure 'date' column is datetime and sorted
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values(by='date').reset_index(drop=True)
        else:
            logger.error("TechnicalAnalyzer: 'date' column not found in stock_data.")
            data_completeness_counter.labels(module='TechnicalAnalyzer', field='no_date_column').inc()
            return {}

        # Get parameters from app_params
        params = app_params.get(market_type, app_params.A) # Fallback to A-share params
        
        ma_short_period = params.get('ma_periods', {}).get('short', 5)
        ma_medium_period = params.get('ma_periods', {}).get('medium', 20)
        macd_fast = params.get('macd_params', {}).get('fast', 12)
        macd_slow = params.get('macd_params', {}).get('slow', 26)
        macd_signal = params.get('macd_params', {}).get('signal', 9)
        rsi_period = params.get('rsi_period', 14)
        
        # Calculate Technical Indicators
        df['MA_short'] = df['close'].rolling(window=ma_short_period).mean()
        df['MA_medium'] = df['close'].rolling(window=ma_medium_period).mean()

        # MACD
        exp1 = df['close'].ewm(span=macd_fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=macd_slow, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=macd_signal, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        df['BB_Middle'] = df['close'].rolling(window=params.get('bollinger_period', 20)).mean()
        df['BB_StdDev'] = df['close'].rolling(window=params.get('bollinger_period', 20)).std()
        df['BB_Upper'] = df['BB_Middle'] + (df['BB_StdDev'] * params.get('bollinger_std', 2))
        df['BB_Lower'] = df['BB_Middle'] - (df['BB_StdDev'] * params.get('bollinger_std', 2))
        
        # Latest values
        latest_close = df['close'].iloc[-1]
        latest_ma_short = df['MA_short'].iloc[-1]
        latest_ma_medium = df['MA_medium'].iloc[-1]
        latest_macd_hist = df['MACD_Hist'].iloc[-1]
        latest_rsi = df['RSI'].iloc[-1]

        detailed_parts = []
        bullish_factors = []
        bearish_factors = []
        neutral_factors = []
        technical_summary = {}

        detailed_parts.append("技术指标分析:")
        technical_summary['latest_close'] = latest_close
        technical_summary['MA_short'] = latest_ma_short
        technical_summary['MA_medium'] = latest_ma_medium
        technical_summary['MACD_Hist'] = latest_macd_hist
        technical_summary['RSI'] = latest_rsi

        if pd.notna(latest_close) and pd.notna(latest_ma_short):
            detailed_parts.append(f"  最新价: {latest_close:.2f}，短期均线(MA{ma_short_period}): {latest_ma_short:.2f}。")
            if latest_close > latest_ma_short:
                bullish_factors.append(f"股价站上MA{ma_short_period}短期均线")
            else:
                bearish_factors.append(f"股价跌破MA{ma_short_period}短期均线")

        if pd.notna(latest_close) and pd.notna(latest_ma_medium):
            detailed_parts.append(f"  中期均线(MA{ma_medium_period}): {latest_ma_medium:.2f}。")
            if latest_close > latest_ma_medium:
                bullish_factors.append(f"股价站上MA{ma_medium_period}中期均线")
            else:
                bearish_factors.append(f"股价跌破MA{ma_medium_period}中期均线")

        if pd.notna(latest_macd_hist):
            detailed_parts.append(f"  MACD柱线: {latest_macd_hist:.2f}。")
            if latest_macd_hist > 0:
                bullish_factors.append("MACD柱线为正，多头占优")
            else:
                bearish_factors.append("MACD柱线为负，空头占优")

        if pd.notna(latest_rsi):
            detailed_parts.append(f"  RSI({rsi_period}): {latest_rsi:.2f}。")
            if latest_rsi > 70:
                bearish_factors.append("RSI超买，短期有回调风险")
            elif latest_rsi < 30:
                bullish_factors.append("RSI超卖，短期有反弹可能")
            else:
                neutral_factors.append("RSI处于中性区域")
        
        # Update context with technical analysis results
        context['TechnicalAnalyzer'] = {
            'latest_close': latest_close,
            'MA_short': latest_ma_short,
            'MA_medium': latest_ma_medium,
            'MACD_Hist': latest_macd_hist,
            'RSI': latest_rsi,
            'bollinger_upper': df['BB_Upper'].iloc[-1] if not df.empty else None,
            'bollinger_lower': df['BB_Lower'].iloc[-1] if not df.empty else None,
            'bollinger_middle': df['BB_Middle'].iloc[-1] if not df.empty else None
        }

        return {
            'detailed_parts': detailed_parts,
            'bullish_factors': bullish_factors,
            'bearish_factors': bearish_factors,
            'neutral_factors': neutral_factors,
            'technical_summary': technical_summary # Return summary for report
        }

class FundamentalAnalyzer(AnalysisModule):
    @analysis_module_execution_time.labels(module_name='FundamentalAnalyzer').time()
    def analyze(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        fina_data = data.get('fina_data')
        
        if fina_data is None or fina_data.empty:
            logger.warning("FundamentalAnalyzer: Missing financial data.")
            data_completeness_counter.labels(module='FundamentalAnalyzer', field='missing_fina_data').inc()
            return {}

        detailed_parts = []
        bullish_factors = []
        bearish_factors = []
        neutral_factors = []

        detailed_parts.append("基本面分析:")

        # Get latest financial report
        latest_fina = fina_data.sort_values(by='report_date', ascending=False).iloc[0]
        
        revenue_yoy = latest_fina.get('revenue_yoy')
        np_yoy = latest_fina.get('np_yoy')
        gross_margin = latest_fina.get('gross_margin')
        roe = latest_fina.get('roe')
        eps = latest_fina.get('eps')
        pb = latest_fina.get('pb')
        pe = latest_fina.get('pe')

        # Add to technical summary for overall context
        context['FundamentalAnalyzer'] = {
            'revenue_yoy': revenue_yoy,
            'np_yoy': np_yoy,
            'gross_margin': gross_margin,
            'roe': roe,
            'eps': eps,
            'pb': pb,
            'pe': pe
        }

        if pd.notna(revenue_yoy):
            detailed_parts.append(f"  最新营收同比增长: {revenue_yoy:.2f}%。")
            if revenue_yoy > 15:
                bullish_factors.append(f"营收同比增长强劲 ({revenue_yoy:.2f}%)")
            elif revenue_yoy < 0:
                bearish_factors.append(f"营收同比下降 ({revenue_yoy:.2f}%)")
            else:
                neutral_factors.append("营收同比增长平稳")

        if pd.notna(np_yoy):
            detailed_parts.append(f"  最新净利润同比增长: {np_yoy:.2f}%。")
            if np_yoy > 15:
                bullish_factors.append(f"净利润同比增长强劲 ({np_yoy:.2f}%)")
            elif np_yoy < 0:
                bearish_factors.append(f"净利润同比下降 ({np_yoy:.2f}%)")
            else:
                neutral_factors.append("净利润同比增长平稳")
        
        if pd.notna(gross_margin):
            detailed_parts.append(f"  最新销售毛利率: {gross_margin:.2f}%。")
            if gross_margin > 30: # Example threshold
                bullish_factors.append(f"毛利率较高 ({gross_margin:.2f}%)")
            elif gross_margin < 10:
                bearish_factors.append(f"毛利率较低 ({gross_margin:.2f}%)")
            else:
                neutral_factors.append("毛利率处于行业平均水平")

        if pd.notna(roe):
            detailed_parts.append(f"  最新净资产收益率(ROE): {roe:.2f}%。")
            if roe > 10: # Example threshold
                bullish_factors.append(f"ROE较高，盈利能力强 ({roe:.2f}%)")
            elif roe < 5:
                bearish_factors.append(f"ROE较低，盈利能力弱 ({roe:.2f}%)")
            else:
                neutral_factors.append("ROE处于合理水平")

        if pd.notna(pe):
            detailed_parts.append(f"  最新市盈率(PE): {pe:.2f}。")
            # PE analysis requires industry context, here's a simplified example
            if pe > 100: # Example for high growth tech or overvalued
                bearish_factors.append(f"市盈率偏高 ({pe:.2f})，估值风险")
            elif pe < 20 and pe > 0: # Example for undervalued or stable
                bullish_factors.append(f"市盈率偏低 ({pe:.2f})，估值吸引")
            else:
                neutral_factors.append("市盈率处于合理区间")

        if pd.notna(pb):
            detailed_parts.append(f"  最新市净率(PB): {pb:.2f}。")
            if pb > 5: # Example for high valuation
                bearish_factors.append(f"市净率偏高 ({pb:.2f})，估值风险")
            elif pb < 1.5 and pb > 0: # Example for undervalued
                bullish_factors.append(f"市净率偏低 ({pb:.2f})，估值吸引")
            else:
                neutral_factors.append("市净率处于合理区间")

        return {
            'detailed_parts': detailed_parts,
            'bullish_factors': bullish_factors,
            'bearish_factors': bearish_factors,
            'neutral_factors': neutral_factors,
            'revenue_yoy': revenue_yoy, # Pass these up for summary phrase generation
            'np_yoy': np_yoy,
            'gross_margin': gross_margin,
            'roe': roe,
            'eps': eps,
            'pb': pb,
            'pe': pe
        }

class MarketSentimentAnalyzer(AnalysisModule):
    @analysis_module_execution_time.labels(module_name='MarketSentimentAnalyzer').time()
    def analyze(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        symbol = data.get('symbol')
        limit_list_d_data = data.get('limit_list_d_data')
        stk_limit_data = data.get('stk_limit_data')
        ak_spot_data = data.get('ak_spot_data')
        top_inst_data_for_symbol = data.get('top_inst_data_for_symbol')
        hm_list_data = data.get('hm_list_data')
        
        detailed_parts = []
        bullish_factors = []
        bearish_factors = []
        neutral_factors = []

        detailed_parts.append("市场情绪与资金流向分析:")
        
        limit_status = "NORMAL"
        trade_amount_limit_d = None
        consecutive_limit_up = None
        limit_up_price = None
        limit_down_price = None

        # 涨跌停分析
        if limit_list_d_data is not None and not limit_list_d_data.empty:
            limit_up_count = limit_list_d_data['涨停家数'].iloc[-1] if '涨停家数' in limit_list_d_data.columns else None
            limit_down_count = limit_list_d_data['跌停家数'].iloc[-1] if '跌停家数' in limit_list_d_data.columns else None
            if limit_up_count is not None:
                detailed_parts.append(f"  今日A股涨停家数: {limit_up_count}。")
            if limit_down_count is not None:
                detailed_parts.append(f"  今日A股跌停家数: {limit_down_count}。")
            
            # Check individual stock limit status
            if stk_limit_data is not None and not stk_limit_data.empty:
                symbol_limit_info = stk_limit_data[stk_limit_data['ts_code'] == symbol]
                if not symbol_limit_info.empty:
                    latest_limit_info = symbol_limit_info.iloc[-1]
                    limit_status_raw = latest_limit_info.get('limit_status')
                    trade_amount_limit_d = latest_limit_info.get('trade_amount')
                    consecutive_limit_up = latest_limit_info.get('up_num')
                    limit_up_price = latest_limit_info.get('up_price')
                    limit_down_price = latest_limit_info.get('down_price')

                    if limit_status_raw == 1: # 涨停
                        limit_status = "LIMIT_UP"
                        detailed_parts.append(f"  该股今日涨停，涨停价: {limit_up_price:.2f}。已连续涨停 {consecutive_limit_up} 天。")
                        bullish_factors.append("今日涨停，市场情绪高涨")
                    elif limit_status_raw == 2: # 跌停
                        limit_status = "LIMIT_DOWN"
                        detailed_parts.append(f"  该股今日跌停，跌停价: {limit_down_price:.2f}。")
                        bearish_factors.append("今日跌停，存在较大风险")
                    else:
                        detailed_parts.append("  该股今日未涨跌停。")
                        neutral_factors.append("股价正常波动")
                else:
                    neutral_factors.append("未找到该股涨跌停信息")
            else:
                neutral_factors.append("涨跌停数据缺失")
        else:
            neutral_factors.append("全局涨跌停统计数据缺失")

        # 实时涨跌幅 (来自Akshare spot data)
        realtime_change_pct_spot = None
        if ak_spot_data is not None and not ak_spot_data.empty:
            symbol_spot_info = ak_spot_data[ak_spot_data['symbol'] == symbol]
            if not symbol_spot_info.empty:
                realtime_change_pct_spot = symbol_spot_info['change_pct'].iloc[0]
                detailed_parts.append(f"  实时涨跌幅: {realtime_change_pct_spot:.2f}%。")
                if realtime_change_pct_spot > 5:
                    bullish_factors.append(f"实时涨幅较大 ({realtime_change_pct_spot:.2f}%)")
                elif realtime_change_pct_spot < -5:
                    bearish_factors.append(f"实时跌幅较大 ({realtime_change_pct_spot:.2f}%)")
            else:
                neutral_factors.append("未找到实时行情数据")
        else:
            neutral_factors.append("实时行情数据缺失")

        # 龙虎榜机构资金分析
        total_net_amount_top_inst = None
        if top_inst_data_for_symbol is not None and not top_inst_data_for_symbol.empty:
            # Sum net buy/sell from institutions
            total_net_amount_top_inst = top_inst_data_for_symbol['net_buy_amount'].sum() # Assuming net_buy_amount is available
            detailed_parts.append(f"  龙虎榜机构净买入额: {total_net_amount_top_inst/10000:.2f}万元。")
            if total_net_amount_top_inst > 0:
                bullish_factors.append(f"龙虎榜机构净买入 ({total_net_amount_top_inst/10000:.2f}万元)")
            elif total_net_amount_top_inst < 0:
                bearish_factors.append(f"龙虎榜机构净卖出 ({total_net_amount_top_inst/10000:.2f}万元)")
            else:
                neutral_factors.append("龙虎榜机构资金无明显动向")
        else:
            neutral_factors.append("龙虎榜机构数据缺失")

        # 游资龙虎榜分析
        hm_list_available = False
        hot_money_on_dragon_tiger_list = []
        if hm_list_data is not None and not hm_list_data.empty:
            hm_list_available = True
            # Check if the symbol is on the hot money list
            symbol_on_hm_list = hm_list_data[hm_list_data['股票代码'] == symbol]
            if not symbol_on_hm_list.empty:
                for idx, row in symbol_on_hm_list.iterrows():
                    hot_money_on_dragon_tiger_list.append(f"{row['营业部名称']} ({row['上榜类型']})")
                detailed_parts.append(f"  该股上榜游资龙虎榜: {', '.join(hot_money_on_dragon_tiger_list)}。")
                bullish_factors.append("上榜游资龙虎榜，市场关注度高")
            else:
                neutral_factors.append("未上游资龙虎榜")
        else:
            neutral_factors.append("游资龙虎榜数据缺失")

        # 个股资金流向 (moneyflow_dc)
        main_net_amount_dc = None
        retail_net_amount_dc = None
        if data.get('moneyflow_dc_data') is not None and not data['moneyflow_dc_data'].empty:
            latest_moneyflow = data['moneyflow_dc_data'].iloc[-1]
            main_net_amount_dc = latest_moneyflow.get('main_net_amount')
            retail_net_amount_dc = latest_moneyflow.get('retail_net_amount')

            if pd.notna(main_net_amount_dc):
                detailed_parts.append(f"  主力净流入: {main_net_amount_dc/10000:.2f}万元。")
                if main_net_amount_dc > 0:
                    bullish_factors.append(f"主力资金净流入 ({main_net_amount_dc/10000:.2f}万元)")
                else:
                    bearish_factors.append(f"主力资金净流出 ({main_net_amount_dc/10000:.2f}万元)")
            
            if pd.notna(retail_net_amount_dc):
                detailed_parts.append(f"  散户净流入: {retail_net_amount_dc/10000:.2f}万元。")
                if retail_net_amount_dc > 0:
                    bearish_factors.append(f"散户资金净流入 ({retail_net_amount_dc/10000:.2f}万元)") # 散户流入通常视为负面
                else:
                    bullish_factors.append(f"散户资金净流出 ({retail_net_amount_dc/10000:.2f}万元)") # 散户流出通常视为正面
        else:
            neutral_factors.append("个股资金流向数据缺失")

        # Update context for summary phrase generation
        context['MarketSentimentAnalyzer'] = {
            'limit_status': limit_status,
            'total_net_amount_top_inst': total_net_amount_top_inst,
            'main_net_amount_dc': main_net_amount_dc,
            'retail_net_amount_dc': retail_net_amount_dc
        }

        return {
            'limit_status': limit_status, # Pass up for summary phrase generation
            'trade_amount_limit_d': trade_amount_limit_d,
            'consecutive_limit_up': consecutive_limit_up,
            'limit_up_price': limit_up_price,
            'limit_down_price': limit_down_price,
            'realtime_change_pct_spot': realtime_change_pct_spot,
            'total_net_amount_top_inst': total_net_amount_top_inst,
            'hm_list_available': hm_list_available,
            'hot_money_on_dragon_tiger_list': hot_money_on_dragon_tiger_list,
            'main_net_amount_dc': main_net_amount_dc,
            'retail_net_amount_dc': retail_net_amount_dc,
            'detailed_parts': detailed_parts,
            'bullish_factors': bullish_factors,
            'bearish_factors': bearish_factors,
            'neutral_factors': neutral_factors
        }

class IndustryConceptAnalyzer(AnalysisModule):
    @analysis_module_execution_time.labels(module_name='IndustryConceptAnalyzer').time()
    def analyze(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        symbol = data.get('symbol')
        current_industry = data.get('current_industry')
        moneyflow_ind_ths_data = data.get('moneyflow_ind_ths_data')
        ths_concept_members_data = data.get('ths_concept_members_data')
        ths_hot_list_data = data.get('ths_hot_list_data')

        detailed_parts = []
        bullish_factors = []
        bearish_factors = []
        neutral_factors = []

        detailed_parts.append("行业与概念分析:")

        # 行业资金流向
        main_net_inflow_ind = None
        if moneyflow_ind_ths_data is not None and not moneyflow_ind_ths_data.empty and current_industry != "未知行业":
            industry_flow = moneyflow_ind_ths_data[moneyflow_ind_ths_data['行业名称'] == current_industry]
            if not industry_flow.empty:
                main_net_inflow_ind = industry_flow['主力净流入'].iloc[0]
                detailed_parts.append(f"  所属行业({current_industry})主力净流入: {main_net_inflow_ind/10000:.2f}万元。")
                if main_net_inflow_ind > 0:
                    bullish_factors.append(f"行业({current_industry})主力资金净流入")
                else:
                    bearish_factors.append(f"行业({current_industry})主力资金净流出")
            else:
                neutral_factors.append(f"未找到行业({current_industry})资金流向数据")
        else:
            neutral_factors.append("行业资金流向数据缺失或行业未知")

        # 同花顺概念
        ths_concepts_for_symbol = []
        if ths_concept_members_data is not None and not ths_concept_members_data.empty:
            concepts_df = ths_concept_members_data[ths_concept_members_data['code'] == symbol]
            if not concepts_df.empty:
                ths_concepts_for_symbol = list(set(concepts_df['concept_name'].tolist()))
        
        if ths_concepts_for_symbol:
            detailed_parts.append(f"  所属概念: {', '.join(ths_concepts_for_symbol)}。")
            neutral_factors.append(f"所属概念: {', '.join(ths_concepts_for_symbol)}")
        else:
            neutral_factors.append("未找到所属THS概念")

        # THS Hot List Analysis
        detailed_parts.append("THS热点榜:")
        ths_hot_info_output: Optional[Dict[str, Any]] = None
        if ths_hot_list_data is not None and not ths_hot_list_data.empty:
            # Check if stock itself is on hot list (indexed by symbol/hot_name)
            if symbol in ths_hot_list_data.index and ths_hot_list_data.loc[symbol].get('hot_type') == '股票':
                ths_hot_info_output = ths_hot_list_data.loc[symbol].to_dict()
            # Check if industry is on hot list
            elif current_industry and current_industry in ths_hot_list_data.index and ths_hot_list_data.loc[current_industry].get('hot_type') == '行业':
                ths_hot_info_output = ths_hot_list_data.loc[current_industry].to_dict()
            # Check if any concept is on hot list
            else:
                for concept in ths_concepts_for_symbol: # Iterate through the concepts found for the symbol
                    if concept in ths_hot_list_data.index and ths_hot_list_data.loc[concept].get('hot_type') == '概念':
                        ths_hot_info_output = ths_hot_list_data.loc[concept].to_dict()
                        break 
            
            if ths_hot_info_output:
                hot_name = ths_hot_info_output.get('hot_name')
                hot_type = ths_hot_info_output.get('hot_type')
                hot_value = ths_hot_info_output.get('hot_value')
                change_rate = ths_hot_info_output.get('change_rate')
                detailed_parts.append(f"  上榜热点: {hot_name} ({hot_type}，热度值{hot_value:.2f}，涨幅{change_rate:.2f}%)。")
                if hot_type == '股票':
                    bullish_factors.append(f"股票上榜热点: {hot_name}")
                elif hot_type == '行业':
                    bullish_factors.append(f"所属行业上榜热点: {hot_name}")
                elif hot_type == '概念':
                    bullish_factors.append(f"所属概念上榜热点: {hot_name}")
            else:
                neutral_factors.append("未上THS热点榜")

        return {
            'main_net_inflow_ind': main_net_inflow_ind,
            'ths_concepts': ths_concepts_for_symbol,
            'ths_hot_info': ths_hot_info_output,
            'detailed_parts': detailed_parts,
            'bullish_factors': bullish_factors,
            'bearish_factors': bearish_factors,
            'neutral_factors': neutral_factors
        }

class CostAnalyzer(AnalysisModule):
    @analysis_module_execution_time.labels(module_name='CostAnalyzer').time()
    def analyze(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        stock_data = data.get('stock_data')
        latest_price = data.get('latest_price') # From input data, or TechnicalAnalyzer context

        if stock_data is None or stock_data.empty or latest_price is None:
            logger.warning("CostAnalyzer: Missing stock_data or latest_price.")
            data_completeness_counter.labels(module='CostAnalyzer', field='missing_input').inc()
            return {}

        df_copy = stock_data.copy()
        
        # Calculate simple moving averages as cost approximations
        # MA5 as short-term cost, MA20 as medium-term cost
        df_copy['MA5'] = df_copy['close'].rolling(window=5).mean()
        df_copy['MA20'] = df_copy['close'].rolling(window=20).mean()

        short_term_cost_approx = df_copy['MA5'].iloc[-1] if not df_copy.empty else None
        medium_term_cost_approx = df_copy['MA20'].iloc[-1] if not df_copy.empty else None

        cost_analysis_results = {
            "short_term_cost_approx": short_term_cost_approx,
            "medium_term_cost_approx": medium_term_cost_approx,
            "current_price": latest_price,
            "short_term_profit_status": "N/A",
            "medium_term_profit_status": "N/A"
        }

        detailed_parts = []
        bullish_factors = []
        bearish_factors = []
        neutral_factors = []

        detailed_parts.append("成本分析:")
        
        if short_term_cost_approx is not None and pd.notna(short_term_cost_approx):
            detailed_parts.append(f"  短期成本(MA5): {short_term_cost_approx:.2f}。")
            if latest_price > short_term_cost_approx:
                cost_analysis_results["short_term_profit_status"] = "获利"
                bullish_factors.append("股价高于短期成本")
            elif latest_price < short_term_cost_approx:
                cost_analysis_results["short_term_profit_status"] = "亏损"
                bearish_factors.append("股价低于短期成本")
            else:
                cost_analysis_results["short_term_profit_status"] = "持平"
                neutral_factors.append("股价与短期成本持平")
            detailed_parts.append(f"  短期获利状态: {cost_analysis_results['short_term_profit_status']}。")
        else:
            neutral_factors.append("短期成本数据缺失")

        if medium_term_cost_approx is not None and pd.notna(medium_term_cost_approx):
            detailed_parts.append(f"  中期成本(MA20): {medium_term_cost_approx:.2f}。")
            if latest_price > medium_term_cost_approx:
                cost_analysis_results["medium_term_profit_status"] = "获利"
                bullish_factors.append("股价高于中期成本")
            elif latest_price < medium_term_cost_approx:
                cost_analysis_results["medium_term_profit_status"] = "亏损"
                bearish_factors.append("股价低于中期成本")
            else:
                cost_analysis_results["medium_term_profit_status"] = "持平"
                neutral_factors.append("股价与中期成本持平")
            detailed_parts.append(f"  中期获利状态: {cost_analysis_results['medium_term_profit_status']}。")
        else:
            neutral_factors.append("中期成本数据缺失")

        return {
            'cost_analysis': cost_analysis_results,
            'detailed_parts': detailed_parts,
            'bullish_factors': bullish_factors,
            'bearish_factors': bearish_factors,
            'neutral_factors': neutral_factors
        }

class AnalysisModuleRegistry:
    """
    Manages the registration and ordering of analysis modules based on priority and dependencies.
    """
    def __init__(self):
        self.modules: List[Tuple[AnalysisModule, int]] = [] # (instance, priority)
        self.loaded_modules: Dict[str, AnalysisModule] = {} # {name: instance}
        self.dependencies: Dict[str, List[str]] = {} # {module_name: [dependency_names]}
        self._load_modules_from_settings()

    def register_module(self, module_instance: AnalysisModule, priority: int = 0, dependencies: Optional[List[str]] = None):
        """Registers an analysis module with its priority and dependencies."""
        module_name = type(module_instance).__name__
        if module_name in self.loaded_modules:
            logger.warning(f"分析模块 '{module_name}' 已注册，跳过重复注册。")
            return
        self.modules.append((module_instance, priority))
        self.loaded_modules[module_name] = module_instance
        self.dependencies[module_name] = dependencies or []
        logger.info(f"注册分析模块: {module_name} (优先级: {priority}, 依赖: {dependencies})")

    def _load_modules_from_settings(self):
        """Loads analysis modules based on configuration settings."""
        logger.info("从配置中加载分析模块...")
        module_configs = settings.get('ANALYSIS_MODULES', {})
        
        # Define a mapping from module name (string) to class
        available_modules = {
            "TechnicalAnalyzer": TechnicalAnalyzer,
            "FundamentalAnalyzer": FundamentalAnalyzer,
            "MarketSentimentAnalyzer": MarketSentimentAnalyzer,
            "IndustryConceptAnalyzer": IndustryConceptAnalyzer,
            "CostAnalyzer": CostAnalyzer,
            # Add other custom modules here if they are in this file
        }

        for module_name, config in module_configs.items():
            if config.get('enabled', False): # Only load if enabled
                module_cls = available_modules.get(module_name)
                if module_cls:
                    try:
                        module_instance = module_cls()
                        self.register_module(
                            module_instance,
                            priority=config.get('priority', 0),
                            dependencies=config.get('dependencies', [])
                        )
                        logger.info(f"加载分析模块: {module_name} (优先级: {config.get('priority', 0)})")
                    except Exception as e:
                        logger.error(f"初始化分析模块 {module_name} 失败: {e}", exc_info=True)
                else:
                    logger.warning(f"配置中指定的分析模块 '{module_name}' 未找到对应的类。")
            else:
                logger.info(f"分析模块 {module_name} 已禁用，跳过加载。")

        # Optional: Load external analysis plugins from a directory
        # This assumes plugins are Python files with an 'analyzer' attribute
        plugin_dir = Path(__file__).parent / "analysis_plugins"
        if plugin_dir.exists() and plugin_dir.is_dir():
            logger.info(f"扫描分析插件目录: {plugin_dir}")
            import importlib.util # Import here to avoid circular dependency if not used
            sys.path.insert(0, str(plugin_dir)) # Add plugin directory to path
            for f in plugin_dir.iterdir():
                if f.suffix == ".py" and f.name != "__init__.py":
                    module_name = f.stem
                    try:
                        # Dynamically import the module
                        spec = importlib.util.spec_from_file_location(module_name, f)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Check if the module exposes an 'analyzer' attribute that is an AnalysisModule
                        if hasattr(module, 'analyzer') and isinstance(module.analyzer, AnalysisModule):
                            # Get config from settings for external plugins too
                            cfg = settings.get(f'analysis_modules.{type(module.analyzer).__name__}', {})
                            if cfg.get('enabled', True):
                                self.register_module(
                                    module.analyzer,
                                    priority=cfg.get('priority', 0),
                                    dependencies=cfg.get('dependencies', [])
                                )
                                logger.info(f"加载分析插件: {module_name} (优先级: {cfg.get('priority', 0)})")
                            else:
                                logger.info(f"分析插件 {module_name} 已禁用，跳过加载。")
                    except Exception as e:
                        logger.error(f"加载分析插件 {module_name} 失败: {e}", exc_info=True)

    def get_ordered_modules(self) -> List[AnalysisModule]:
        """Returns modules ordered by dependencies and then by priority."""
        ordered_modules = []
        visited = set()
        recursion_stack = set()

        def topological_sort(module_name: str):
            if module_name in recursion_stack:
                raise ValueError(f"检测到循环依赖: {module_name} -> {' -> '.join(list(recursion_stack)[list(recursion_stack).index(module_name):])} -> {module_name}")
            if module_name in visited:
                return

            visited.add(module_name)
            recursion_stack.add(module_name)

            # Resolve dependencies first
            for dep_name in self.dependencies.get(module_name, []):
                if dep_name not in self.loaded_modules:
                    raise ValueError(f"模块 '{module_name}' 依赖的模块 '{dep_name}' 未加载。")
                topological_sort(dep_name)
            
            # Add module to ordered list after its dependencies are resolved
            module_instance = self.loaded_modules[module_name]
            if module_instance not in ordered_modules: # Avoid duplicates if a module is a dependency of multiple
                ordered_modules.append(module_instance)
            recursion_stack.remove(module_name)

        # Sort modules by priority first to process higher priority modules earlier
        # This is a heuristic for initial ordering before topological sort ensures dependencies
        sorted_by_priority = sorted(self.modules, key=lambda x: x[1])
        
        # Perform topological sort on all loaded modules
        for module, _ in sorted_by_priority:
            module_name = type(module).__name__
            if module_name not in visited:
                topological_sort(module_name)
        
        return ordered_modules

# Initialize the AnalysisModuleRegistry
analyzer_registry = AnalysisModuleRegistry()

class AnalysisEngine:
    """
    Orchestrates the execution of registered analysis modules.
    Supports context passing between modules.
    """
    def __init__(self):
        self.modules = analyzer_registry.get_ordered_modules()
        self.context: Dict[str, Any] = {} # Context to pass between modules

    async def run_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs all registered analysis modules in their determined order,
        passing context between them.
        """
        # Initialize full_results with default structures for aggregation
        full_results = {
            'detailed_parts': [],
            'bullish_factors': [],
            'bearish_factors': [],
            'neutral_factors': [],
            'cost_analysis': None, # Will be updated by MarketSentimentAnalyzer if available
            'chip_peak_price': None, # Will be updated by MarketSentimentAnalyzer if available
            'chip_peak_ratio': None, # Will be updated by MarketSentimentAnalyzer if available
            'limit_status': "NORMAL",
            'trade_amount_limit_d': None,
            'consecutive_limit_up': None,
            'limit_up_price': None,
            'limit_down_price': None,
            'realtime_change_pct_spot': None,
            'total_net_amount_top_inst': None,
            'hm_list_available': False,
            'hot_money_on_dragon_tiger_list': [], # This will be populated by MarketSentimentAnalyzer
            'main_net_amount_dc': None,
            'retail_net_amount_dc': None,
            'main_net_inflow_ind': None,
            'ths_concepts': [],
            'ths_hot_info': None,
            'technical_summary': {} # Will be updated by TechnicalAnalyzer
        }
        self.context = {} # Reset context for each analysis run

        for module in self.modules:
            module_name = type(module).__name__
            try:
                logger.debug(f"运行分析模块: {module_name}")
                module_results = await asyncio.to_thread(module.analyze, data, self.context) # Run analyze in a thread
                self.context[module_name] = module_results # Store results in context for dependencies

                # Aggregate results from each module
                full_results['detailed_parts'].extend(module_results.pop('detailed_parts', []))
                full_results['bullish_factors'].extend(module_results.pop('bullish_factors', []))
                full_results['bearish_factors'].extend(module_results.pop('bearish_factors', []))
                full_results['neutral_factors'].extend(module_results.pop('neutral_factors', []))
                
                # Update other specific fields, prioritizing later modules if they provide the same key
                full_results.update(module_results) 

            except Exception as e:
                logger.error(f"运行分析模块 {module_name} 失败: {e}", exc_info=True)
                data_completeness_counter.labels(module=module_name, field='analysis_error').inc()
        
        # Ensure all lists are unique
        full_results['bullish_factors'] = list(set(full_results['bullish_factors']))
        full_results['bearish_factors'] = list(set(full_results['bearish_factors']))
        full_results['neutral_factors'] = list(set(full_results['neutral_factors']))
        # Note: detailed_parts can have duplicates if multiple modules add similar phrases,
        # but for readability in the report, we might keep them or deduplicate based on context.
        # For now, let's deduplicate for cleaner output.
        full_results['detailed_parts'] = list(set(full_results['detailed_parts'])) # Order might change

        return full_results

# Initialize the AnalysisEngine
analysis_engine = AnalysisEngine()

# --- 12. Report Generation ---
# Pydantic model for CostAnalysis (defined here for use in AnalysisReportResponse)
class CostAnalysis(BaseModel):
    short_term_cost_approx: Optional[float] = Field(None, description="短期成本近似值 (MA5)")
    medium_term_cost_approx: Optional[float] = Field(None, description="中期成本近似值 (MA20)")
    current_price: Optional[float] = Field(None, description="当前价格")
    short_term_profit_status: Optional[str] = Field(None, description="短期获利状态")
    medium_term_profit_status: Optional[str] = Field(None, description="中期获利状态")

def generate_summary_phrase(full_analysis_results: Dict[str, Any]) -> str:
    """
    Generates a summary phrase based on predefined rules from settings.
    Uses Python's eval for condition evaluation (use with caution, ensure rules are safe).
    """
    rules = settings.get('SUMMARY_RULES', [])
    
    # Prepare context for rule evaluation
    context = {
        'limit_status': full_analysis_results.get('limit_status', 'NORMAL'),
        'total_net_amount_top_inst': full_analysis_results.get('total_net_amount_top_inst'),
        'main_net_amount_dc': full_analysis_results.get('main_net_amount_dc'),
        'latest_price': full_analysis_results.get('technical_summary', {}).get('latest_close'), # Use latest_close from technical summary
        'price_change_pct': full_analysis_results.get('price_change_pct'),
        'MA_short': full_analysis_results.get('technical_summary', {}).get('MA_short'),
        'MA_medium': full_analysis_results.get('technical_summary', {}).get('MA_medium'),
        'MACD_Hist': full_analysis_results.get('technical_summary', {}).get('MACD_Hist'),
        'RSI': full_analysis_results.get('technical_summary', {}).get('RSI'),
        'revenue_yoy': full_analysis_results.get('revenue_yoy'),
        'np_yoy': full_analysis_results.get('np_yoy'),
        'gross_margin': full_analysis_results.get('gross_margin'),
        'roe': full_analysis_results.get('roe'), # Added ROE to context for rules
        'eps': full_analysis_results.get('eps'), # Added EPS to context for rules
        'pb': full_analysis_results.get('pb'),   # Added PB to context for rules
        'pe': full_analysis_results.get('pe'),   # Added PE to context for rules
        'main_net_inflow_ind': full_analysis_results.get('main_net_inflow_ind'),
        'chip_peak_price': full_analysis_results.get('chip_peak_price'),
        'chip_peak_ratio': full_analysis_results.get('chip_peak_ratio'),
        # Add other relevant metrics to context as needed by your rules
    }
    
    # Sort rules by priority (lower number means higher priority)
    sorted_rules = sorted(rules, key=lambda x: x.get('priority', 999))

    for rule in sorted_rules:
        condition_str = rule.get('condition')
        summary_phrase_str = rule.get('summary_phrase')
        if not condition_str or not summary_phrase_str:
            logger.warning(f"Skipping invalid summary rule: {rule}")
            continue
        try:
            # Evaluate the condition string using the prepared context
            # WARNING: Using eval() with untrusted input is a security risk.
            # Ensure your config.yaml is trusted and not user-modifiable.
            if eval(condition_str, {}, context): 
                logger.debug(f"Rule matched: '{condition_str}' -> '{summary_phrase_str}'")
                return summary_phrase_str
        except Exception as e:
            logger.warning(f"Failed to evaluate summary rule: '{condition_str}' - {e}", exc_info=True)
    
    logger.info("No rules matched, returning default summary phrase.")
    return "中性观望" # Default fallback phrase

async def generate_stock_analysis_report(
    symbol: str,
    market_type: str = Query("A", description="Market type: A, HK, US, CRYPTO, ETF, LOF, JP, IN"),
    lang: str = Query("zh", description="Report language: zh (Chinese), en (English)")
) -> Dict[str, Any]:
    """
    Generates a comprehensive stock analysis report.
    This function orchestrates data fetching, analysis, and report rendering.
    """
    api_request_counter.inc()
    start_time = time.time()

    stock_name_map, industry_map = await get_stock_name_map_and_cache(redis_client)
    current_industry = industry_map.get(symbol, "Unknown Industry")

    # Fetch all necessary data concurrently
    # Note: Some global data might be fetched multiple times if not cached and needed by different modules.
    # The DataSourceManager and caching should mitigate this.
    try:
        # Get latest trading date first, as many data fetches depend on it
        latest_trade_date_str = await get_latest_trading_date(redis_client)
        if not latest_trade_date_str:
            raise APIError(status.HTTP_500_INTERNAL_SERVER_ERROR, "无法获取最新交易日，无法生成报告。", "NO_LATEST_TRADE_DATE")

        # Fetch historical data for technical analysis
        stock_data_task = data_source_manager.get_data("fetch_daily", market_type=market_type, symbols=symbol, 
                                                        start_date=(datetime.now() - timedelta(days=app_params.get(market_type, {}).get('data_days', 60))).strftime('%Y%m%d'), 
                                                        end_date=latest_trade_date_str,
                                                        is_fund=True if market_type in ['ETF', 'LOF'] else False)
        
        # Fetch financial data (e.g., last 5 years)
        fina_data_task = data_source_manager.get_data("fetch_fundamentals", market_type=market_type, symbols=[symbol], 
                                                      start_date=(datetime.now() - timedelta(days=365*5)).strftime('%Y%m%d'), 
                                                      end_date=latest_trade_date_str)
        
        # Fetch money flow data
        moneyflow_dc_data_task = data_source_manager.get_data("fetch_moneyflow", market_type=market_type, symbols=[symbol],
                                                              start_date=(datetime.now() - timedelta(days=app_params.get(market_type, {}).get('data_days', 60))).strftime('%Y%m%d'),
                                                              end_date=latest_trade_date_str)
        
        # Fetch global data for market sentiment and industry/concept analysis
        # These are now called via the _get_latest_trading_date_data helpers, which handle caching and fallback
        limit_list_d_data_task = get_limit_list_d_data_and_cache(redis_client)
        stk_limit_data_task = get_stk_limit_data_and_cache(redis_client)
        ak_spot_data_task = data_source_manager.get_data("fetch_spot_data", market_type="A", symbols="global") # Akshare only
        top_inst_data_task = get_top_inst_data_and_cache(redis_client)
        hm_list_data_task = get_hm_list_data_and_cache(redis_client)
        ths_concept_members_data_task = get_ths_concept_members_and_cache(redis_client)
        ths_hot_list_data_task = get_ths_hot_list_and_cache(redis_client)
        moneyflow_ind_ths_data_task = get_moneyflow_ind_ths_data_and_cache(redis_client)
        cyq_chips_data_task = get_cyq_chips_data_and_cache_for_symbol(redis_client, symbol)


        (stock_data, fina_data_dict, moneyflow_dc_data_dict, 
         limit_list_d_data, stk_limit_data, ak_spot_data, 
         top_inst_data, hm_list_data, ths_concept_members_data, 
         ths_hot_list_data, moneyflow_ind_ths_data, cyq_chips_data) = await asyncio.gather(
            stock_data_task, fina_data_task, moneyflow_dc_data_task,
            limit_list_d_data_task, stk_limit_data_task, ak_spot_data_task,
            top_inst_data_task, hm_list_data_task, ths_concept_members_data_task,
            ths_hot_list_data_task, moneyflow_ind_ths_data_task, cyq_chips_data_task
        )
        
        fina_data = fina_data_dict.get(symbol, pd.DataFrame())
        moneyflow_dc_data = moneyflow_dc_data_dict.get(symbol, pd.DataFrame())
        top_inst_data_for_symbol = top_inst_data[top_inst_data['symbol'] == symbol] if not top_inst_data.empty else pd.DataFrame()
        
        latest_price = stock_data['close'].iloc[-1] if not stock_data.empty else None
        price_change_pct = (stock_data['close'].iloc[-1] / stock_data['close'].iloc[-2] - 1) * 100 if len(stock_data) >= 2 else None

        # Prepare initial data for analysis engine
        analysis_input_data = {
            'symbol': symbol,
            'market_type': market_type,
            'stock_data': stock_data,
            'fina_data': fina_data,
            'moneyflow_dc_data': moneyflow_dc_data,
            'limit_list_d_data': limit_list_d_data,
            'stk_limit_data': stk_limit_data,
            'ak_spot_data': ak_spot_data,
            'top_inst_data_for_symbol': top_inst_data_for_symbol,
            'hm_list_data': hm_list_data,
            'hot_money_on_dragon_tiger_list': [], # This will be populated by MarketSentimentAnalyzer
            'ths_concept_members_data': ths_concept_members_data,
            'ths_hot_list_data': ths_hot_list_data,
            'moneyflow_ind_ths_data': moneyflow_ind_ths_data,
            'cyq_chips_data': cyq_chips_data,
            'latest_price': latest_price, # Pass initial latest price for PriceAnalyzer
            'price_change_pct': price_change_pct, # Pass initial price change for PriceAnalyzer
            'current_industry': current_industry
        }

        # Run analysis modules
        full_analysis_results = await analysis_engine.run_analysis(analysis_input_data)

        # Generate summary phrase based on combined analysis results
        summary_phrase = generate_summary_phrase(full_analysis_results)

        # Prepare template data
        template_data = {
            "symbol": symbol,
            "stock_name": stock_name_map.get(symbol, symbol),
            "analysis_date": datetime.now().strftime('%Y-%m-%d'),
            "latest_price": f"{full_analysis_results.get('technical_summary', {}).get('latest_close', 'N/A'):.2f}" if pd.notna(full_analysis_results.get('technical_summary', {}).get('latest_close')) else "N/A",
            "price_change_pct": f"{full_analysis_results.get('price_change_pct', 'N/A'):.2f}%" if pd.notna(full_analysis_results.get('price_change_pct')) else "N/A",
            "detailed_parts": full_analysis_results['detailed_parts'],
            "summary_phrase": summary_phrase,
            "bullish_factors": full_analysis_results['bullish_factors'],
            "bearish_factors": full_analysis_results['bearish_factors'],
            "neutral_factors": full_analysis_results['neutral_factors'],
            "cost_analysis": full_analysis_results.get('cost_analysis'),
            "chip_peak_price": full_analysis_results.get('chip_peak_price'),
            "chip_peak_ratio": full_analysis_results.get('chip_peak_ratio'),
            "technical_summary": full_analysis_results.get('technical_summary', {}) # Pass technical summary
        }

        # Determine template name based on market_type and language
        template_name = template_settings.get('default_template', 'analysis_report_template.html') # Default template
        
        # Prepend language directory if specified and exists
        lang_dir = template_settings.get('languages', {}).get(lang)
        if lang_dir:
            potential_lang_template_name = f"{lang_dir}/{template_name}"
            # Check if the language-specific template exists in the template directory
            template_path = Path(env.loader.searchpath[0]) / potential_lang_template_name
            if template_path.exists():
                template_name = potential_lang_template_name
            else:
                logger.warning(f"Language template path '{template_path}' does not exist, using default template.")
        else:
            logger.warning(f"Language directory for '{lang}' not found in template settings, using default template.")

        template = env.get_template(template_name)
        detailed_analysis_html = template.render(template_data)

        end_time = time.time()
        api_response_time_histogram.observe(end_time - start_time)
        logger.info(f"Stock analysis report generation completed, time taken: {end_time - start_time:.2f} seconds.")

        return {
            "summary_phrase": summary_phrase,
            "detailed_analysis": detailed_analysis_html,
            "bullish_factors": full_analysis_results['bullish_factors'],
            "bearish_factors": full_analysis_results['bearish_factors'],
            "neutral_factors": full_analysis_results['neutral_factors'],
            "cost_analysis": full_analysis_results.get('cost_analysis'),
            "chip_peak_price": full_analysis_results.get('chip_peak_price'),
            "chip_peak_ratio": full_analysis_results.get('chip_peak_ratio')
        }

    except APIError as e:
        logger.error(f"API Error in generate_stock_analysis_report: {e.detail}", exc_info=True)
        raise e
    except Exception as e:
        logger.critical(f"An unexpected error occurred in generate_stock_analysis_report: {e}", exc_info=True)
        raise APIError(status.HTTP_500_INTERNAL_SERVER_ERROR, f"An unexpected error occurred during report generation: {e}", "REPORT_GENERATION_ERROR")


# --- 13. FastAPI Application Setup ---
app = FastAPI(
    title="Stock Analysis API",
    description="Provides comprehensive analysis reports for stocks, including technical, fundamental, capital flow, and market sentiment.",
    version=_VERSION_IDENTIFIER_
)

# API Response Models
class AnalysisReportResponse(BaseModel):
    summary_phrase: str = Field(..., description="Brief summary phrase")
    detailed_analysis: str = Field(..., description="Detailed analysis report (HTML format)")
    bullish_factors: List[str] = Field(..., description="List of bullish factors")
    bearish_factors: List[str] = Field(..., description="List of bearish factors")
    neutral_factors: List[str] = Field(..., description="List of neutral factors")
    cost_analysis: Optional[CostAnalysis] = Field(None, description="Cost analysis data (e.g., cost moving averages)")
    chip_peak_price: Optional[float] = Field(None, description="Chip peak price")
    chip_peak_ratio: Optional[float] = Field(None, description="Chip peak ratio")

# --- API Endpoints ---
@app.get("/analyze/{symbol}", response_model=AnalysisReportResponse, summary="Get comprehensive stock analysis report")
async def get_stock_analysis(
    symbol: str = Field(..., description="Stock code, e.g., '000001'"),
    market_type: str = Query("A", description="Market type: A (A-shares), HK (Hong Kong stocks), US (US stocks), CRYPTO (Cryptocurrency), ETF, LOF, JP (Japanese stocks), IN (Indian stocks)"),
    x_auth_token: Optional[str] = Header(None, description="API Authorization Token"),
    lang: str = Query("zh", description="Report language: zh (Chinese), en (English)")
):
    """
    Generates a comprehensive analysis report including technical, fundamental, capital flow, and market sentiment
    based on the stock code and market type.
    """
    if settings.VALID_AUTH_TOKENS:
        valid_tokens = [t.strip() for t in settings.VALID_AUTH_TOKENS.split(',')]
        if x_auth_token not in valid_tokens:
            raise APIError(status.HTTP_401_UNAUTHORIZED, "Invalid Authorization Token", "INVALID_AUTH_TOKEN")
    
    logger.info(f"Received analysis request: Symbol={symbol}, Market Type={market_type}, Language={lang}")
    
    # Validate market_type
    if market_type not in app_params.keys():
        raise APIError(status.HTTP_400_BAD_REQUEST, f"Unsupported market type: {market_type}", "UNSUPPORTED_MARKET_TYPE")

    # Validate language
    if lang not in template_settings.get('languages', {}).keys():
        raise APIError(status.HTTP_400_BAD_REQUEST, f"Unsupported language: {lang}", "UNSUPPORTED_LANGUAGE")

    try:
        report = await generate_stock_analysis_report(symbol, market_type, lang)
        return report
    except APIError as e:
        logger.error(f"API Error: {e.detail}", exc_info=True)
        raise e
    except Exception as e:
        logger.critical(f"An unexpected error occurred while processing the request: {e}", exc_info=True)
        raise APIError(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Internal Server Error: {e}", "INTERNAL_SERVER_ERROR")

@app.get("/metrics", summary="Prometheus monitoring metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    """
    return Response(generate_latest(), media_type="text/plain")

@app.get("/health", summary="Health check endpoint")
async def health_check():
    """
    Health check endpoint to verify Redis connection.
    """
    try:
        redis_client.ping()
        return {"status": "healthy", "redis_connected": True}
    except Exception as e:
        logger.error(f"Health check failed: Redis connection error: {e}", exc_info=True)
        raise APIError(status.HTTP_503_SERVICE_UNAVAILABLE, "Redis connection failed", "REDIS_UNAVAILABLE")

@app.on_event("startup")
async def startup_event():
    """
    FastAPI startup event: preheat caches for global data.
    """
    logger.info("FastAPI startup event: Starting cache preheating...")
    
    # Pre-fetch global data that is frequently accessed and relatively static
    try:
        # Pre-fetch stock name map and industry map
        await get_stock_name_map_and_cache(redis_client)
        
        # Pre-fetch latest trading date
        await get_latest_trading_date(redis_client)

        # Pre-fetch other global data for the latest trading date
        await get_moneyflow_ind_ths_data_and_cache(redis_client)
        await get_stk_factor_pro_data_and_cache(redis_client)
        await get_limit_list_d_data_and_cache(redis_client)
        await get_stk_limit_data_and_cache(redis_client)
        await get_top_inst_data_and_cache(redis_client)
        await get_hm_list_data_and_cache(redis_client)
        await get_ths_concept_members_and_cache(redis_client)
        await get_ths_hot_list_and_cache(redis_client)

        logger.info("FastAPI startup event: Cache preheating completed.")
    except Exception as e:
        logger.error(f"FastAPI startup event: Cache preheating failed: {e}", exc_info=True)

@app.on_event("shutdown")
async def shutdown_event():
    """
    FastAPI shutdown event: close aiohttp session.
    """
    logger.info("FastAPI shutdown event: Closing aiohttp session...")
    if hasattr(TushareDataSource, 'session') and TushareDataSource.session is not None and not TushareDataSource.session.closed:
        await TushareDataSource.session.close()
        logger.info("aiohttp session closed.")

if __name__ == "__main__":
    import uvicorn
    # Create a dummy templates directory and file for local testing if they don't exist
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    zh_templates_dir = templates_dir / "zh"
    zh_templates_dir.mkdir(exist_ok=True)

    en_templates_dir = templates_dir / "en"
    en_templates_dir.mkdir(exist_ok=True)

    default_template_path = zh_templates_dir / "analysis_report_template.html"
    if not default_template_path.exists():
        with open(default_template_path, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ stock_name }} ({{ symbol }}) 股票分析报告 - {{ analysis_date }}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f4f7f6; color: #333; line-height: 1.6; }
        .container { max-width: 900px; margin: auto; background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 25px; border-bottom: 2px solid #e0e0e0; padding-bottom: 15px; }
        h2 { color: #34495e; border-left: 5px solid #3498db; padding-left: 10px; margin-top: 30px; margin-bottom: 15px; }
        p { margin-bottom: 10px; }
        .summary { background-color: #e8f5e9; border-left: 6px solid #4CAF50; padding: 15px 20px; border-radius: 8px; margin-bottom: 25px; font-size: 1.1em; font-weight: bold; color: #2e7d32; }
        .factors-section { display: flex; justify-content: space-between; margin-top: 20px; flex-wrap: wrap; }
        .factor-list { background-color: #f8f8f8; padding: 15px; border-radius: 8px; flex: 1; min-width: 280px; margin: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .factor-list h3 { margin-top: 0; color: #555; border-bottom: 1px dashed #ddd; padding-bottom: 8px; margin-bottom: 10px; }
        .factor-list ul { list-style-type: none; padding: 0; }
        .factor-list li { margin-bottom: 5px; padding-left: 20px; position: relative; }
        .bullish li:before { content: '↑'; color: #4CAF50; position: absolute; left: 0; }
        .bearish li:before { content: '↓'; color: #f44336; position: absolute; left: 0; }
        .neutral li:before { content: '—'; color: #ff9800; position: absolute; left: 0; }
        .detailed-analysis { background-color: #fdfdfd; border: 1px solid #eee; padding: 20px; border-radius: 8px; margin-top: 25px; }
        .detailed-analysis p { white-space: pre-wrap; word-wrap: break-word; }
        .footer { text-align: center; margin-top: 40px; font-size: 0.85em; color: #777; }
        .disclaimer { font-size: 0.8em; color: #999; margin-top: 30px; padding: 15px; background-color: #f0f0f0; border-left: 4px solid #ccc; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ stock_name }} ({{ symbol }}) 股票分析报告</h1>
        <p><strong>分析日期:</strong> {{ analysis_date }}</p>
        <p><strong>最新价:</strong> {{ latest_price }} 元</p>
        <p><strong>日涨跌幅:</strong> {{ price_change_pct }}</p>

        <div class="summary">
            <p><strong>总结:</strong> {{ summary_phrase }}</p>
        </div>

        <h2>详细分析</h2>
        <div class="detailed-analysis">
            {% for part in detailed_parts %}
                <p>{{ part }}</p>
            {% endfor %}
        </div>

        <div class="factors-section">
            <div class="factor-list bullish">
                <h3>看涨因素</h3>
                <ul>
                    {% for factor in bullish_factors %}
                        <li>{{ factor }}</li>
                    {% endfor %}
                    {% if not bullish_factors %}
                        <li>暂无明显看涨因素。</li>
                    {% endif %}
                </ul>
            </div>
            <div class="factor-list bearish">
                <h3>看跌因素</h3>
                <ul>
                    {% for factor in bearish_factors %}
                        <li>{{ factor }}</li>
                    {% endfor %}
                    {% if not bearish_factors %}
                        <li>暂无明显看跌因素。</li>
                    {% endif %}
                </ul>
            </div>
            <div class="factor-list neutral">
                <h3>中性因素</h3>
                <ul>
                    {% for factor in neutral_factors %}
                        <li>{{ factor }}</li>
                    {% endfor %}
                    {% if not neutral_factors %}
                        <li>暂无明显中性因素。</li>
                    {% endif %}
                </ul>
            </div>
        </div>

        {% if cost_analysis or chip_peak_price %}
        <h2>补充分析</h2>
        <div class="detailed-analysis">
            {% if cost_analysis %}
            <h3>成本分析</h3>
            <p>平均成本：{{ cost_analysis.short_term_cost_approx|default('N/A', true) }} (短期)</p>
            <p>平均成本：{{ cost_analysis.medium_term_cost_approx|default('N/A', true) }} (中期)</p>
            <p>当前价格：{{ cost_analysis.current_price|default('N/A', true) }}</p>
            <p>短期获利状态：{{ cost_analysis.short_term_profit_status|default('N/A', true) }}</p>
            <p>中期获利状态：{{ cost_analysis.medium_term_profit_status|default('N/A', true) }}</p>
            {% endif %}

            {% if chip_peak_price %}
            <h3>筹码分布</h3>
            <p>主要筹码峰价格：{{ chip_peak_price|default('N/A', true) }}</p>
            <p>主要筹码峰占比：{{ chip_peak_ratio|default('N/A', true) }}%</p>
            {% endif %}
        </div>
        {% endif %}

        <div class="disclaimer">
            <p><strong>免责声明:</strong> 本报告仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。所有数据来源于第三方数据源，本报告不保证其准确性和完整性。</p>
        </div>
        <div class="footer">
            <p>&copy; {{ analysis_date.split('-')[0] }} 股票分析API. All rights reserved.</p>
        </div>
    </div>
</body>
</html>""")
        logger.info(f"Created default Chinese template file: {default_template_path}")

    default_en_template_path = en_templates_dir / "analysis_report_template.html"
    if not default_en_template_path.exists():
        with open(default_en_template_path, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ stock_name }} ({{ symbol }}) Stock Analysis Report - {{ analysis_date }}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f4f7f6; color: #333; line-height: 1.6; }
        .container { max-width: 900px; margin: auto; background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 25px; border-bottom: 2px solid #e0e0e0; padding-bottom: 15px; }
        h2 { color: #34495e; border-left: 5px solid #3498db; padding-left: 10px; margin-top: 30px; margin-bottom: 15px; }
        p { margin-bottom: 10px; }
        .summary { background-color: #e8f5e9; border-left: 6px solid #4CAF50; padding: 15px 20px; border-radius: 8px; margin-bottom: 25px; font-size: 1.1em; font-weight: bold; color: #2e7d32; }
        .factors-section { display: flex; justify-content: space-between; margin-top: 20px; flex-wrap: wrap; }
        .factor-list { background-color: #f8f8f8; padding: 15px; border-radius: 8px; flex: 1; min-width: 280px; margin: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .factor-list h3 { margin-top: 0; color: #555; border-bottom: 1px dashed #ddd; padding-bottom: 8px; margin-bottom: 10px; }
        .factor-list ul { list-style-type: none; padding: 0; }
        .factor-list li { margin-bottom: 5px; padding-left: 20px; position: relative; }
        .bullish li:before { content: '↑'; color: #4CAF50; position: absolute; left: 0; }
        .bearish li:before { content: '↓'; color: #f44336; position: absolute; left: 0; }
        .neutral li:before { content: '—'; color: #ff9800; position: absolute; left: 0; }
        .detailed-analysis { background-color: #fdfdfd; border: 1px solid #eee; padding: 20px; border-radius: 8px; margin-top: 25px; }
        .detailed-analysis p { white-space: pre-wrap; word-wrap: break-word; }
        .footer { text-align: center; margin-top: 40px; font-size: 0.85em; color: #777; }
        .disclaimer { font-size: 0.8em; color: #999; margin-top: 30px; padding: 15px; background-color: #f0f0f0; border-left: 4px solid #ccc; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ stock_name }} ({{ symbol }}) Stock Analysis Report</h1>
        <p><strong>Analysis Date:</strong> {{ analysis_date }}</p>
        <p><strong>Latest Price:</strong> {{ latest_price }} CNY</p>
        <p><strong>Daily Change:</strong> {{ price_change_pct }}</p>

        <div class="summary">
            <p><strong>Summary:</strong> {{ summary_phrase }}</p>
        </div>

        <h2>Detailed Analysis</h2>
        <div class="detailed-analysis">
            {% for part in detailed_parts %}
                <p>{{ part }}</p>
            {% endfor %}
        </div>

        <div class="factors-section">
            <div class="factor-list bullish">
                <h3>Bullish Factors</h3>
                <ul>
                    {% for factor in bullish_factors %}
                        <li>{{ factor }}</li>
                    {% endfor %}
                    {% if not bullish_factors %}
                        <li>No significant bullish factors.</li>
                    {% endif %}
                </ul>
            </div>
            <div class="factor-list bearish">
                <h3>Bearish Factors</h3>
                <ul>
                    {% for factor in bearish_factors %}
                        <li>{{ factor }}</li>
                    {% endfor %}
                    {% if not bearish_factors %}
                        <li>No significant bearish factors.</li>
                    {% endif %}
                </ul>
            </div>
            <div class="factor-list neutral">
                <h3>Neutral Factors</h3>
                <ul>
                    {% for factor in neutral_factors %}
                        <li>{{ factor }}</li>
                    {% endfor %}
                    {% if not neutral_factors %}
                        <li>No significant neutral factors.</li>
                    {% endif %}
                </ul>
            </div>
        </div>

        {% if cost_analysis or chip_peak_price %}
        <h2>Additional Analysis</h2>
        <div class="detailed-analysis">
            {% if cost_analysis %}
            <h3>Cost Analysis</h3>
            <p>Average Cost Price (Short-term/MA5): {{ cost_analysis.short_term_cost_approx|default('N/A', true) }}</p>
            <p>Average Cost Price (Medium-term/MA20): {{ cost_analysis.medium_term_cost_approx|default('N/A', true) }}</p>
            <p>Current Price: {{ cost_analysis.current_price|default('N/A', true) }}</p>
            <p>Short-term Profit Status: {{ cost_analysis.short_term_profit_status|default('N/A', true) }}</p>
            <p>Medium-term Profit Status: {{ cost_analysis.medium_term_profit_status|default('N/A', true) }}</p>
            {% endif %}

            {% if chip_peak_price %}
            <h3>Chip Distribution</h3>
            <p>Main Chip Peak Price: {{ chip_peak_price|default('N/A', true) }}</p>
            <p>Main Chip Peak Ratio: {{ chip_peak_ratio|default('N/A', true) }}%</p>
            {% endif %}
        </div>
        {% endif %}

        <div class="disclaimer">
            <p><strong>Disclaimer:</strong> This report is for reference only and does not constitute investment advice. Investing involves risks, and caution is advised. All data is sourced from third-party data providers, and this report does not guarantee its accuracy or completeness.</p>
        </div>
        <div class="footer">
            <p>&copy; {{ analysis_date.split('-')[0] }} Stock Analysis API. All rights reserved.</p>
        </div>
    </div>
</body>
</html>""")
        logger.info(f"Created default English template file: {default_en_template_path}")

    uvicorn.run(app, host="0.0.0.0", port=8000)

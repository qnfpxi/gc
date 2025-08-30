import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

from dynaconf import Dynaconf, settings # For configuration management

# Add the parent directory to the Python path to import stock_analysis_api
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

# Import necessary components from the main API file
# We need specific functions and classes, not the entire app
from stock_analysis_api import (
    redis_client,
    data_source_manager,
    get_stock_name_map_and_cache,
    get_latest_trading_date,
    get_moneyflow_ind_ths_data_and_cache,
    get_stk_factor_pro_data_and_cache,
    get_limit_list_d_data_and_cache,
    get_stk_limit_data_and_cache,
    get_top_inst_data_and_cache,
    get_hm_list_data_and_cache,
    get_ths_concept_members_and_cache,
    get_ths_hot_list_and_cache,
    TushareDataSource, # To close aiohttp session if needed
    setup_logging, # To configure logging consistently
    app_params # To get market configurations
)

# Setup logging for this script
setup_logging()
logger = logging.getLogger(__name__)

async def preheat_cache():
    """
    Preheats the Redis cache with global and frequently accessed stock data.
    This helps reduce latency for initial API requests.
    """
    logger.info("Starting cache preheating...")
    
    try:
        # 1. Pre-fetch stock name map and industry map
        logger.info("Preheating: Fetching stock name and industry map...")
        stock_name_map, _ = await get_stock_name_map_and_cache(redis_client)
        logger.info(f"Preheating: Cached {len(stock_name_map)} stock names and industry maps.")
        
        # 2. Pre-fetch latest trading date
        logger.info("Preheating: Fetching latest trading date...")
        latest_trade_date = await get_latest_trading_date(redis_client)
        logger.info(f"Preheating: Latest trading date: {latest_trade_date}")

        # 3. Pre-fetch other global data for the latest trading date
        logger.info("Preheating: Fetching money flow - industry sector data (Eastmoney)...")
        await get_moneyflow_ind_ths_data_and_cache(redis_client)
        logger.info("Preheating: Money flow - industry sector data cached.")

        logger.info("Preheating: Fetching stock basic factor data...")
        await get_stk_factor_pro_data_and_cache(redis_client)
        logger.info("Preheating: Stock basic factor data cached.")

        logger.info("Preheating: Fetching daily limit-up/down statistics data...")
        await get_limit_list_d_data_and_cache(redis_client)
        logger.info("Preheating: Daily limit-up/down statistics data cached.")

        logger.info("Preheating: Fetching stock limit-up/down price data...")
        await get_stk_limit_data_and_cache(redis_client)
        logger.info("Preheating: Stock limit-up/down price data cached.")
        
        logger.info("Preheating: Fetching institutional Dragon-Tiger list data...")
        await get_top_inst_data_and_cache(redis_client)
        logger.info("Preheating: Institutional Dragon-Tiger list data cached.")

        logger.info("Preheating: Fetching hot money list data...")
        await get_hm_list_data_and_cache(redis_client)
        logger.info("Preheating: Hot money list data cached.")

        logger.info("Preheating: Fetching Tonghuashun concept constituent stock data...")
        await get_ths_concept_members_and_cache(redis_client)
        logger.info("Preheating: Tonghuashun concept constituent stock data cached.")
        
        logger.info("Preheating: Fetching Tonghuashun hot list data...")
        await get_ths_hot_list_and_cache(redis_client)
        logger.info("Preheating: Tonghuashun hot list data cached.")

        # 4. Optional: Pre-fetch some top N hot/active stocks' daily and financial data
        # This part can be resource-intensive, enable with caution and monitor Tushare quotas
        if settings.get('PREHEAT_TOP_N_STOCKS', 0) > 0:
            top_n = settings.PREHEAT_TOP_N_STOCKS
            logger.info(f"Starting preheating of daily and financial data for top {top_n} hot stocks...")
            
            # This is a placeholder. You'd need a way to get "top N hot stocks".
            # For A-shares, perhaps from a list of major indices or a static list.
            # For simplicity, let's just pick first N from stock_name_map.
            a_share_symbols = [s for s in stock_name_map.keys() if s.startswith(('00', '30', '60', '68'))][:top_n]

            tasks = []
            today_str = datetime.now().strftime('%Y%m%d')
            data_days_for_preheat = app_params.get('A', {}).get('data_days', 60) # Use default for A-shares

            for symbol in a_share_symbols:
                # Fetch daily data
                tasks.append(
                    data_source_manager.get_data(
                        "fetch_daily",
                        market_type="A", # Assuming A-shares for preheat
                        symbols=symbol,
                        start_date=(datetime.now() - timedelta(days=data_days_for_preheat)).strftime('%Y%m%d'),
                        end_date=today_str,
                        is_fund=False # Assuming these are common stocks for preheat
                    )
                )
                # Fetch financial data (e.g., last 2 years)
                tasks.append(
                    data_source_manager.get_data(
                        "fetch_fundamentals",
                        market_type="A", # Assuming A-shares for preheat
                        symbols=[symbol],
                        start_date=(datetime.now() - timedelta(days=365*2)).strftime('%Y%m%d'),
                        end_date=today_str
                    )
                )
                # Fetch moneyflow data
                tasks.append(
                    data_source_manager.get_data(
                        "fetch_moneyflow",
                        market_type="A", # Assuming A-shares for preheat
                        symbols=[symbol],
                        start_date=(datetime.now() - timedelta(days=data_days_for_preheat)).strftime('%Y%m%d'),
                        end_date=today_str
                    )
                )
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = 0
            for res in results:
                if isinstance(res, Exception):
                    logger.error(f"Failed to preheat single stock data: {res}")
                else:
                    success_count += 1
            logger.info(f"Preheating of top {top_n} stock data completed. Successfully fetched {success_count} data batches.")

        logger.info("All cache preheating tasks completed.")

    except Exception as e:
        logger.critical(f"A critical error occurred during cache preheating: {e}", exc_info=True)
    finally:
        # Ensure aiohttp session is closed if it was opened
        if hasattr(TushareDataSource, 'session') and TushareDataSource.session is not None and not TushareDataSource.session.closed:
            await TushareDataSource.session.close()
            logger.info("aiohttp session closed (preheat_cache.py).")

if __name__ == "__main__":
    # Ensure settings are loaded
    settings.configure(SETTINGS_FILES=[
        'config.yaml', '.env' # Load from config.yaml and .env files
    ], environments=True, load_dotenv=True)
    
    logger.info("preheat_cache.py script started.")
    asyncio.run(preheat_cache())
    logger.info("preheat_cache.py script finished execution.")

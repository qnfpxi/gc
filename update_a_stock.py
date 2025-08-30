import asyncio
import logging
import os
import sys
from datetime import datetime

from dynaconf import Dynaconf, settings

# Add the parent directory to the Python path to import stock_analysis_api
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

from stock_analysis_api import (
    redis_client,
    get_stock_name_map_and_cache,
    get_latest_trading_date,
    get_moneyflow_ind_ths_data_and_cache, # Added for periodic update
    get_stk_factor_pro_data_and_cache,    # Added for periodic update
    get_limit_list_d_data_and_cache,      # Added for periodic update
    get_stk_limit_data_and_cache,         # Added for periodic update
    get_top_inst_data_and_cache,          # Added for periodic update
    get_hm_list_data_and_cache,           # Added for periodic update
    get_ths_concept_members_and_cache,    # Added for periodic update
    get_ths_hot_list_and_cache,           # Added for periodic update
    TushareDataSource, # To close aiohttp session if needed
    setup_logging # To configure logging consistently
)

# Setup logging for this script
setup_logging()
logger = logging.getLogger(__name__)

async def update_a_stock_data():
    """
    Performs specific updates for A-share related global data,
    such as the latest stock list or industry data.
    This can be scheduled as a daily or weekly cron job.
    """
    logger.info("Starting update of A-share related global data...")

    try:
        # Update stock name map and industry map (this refreshes daily from Tushare)
        logger.info("Updating: Fetching latest stock name and industry map...")
        stock_name_map, _ = await get_stock_name_map_and_cache(redis_client)
        logger.info(f"Updating: Cached {len(stock_name_map)} latest stock names and industry maps.")
        
        # Update latest trading date (important for other data fetches)
        logger.info("Updating: Fetching latest trading date...")
        latest_trade_date = await get_latest_trading_date(redis_client)
        logger.info(f"Updating: Latest trading date: {latest_trade_date}")

        # Update other global data for the latest trading date
        logger.info("Updating: Fetching money flow - industry sector data (Eastmoney)...")
        await get_moneyflow_ind_ths_data_and_cache(redis_client)
        logger.info("Updating: Money flow - industry sector data cached.")

        logger.info("Updating: Fetching stock basic factor data...")
        await get_stk_factor_pro_data_and_cache(redis_client)
        logger.info("Updating: Stock basic factor data cached.")

        logger.info("Updating: Fetching daily limit-up/down statistics data...")
        await get_limit_list_d_data_and_cache(redis_client)
        logger.info("Updating: Daily limit-up/down statistics data cached.")

        logger.info("Updating: Fetching stock limit-up/down price data...")
        await get_stk_limit_data_and_cache(redis_client)
        logger.info("Updating: Stock limit-up/down price data cached.")
        
        logger.info("Updating: Fetching institutional Dragon-Tiger list data...")
        await get_top_inst_data_and_cache(redis_client)
        logger.info("Updating: Institutional Dragon-Tiger list data cached.")

        logger.info("Updating: Fetching hot money list data...")
        await get_hm_list_data_and_cache(redis_client)
        logger.info("Updating: Hot money list data cached.")

        logger.info("Updating: Fetching Tonghuashun concept constituent stock data...")
        await get_ths_concept_members_and_cache(redis_client)
        logger.info("Updating: Tonghuashun concept constituent stock data cached.")
        
        logger.info("Updating: Fetching Tonghuashun hot list data...")
        await get_ths_hot_list_and_cache(redis_client)
        logger.info("Updating: Tonghuashun hot list data cached.")

        logger.info("A-share related global data update completed.")

    except Exception as e:
        logger.critical(f"A critical error occurred during A-share global data update: {e}", exc_info=True)
    finally:
        # Ensure aiohttp session is closed if it was opened
        if hasattr(TushareDataSource, 'session') and TushareDataSource.session is not None and not TushareDataSource.session.closed:
            await TushareDataSource.session.close()
            logger.info("aiohttp session closed (update_a_stock.py).")

if __name__ == "__main__":
    # Ensure settings are loaded
    settings.configure(SETTINGS_FILES=[
        'config.yaml', '.env' # Load from config.yaml and .env files
    ], environments=True, load_dotenv=True)
    
    logger.info("update_a_stock.py script started.")
    asyncio.run(update_a_stock_data())
    logger.info("update_a_stock.py script finished execution.")

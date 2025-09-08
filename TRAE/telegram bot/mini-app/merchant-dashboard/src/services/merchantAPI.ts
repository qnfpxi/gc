import axios, { AxiosInstance, AxiosResponse } from 'axios';

// API响应接口
interface ApiResponse<T> {
  status: string;
  data?: T;
  message?: string;
}

// 商家基础信息接口
interface MerchantInfo {
  merchant_id: number;
  name: string;
  description?: string;
  region_id: number;
  address?: string;
  contact_phone?: string;
  contact_wechat?: string;
  contact_telegram?: string;
  subscription_tier: string;
  created_at: string;
  rating_avg?: number;
  rating_count: number;
  view_count: number;
}

// 商家更新请求接口
interface MerchantUpdateRequest {
  name: string;
  description?: string;
  region_id: number;
  address?: string;
  contact_phone?: string;
  contact_wechat?: string;
  contact_telegram?: string;
}

// 商家统计数据接口
interface MerchantStats {
  merchant_id: number;
  products_count: number;
  active_products_count: number;
  total_views: number;
  total_favorites: number;
  rating_avg: number;
  rating_count: number;
  subscription_status: string;
  subscription_tier: string;
  is_premium: boolean;
}

class MerchantAPIService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor() {
    // 从环境变量或配置中获取API基础URL
    this.baseURL = import.meta.env.VITE_API_BASE_URL || 'https://your-api-domain.com/api/v1';
    
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 设置请求拦截器，自动添加认证token
    this.api.interceptors.request.use(
      (config) => {
        const token = this.getTelegramToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 设置响应拦截器，统一处理错误
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        // API请求错误处理
        
        if (error.response?.status === 401) {
          // 认证失败，可能需要重新获取token
          // 认证失败处理
        }
        
        return Promise.reject(error);
      }
    );
  }

  /**
   * 获取Telegram WebApp的认证token
   */
  private getTelegramToken(): string | null {
    try {
      // 从Telegram WebApp获取initData
      const tg = (window as any).Telegram?.WebApp;
      if (tg && tg.initData) {
        return tg.initData;
      }
      
      // 开发环境fallback（仅用于测试）
      if (import.meta.env.DEV) {
        return 'dev-test-token';
      }
      
      return null;
    } catch (error) {
      // 获取Telegram token失败处理
      return null;
    }
  }

  /**
   * 获取当前商家信息
   */
  async getCurrentMerchant(): Promise<MerchantInfo> {
    try {
      const response: AxiosResponse<ApiResponse<MerchantInfo>> = await this.api.get('/merchants/me');
      
      if (response.data.status === 'success' && response.data.data) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '获取商家信息失败');
      }
    } catch (error: any) {
      // 获取商家信息失败处理
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 更新商家信息
   */
  async updateMerchant(merchantId: number, updateData: MerchantUpdateRequest): Promise<MerchantInfo> {
    try {
      const response: AxiosResponse<ApiResponse<MerchantInfo>> = await this.api.put(
        `/merchants/${merchantId}`,
        updateData
      );
      
      if (response.data.status === 'success' && response.data.data) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '更新商家信息失败');
      }
    } catch (error: any) {
      // 更新商家信息失败处理
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 获取商家统计数据
   */
  async getMerchantStats(merchantId: number): Promise<MerchantStats> {
    try {
      const response: AxiosResponse<ApiResponse<MerchantStats>> = await this.api.get(
        `/merchants/${merchantId}/stats`
      );
      
      if (response.data.status === 'success' && response.data.data) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '获取统计数据失败');
      }
    } catch (error: any) {
      // 获取统计数据失败处理
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 获取指定商家详情
   */
  async getMerchantById(merchantId: number): Promise<MerchantInfo> {
    try {
      const response: AxiosResponse<ApiResponse<MerchantInfo>> = await this.api.get(
        `/merchants/${merchantId}`
      );
      
      if (response.data.status === 'success' && response.data.data) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '获取商家详情失败');
      }
    } catch (error: any) {
      // 获取商家详情失败处理
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 测试API连接
   */
  async testConnection(): Promise<boolean> {
    try {
      // 尝试获取当前商家信息来测试连接
      await this.getCurrentMerchant();
      return true;
    } catch (error) {
      // API连接测试失败处理
      return false;
    }
  }
}

// 创建单例实例
export const merchantAPI = new MerchantAPIService();

// 导出接口类型
export type { 
  MerchantInfo, 
  MerchantUpdateRequest, 
  MerchantStats,
  ApiResponse 
};
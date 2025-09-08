import axios, { AxiosInstance, AxiosResponse } from 'axios';

// API响应接口
interface ApiResponse<T> {
  status: string;
  data?: T;
  message?: string;
}

// 商家列表项接口
export interface MerchantListItem {
  id: number;
  name: string;
  description?: string;
  logo_url?: string;
  address?: string;
  rating_avg: number;
  rating_count: number;
  view_count: number;
  subscription_tier: string;
  is_featured?: boolean;
  created_at: string;
}

// 商品列表项接口
export interface ProductListItem {
  id: number;
  merchant_id: number;
  name: string;
  description?: string;
  price?: number;
  currency: string;
  main_image_url?: string;
  view_count: number;
  favorite_count: number;
  is_new?: boolean;
  created_at: string;
}

// 商家详情接口
export interface MerchantDetail extends MerchantListItem {
  contact_phone?: string;
  contact_telegram?: string;
  contact_wechat?: string;
  is_verified?: boolean;
}

// 商品详情接口
export interface ProductDetail {
  id: number;
  merchant_id: number;
  name: string;
  description?: string;
  price?: number;
  price_unit: string;
  is_price_negotiable: boolean;
  currency: string;
  image_urls: string[];
  tags: string[];
  status: string;
  view_count: number;
  favorite_count: number;
  sales_count: number;
  created_at: string;
  updated_at: string;
}

// 统一搜索结果接口
export interface UnifiedSearchResult {
  merchants: MerchantListItem[];
  products: ProductListItem[];
  total_merchants: number;
  total_products: number;
}

// 收藏商品请求接口
interface FavoriteProductRequest {
  product_id: number;
}

class APIService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor() {
    // 从环境变量或配置中获取API基础URL
    this.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
    
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
        const token = this.getAuthToken();
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
        console.error('API请求错误:', error);
        
        if (error.response?.status === 401) {
          // 认证失败，可能需要重新获取token
          console.warn('认证失败，请重新登录');
        }
        
        return Promise.reject(error);
      }
    );
  }

  /**
   * 获取认证token
   */
  private getAuthToken(): string | null {
    try {
      // 从Telegram WebApp获取initData
      const tg = (window as any).Telegram?.WebApp;
      if (tg && tg.initData) {
        return tg.initData;
      }
      
      // 开发环境fallback（仅用于测试）
      if (import.meta.env.DEV) {
        return localStorage.getItem('auth_token') || 'dev-test-token';
      }
      
      return null;
    } catch (error) {
      console.error('获取认证token失败:', error);
      return null;
    }
  }

  /**
   * 全局搜索商家和商品
   */
  async searchAll(query: string, limit: number = 10): Promise<UnifiedSearchResult> {
    try {
      const response: AxiosResponse<ApiResponse<UnifiedSearchResult>> = await this.api.get(
        '/search/',
        { params: { q: query, limit } }
      );
      
      if (response.data.status === 'success' && response.data.data) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '搜索失败');
      }
    } catch (error: any) {
      console.error('搜索失败:', error);
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 获取商家列表
   */
  async getMerchants(params?: {
    region_id?: number;
    keyword?: string;
    latitude?: number;
    longitude?: number;
    radius_km?: number;
    subscription_tier?: string;
    is_featured?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<MerchantListItem[]> {
    try {
      const response: AxiosResponse<ApiResponse<MerchantListItem[]>> = await this.api.get(
        '/merchants/',
        { params }
      );
      
      if (response.data.status === 'success' && response.data.data) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '获取商家列表失败');
      }
    } catch (error: any) {
      console.error('获取商家列表失败:', error);
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 获取商家详情
   */
  async getMerchantById(merchantId: number): Promise<MerchantDetail> {
    try {
      const response: AxiosResponse<ApiResponse<MerchantDetail>> = await this.api.get(
        `/merchants/${merchantId}`
      );
      
      if (response.data.status === 'success' && response.data.data) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '获取商家详情失败');
      }
    } catch (error: any) {
      console.error('获取商家详情失败:', error);
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 获取商品列表
   */
  async getProducts(params?: {
    q?: string;
    category_id?: number;
    merchant_id?: number;
    status?: string;
    min_price?: number;
    max_price?: number;
    tags?: string[];
    sort_by?: string;
    sort_order?: string;
    limit?: number;
    offset?: number;
  }): Promise<ProductListItem[]> {
    try {
      const response: AxiosResponse<ApiResponse<ProductListItem[]>> = await this.api.get(
        '/products/',
        { params }
      );
      
      if (response.data.status === 'success' && response.data.data) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '获取商品列表失败');
      }
    } catch (error: any) {
      console.error('获取商品列表失败:', error);
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 获取商品详情
   */
  async getProductById(productId: number): Promise<ProductDetail> {
    try {
      const response: AxiosResponse<ApiResponse<ProductDetail>> = await this.api.get(
        `/products/${productId}`
      );
      
      if (response.data.status === 'success' && response.data.data) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '获取商品详情失败');
      }
    } catch (error: any) {
      console.error('获取商品详情失败:', error);
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 收藏商品
   */
  async favoriteProduct(productId: number): Promise<boolean> {
    try {
      const response: AxiosResponse<ApiResponse<null>> = await this.api.post(
        '/users/me/favorites',
        { product_id: productId }
      );
      
      return response.data.status === 'success';
    } catch (error: any) {
      console.error('收藏商品失败:', error);
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 取消收藏商品
   */
  async unfavoriteProduct(productId: number): Promise<boolean> {
    try {
      const response: AxiosResponse<ApiResponse<null>> = await this.api.delete(
        `/users/me/favorites/${productId}`
      );
      
      return response.data.status === 'success';
    } catch (error: any) {
      console.error('取消收藏商品失败:', error);
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 获取当前用户收藏的商品
   */
  async getFavoriteProducts(): Promise<ProductListItem[]> {
    try {
      const response: AxiosResponse<ApiResponse<ProductListItem[]>> = await this.api.get(
        '/users/me/favorites'
      );
      
      if (response.data.status === 'success' && response.data.data) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '获取收藏商品失败');
      }
    } catch (error: any) {
      console.error('获取收藏商品失败:', error);
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 测试API连接
   */
  async testConnection(): Promise<boolean> {
    try {
      // 尝试获取商家列表来测试连接
      await this.getMerchants({ limit: 1 });
      return true;
    } catch (error) {
      console.error('API连接测试失败:', error);
      return false;
    }
  }
}

// 创建并导出单例实例
const apiService = new APIService();
export default apiService;
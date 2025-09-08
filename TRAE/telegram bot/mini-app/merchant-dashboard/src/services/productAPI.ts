import axios, { AxiosInstance, AxiosResponse } from 'axios';

// API响应接口
interface ApiResponse<T> {
  status: string;
  data?: T;
  message?: string;
}

// 商品基础信息接口
export interface ProductInfo {
  id: number;
  merchant_id: number;
  name: string;
  description?: string;
  price?: number;
  price_unit: string;
  is_price_negotiable: boolean;
  currency: string;
  category_id?: number;
  image_urls: string[];
  tags: string[];
  status: string;
  sort_order: number;
  view_count: number;
  favorite_count: number;
  sales_count: number;
  stock_status: string;
  created_at: string;
  updated_at: string;
}

// 商品列表项接口
export interface ProductListItem {
  id: number;
  merchant_id: number;
  name: string;
  description?: string;
  price?: number;
  price_unit: string;
  is_price_negotiable: boolean;
  currency: string;
  main_image_url?: string;
  status: string;
  view_count: number;
  favorite_count: number;
  stock_status: string;
  created_at: string;
}

// 商品创建请求接口
export interface ProductCreateRequest {
  name: string;
  description?: string;
  price?: number;
  price_unit?: string;
  is_price_negotiable?: boolean;
  currency?: string;
  category_id?: number;
  image_urls?: string[];
  tags?: string[];
  status?: string;
  sort_order?: number;
}

// 商品更新请求接口
export interface ProductUpdateRequest {
  name?: string;
  description?: string;
  price?: number;
  price_unit?: string;
  is_price_negotiable?: boolean;
  currency?: string;
  category_id?: number;
  image_urls?: string[];
  tags?: string[];
  status?: string;
  sort_order?: number;
}

// 商品搜索响应接口
export interface ProductSearchResponse {
  products: ProductListItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// 商品统计数据接口
export interface ProductStats {
  product_id: number;
  view_count: number;
  favorite_count: number;
  sales_count: number;
  rating_avg?: number;
  rating_count: number;
}

class ProductAPIService {
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
        // API请求错误处理
        
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
        return localStorage.getItem('auth_token');
      }
      
      return null;
    } catch (error) {
      // 获取认证token失败处理
      return null;
    }
  }

  /**
   * 创建商品
   */
  async createProduct(productData: ProductCreateRequest): Promise<ProductInfo> {
    try {
      const response: AxiosResponse<ApiResponse<ProductInfo>> = await this.api.post(
        '/products/',
        productData
      );
      
      if (response.data.status === 'success' && response.data.data) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '创建商品失败');
      }
    } catch (error: any) {
      // 创建商品失败处理
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 获取商品列表
   */
  async getProducts(params?: {
    page?: number;
    per_page?: number;
    q?: string;
    category_id?: number;
    status?: string;
    min_price?: number;
    max_price?: number;
    tags?: string[];
    sort_by?: string;
    sort_order?: string;
  }): Promise<ProductSearchResponse> {
    try {
      const response: AxiosResponse<ApiResponse<ProductSearchResponse>> = await this.api.get(
        '/products/',
        { params }
      );
      
      if (response.data.status === 'success' && response.data.data) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '获取商品列表失败');
      }
    } catch (error: any) {
      // 获取商品列表失败处理
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 获取商品详情
   */
  async getProductById(productId: number): Promise<ProductInfo> {
    try {
      const response: AxiosResponse<ApiResponse<ProductInfo>> = await this.api.get(
        `/products/${productId}`
      );
      
      if (response.data.status === 'success' && response.data.data) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '获取商品详情失败');
      }
    } catch (error: any) {
      // 获取商品详情失败处理
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 更新商品
   */
  async updateProduct(productId: number, updateData: ProductUpdateRequest): Promise<ProductInfo> {
    try {
      const response: AxiosResponse<ApiResponse<ProductInfo>> = await this.api.put(
        `/products/${productId}`,
        updateData
      );
      
      if (response.data.status === 'success' && response.data.data) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '更新商品失败');
      }
    } catch (error: any) {
      // 更新商品失败处理
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 删除商品
   */
  async deleteProduct(productId: number): Promise<boolean> {
    try {
      const response: AxiosResponse<ApiResponse<null>> = await this.api.delete(
        `/products/${productId}`
      );
      
      if (response.data.status === 'success') {
        return true;
      } else {
        throw new Error(response.data.message || '删除商品失败');
      }
    } catch (error: any) {
      // 删除商品失败处理
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }

  /**
   * 获取商品统计数据
   */
  async getProductStats(productId: number): Promise<ProductStats> {
    try {
      const response: AxiosResponse<ApiResponse<ProductStats>> = await this.api.get(
        `/products/${productId}/stats`
      );
      
      if (response.data.status === 'success' && response.data.data) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '获取商品统计数据失败');
      }
    } catch (error: any) {
      // 获取商品统计数据失败处理
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
  }
}

// 创建并导出单例实例
const productAPI = new ProductAPIService();
export default productAPI;
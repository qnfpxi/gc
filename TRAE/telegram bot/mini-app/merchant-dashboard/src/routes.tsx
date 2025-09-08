import React from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import App from './App';
import Login from './pages/Login';
import Register from './pages/Register';

// 创建路由配置
const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
  },
  {
    path: "/login",
    element: <Login />,
  },
  {
    path: "/register",
    element: <Register />,
  },
]);

// 路由提供者组件
export const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default AppRouter;
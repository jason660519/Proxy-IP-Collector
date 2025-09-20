/**
 * 主題狀態管理
 * @description 管理應用主題設置（亮色/暗色模式）
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export type ThemeType = 'light' | 'dark';

interface ThemeState {
  theme: ThemeType;
  collapsed: boolean;
}

const initialState: ThemeState = {
  theme: 'light',
  collapsed: false,
};

const themeSlice = createSlice({
  name: 'theme',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<ThemeType>) => {
      state.theme = action.payload;
    },
    toggleTheme: (state) => {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
    },
    toggleSidebar: (state) => {
      state.collapsed = !state.collapsed;
    },
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.collapsed = action.payload;
    },
  },
});

export const { setTheme, toggleTheme, toggleSidebar, setSidebarCollapsed } = themeSlice.actions;
export default themeSlice.reducer;
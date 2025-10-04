import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'chatterbox-processing-mode';

export type ProcessingMode = 'auto' | 'streaming' | 'long-text';

interface ProcessingModeSettings {
  mode: ProcessingMode;
}

const DEFAULT_SETTINGS: ProcessingModeSettings = {
  mode: 'auto'
};

export function useProcessingMode() {
  const [settings, setSettings] = useState<ProcessingModeSettings>(() => {
    if (typeof window === 'undefined') return DEFAULT_SETTINGS;

    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        return {
          mode: parsed.mode || DEFAULT_SETTINGS.mode
        };
      }
    } catch (error) {
      console.error('Error loading processing mode settings:', error);
    }

    return DEFAULT_SETTINGS;
  });

  // Save to localStorage whenever settings change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
      console.log('[ProcessingMode] Saved to localStorage:', settings);
    } catch (error) {
      console.error('Error saving processing mode settings:', error);
    }
  }, [settings]);

  const setMode = useCallback((mode: ProcessingMode) => {
    console.log('[ProcessingMode] Setting mode to:', mode);
    setSettings({ mode });
  }, []);

  const resetToAuto = useCallback(() => {
    console.log('[ProcessingMode] Resetting to auto mode');
    setSettings(DEFAULT_SETTINGS);
  }, []);

  /**
   * Determine if long text mode should be used based on current settings and text
   */
  const shouldUseLongText = useCallback((text: string): boolean => {
    const textLength = text.length;
    console.log('[ProcessingMode] shouldUseLongText check:', {
      mode: settings.mode,
      textLength,
      threshold: 3000
    });

    // Manual override: user explicitly chose a mode
    if (settings.mode === 'streaming') {
      console.log('[ProcessingMode] Using STREAMING mode (manual override)');
      return false;
    }

    if (settings.mode === 'long-text') {
      console.log('[ProcessingMode] Using LONG-TEXT mode (manual override)');
      return true;
    }

    // Auto mode: use text length threshold
    const useLongText = textLength > 3000;
    console.log('[ProcessingMode] Using AUTO mode, result:', useLongText);
    return useLongText;
  }, [settings.mode]);

  return {
    mode: settings.mode,
    setMode,
    resetToAuto,
    shouldUseLongText,
    isAuto: settings.mode === 'auto',
    isManualStreaming: settings.mode === 'streaming',
    isManualLongText: settings.mode === 'long-text'
  };
}

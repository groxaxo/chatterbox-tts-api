import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'chatterbox-advanced-settings';

// Default values for advanced settings
const DEFAULT_SETTINGS = {
  exaggeration: 0.5,
  cfgWeight: 0.5,
  temperature: 0.8,
  streamingChunkSize: undefined as number | undefined,
  streamingStrategy: 'sentence' as 'sentence' | 'paragraph' | 'fixed' | 'word',
  streamingQuality: 'balanced' as 'fast' | 'balanced' | 'high'
};

interface AdvancedSettings {
  exaggeration: number;
  cfgWeight: number;
  temperature: number;
  streamingChunkSize?: number;
  streamingStrategy: 'sentence' | 'paragraph' | 'fixed' | 'word';
  streamingQuality: 'fast' | 'balanced' | 'high';
}

export function useAdvancedSettings() {
  const [settings, setSettings] = useState<AdvancedSettings>(() => {
    if (typeof window === 'undefined') return DEFAULT_SETTINGS;

    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        // Ensure all required fields exist and are valid numbers
        return {
          exaggeration: typeof parsed.exaggeration === 'number' ? parsed.exaggeration : DEFAULT_SETTINGS.exaggeration,
          cfgWeight: typeof parsed.cfgWeight === 'number' ? parsed.cfgWeight : DEFAULT_SETTINGS.cfgWeight,
          temperature: typeof parsed.temperature === 'number' ? parsed.temperature : DEFAULT_SETTINGS.temperature,
          streamingChunkSize: typeof parsed.streamingChunkSize === 'number' ? parsed.streamingChunkSize : DEFAULT_SETTINGS.streamingChunkSize,
          streamingStrategy: parsed.streamingStrategy || DEFAULT_SETTINGS.streamingStrategy,
          streamingQuality: parsed.streamingQuality || DEFAULT_SETTINGS.streamingQuality
        };
      }
    } catch (error) {
      console.error('Error loading advanced settings:', error);
    }

    return DEFAULT_SETTINGS;
  });

  // Save to localStorage whenever settings change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch (error) {
      console.error('Error saving advanced settings:', error);
    }
  }, [settings]);

  const updateExaggeration = useCallback((value: number) => {
    setSettings(prev => ({ ...prev, exaggeration: value }));
  }, []);

  const updateCfgWeight = useCallback((value: number) => {
    setSettings(prev => ({ ...prev, cfgWeight: value }));
  }, []);

  const updateTemperature = useCallback((value: number) => {
    setSettings(prev => ({ ...prev, temperature: value }));
  }, []);

  const updateStreamingChunkSize = useCallback((value: number | undefined) => {
    setSettings(prev => ({ ...prev, streamingChunkSize: value }));
  }, []);

  const updateStreamingStrategy = useCallback((value: 'sentence' | 'paragraph' | 'fixed' | 'word') => {
    setSettings(prev => ({ ...prev, streamingStrategy: value }));
  }, []);

  const updateStreamingQuality = useCallback((value: 'fast' | 'balanced' | 'high') => {
    setSettings(prev => ({ ...prev, streamingQuality: value }));
  }, []);

  const resetToDefaults = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
  }, []);

  const isDefault = useCallback(() => {
    return (
      settings.exaggeration === DEFAULT_SETTINGS.exaggeration &&
      settings.cfgWeight === DEFAULT_SETTINGS.cfgWeight &&
      settings.temperature === DEFAULT_SETTINGS.temperature &&
      settings.streamingChunkSize === DEFAULT_SETTINGS.streamingChunkSize &&
      settings.streamingStrategy === DEFAULT_SETTINGS.streamingStrategy &&
      settings.streamingQuality === DEFAULT_SETTINGS.streamingQuality
    );
  }, [settings]);

  return {
    // Individual values
    exaggeration: settings.exaggeration,
    cfgWeight: settings.cfgWeight,
    temperature: settings.temperature,
    streamingChunkSize: settings.streamingChunkSize,
    streamingStrategy: settings.streamingStrategy,
    streamingQuality: settings.streamingQuality,

    // Update functions
    updateExaggeration,
    updateCfgWeight,
    updateTemperature,
    updateStreamingChunkSize,
    updateStreamingStrategy,
    updateStreamingQuality,

    // Utility functions
    resetToDefaults,
    isDefault: isDefault(),

    // Full settings object for easy passing
    settings
  };
} 